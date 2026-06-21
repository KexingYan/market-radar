import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Awaitable, Callable

from app.jobs.models import (
    JobErrorCode,
    JobRun,
    JobRunResult,
    JobRunStatus,
    JobTriggerType,
    JobType,
    ScheduledJob,
)
from app.jobs.registry import JOB_HANDLERS
from app.jobs.tasks import TaskContext
from app.repositories.base import JobLockRepository, JobRepository, JobRunRepository


class JobExecutionError(Exception):
    def __init__(self, code: JobErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


class JobExecutor:
    def __init__(
        self,
        job_repository: JobRepository,
        run_repository: JobRunRepository,
        lock_repository: JobLockRepository,
        context: TaskContext,
        sleep_seconds: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self._jobs = job_repository
        self._runs = run_repository
        self._locks = lock_repository
        self._context = context
        self._sleep = sleep_seconds or asyncio.sleep

    async def run_job(self, job_id: str, trigger_type: JobTriggerType = JobTriggerType.MANUAL) -> JobRunResult:
        await self._jobs.ensure_default_jobs()
        job = await self._jobs.get_job(job_id)
        if job is None:
            raise JobExecutionError(JobErrorCode.VALIDATION_ERROR, "job_not_found")
        return await self._run_job(job, trigger_type)

    async def run_job_by_key(self, job_key: str, trigger_type: JobTriggerType = JobTriggerType.PIPELINE) -> JobRunResult:
        await self._jobs.ensure_default_jobs()
        job = await self._jobs.get_job_by_key(job_key)
        if job is None:
            raise JobExecutionError(JobErrorCode.VALIDATION_ERROR, "job_not_found")
        return await self._run_job(job, trigger_type)

    async def run_pipeline(self, trigger_type: JobTriggerType = JobTriggerType.MANUAL) -> JobRunResult:
        await self._jobs.ensure_default_jobs()
        pipeline_job = await self._jobs.get_job_by_key("full_pipeline")
        if pipeline_job is None:
            raise JobExecutionError(JobErrorCode.VALIDATION_ERROR, "job_not_found")
        return await self._run_job(pipeline_job, trigger_type)

    async def _run_job(self, job: ScheduledJob, trigger_type: JobTriggerType) -> JobRunResult:
        owner = f"runner-{uuid.uuid4().hex}"
        now = datetime.now(UTC)
        acquired = await self._locks.acquire(
            job.job_key,
            owner,
            expires_at=now + timedelta(seconds=job.timeout_seconds + 30),
            now=now,
        )
        if not acquired:
            run = await self._create_run(job, trigger_type, JobRunStatus.SKIPPED, 1, now)
            await self._runs.update_run(
                run.id,
                finished_at=now,
                duration_ms=0,
                error_code=JobErrorCode.ALREADY_RUNNING,
                error_message="already_running",
            )
            return JobRunResult(
                run_id=run.id,
                job_key=job.job_key,
                job_type=job.job_type,
                status=JobRunStatus.SKIPPED,
                attempts=1,
                error_code=JobErrorCode.ALREADY_RUNNING,
                error_message="already_running",
            )

        attempts = 0
        run = await self._create_run(job, trigger_type, JobRunStatus.RUNNING, 1, now)
        try:
            for attempt in range(1, job.max_retries + 2):
                attempts = attempt
                await self._runs.update_run(run.id, attempt=attempt)
                started = datetime.now(UTC)
                try:
                    summary = await asyncio.wait_for(self._execute_handler(job), timeout=job.timeout_seconds)
                    finished = datetime.now(UTC)
                    duration_ms = int((finished - started).total_seconds() * 1000)
                    await self._runs.update_run(
                        run.id,
                        status=JobRunStatus.SUCCEEDED,
                        finished_at=finished,
                        duration_ms=duration_ms,
                        result_summary=sanitize_summary(summary),
                    )
                    await self._jobs.mark_run_schedule(
                        job.id,
                        finished,
                        finished + timedelta(seconds=job.interval_seconds) if job.is_enabled else None,
                    )
                    return JobRunResult(
                        run_id=run.id,
                        job_key=job.job_key,
                        job_type=job.job_type,
                        status=JobRunStatus.SUCCEEDED,
                        attempts=attempts,
                        result_summary=sanitize_summary(summary),
                    )
                except TimeoutError:
                    if attempt > job.max_retries:
                        return await self._fail_run(run, job, attempts, JobRunStatus.TIMED_OUT, JobErrorCode.TIMEOUT, started)
                except JobExecutionError as exc:
                    return await self._fail_run(run, job, attempts, JobRunStatus.FAILED, exc.code, started)
                except Exception:
                    if attempt > job.max_retries:
                        return await self._fail_run(run, job, attempts, JobRunStatus.FAILED, JobErrorCode.INTERNAL_ERROR, started)
                await self._sleep(min(2 ** (attempt - 1), 4))
        finally:
            await self._locks.release(job.job_key, owner)
        return JobRunResult(
            run_id=run.id,
            job_key=job.job_key,
            job_type=job.job_type,
            status=JobRunStatus.FAILED,
            attempts=attempts,
            error_code=JobErrorCode.INTERNAL_ERROR,
            error_message="internal_error",
        )

    async def _execute_handler(self, job: ScheduledJob) -> dict[str, Any]:
        if job.job_type == JobType.FULL_PIPELINE:
            return await self._execute_full_pipeline()
        handler = JOB_HANDLERS.get(job.job_type)
        if handler is None:
            raise JobExecutionError(JobErrorCode.VALIDATION_ERROR, "unsupported_job_type")
        return await handler(self._context)

    async def _execute_full_pipeline(self) -> dict[str, Any]:
        steps: list[dict[str, Any]] = []
        final_status = "succeeded"
        for key in ["collect_quotes", "collect_events", "archive_market_data", "generate_intraday_report", "evaluate_alerts"]:
            job = await self._jobs.get_job_by_key(key)
            if job is None:
                handler = JOB_HANDLERS.get(JobType(key))
                if handler is None:
                    final_status = "failed"
                    steps.append({"job_key": key, "status": "failed", "summary": {"error_code": "validation_error"}})
                    break
                summary = sanitize_summary(await handler(self._context))
                steps.append({"job_key": key, "status": "succeeded", "summary": summary})
                continue
            result = await self.run_job_by_key(key, JobTriggerType.PIPELINE)
            steps.append({"job_key": result.job_key, "status": result.status.value, "run_id": result.run_id, "summary": result.result_summary})
            if result.status in {JobRunStatus.FAILED, JobRunStatus.TIMED_OUT}:
                final_status = "partial" if key not in {"collect_quotes"} else "failed"
                if key == "collect_quotes":
                    break
        return {"pipeline_status": final_status, "steps": steps, "mock_data_used": True}

    async def _create_run(
        self,
        job: ScheduledJob,
        trigger_type: JobTriggerType,
        status: JobRunStatus,
        attempt: int,
        now: datetime,
    ) -> JobRun:
        run = JobRun(
            id=f"run-{uuid.uuid4().hex}",
            job_id=job.id,
            job_key=job.job_key,
            job_type=job.job_type,
            status=status,
            started_at=now if status == JobRunStatus.RUNNING else None,
            finished_at=None,
            duration_ms=None,
            attempt=attempt,
            trigger_type=trigger_type,
            input_summary={"job_key": job.job_key, "trigger_type": trigger_type.value},
            result_summary={},
            error_code=None,
            error_message=None,
            created_at=now,
        )
        return await self._runs.create_run(run)

    async def _fail_run(
        self,
        run: JobRun,
        job: ScheduledJob,
        attempts: int,
        status: JobRunStatus,
        code: JobErrorCode,
        started: datetime,
    ) -> JobRunResult:
        finished = datetime.now(UTC)
        await self._runs.update_run(
            run.id,
            status=status,
            finished_at=finished,
            duration_ms=int((finished - started).total_seconds() * 1000),
            error_code=code,
            error_message=code.value,
        )
        return JobRunResult(
            run_id=run.id,
            job_key=job.job_key,
            job_type=job.job_type,
            status=status,
            attempts=attempts,
            error_code=code,
            error_message=code.value,
        )


def sanitize_summary(summary: dict[str, Any]) -> dict[str, Any]:
    allowed: dict[str, Any] = {}
    for key, value in summary.items():
        if isinstance(value, dict):
            allowed[key] = sanitize_summary(value)
        elif isinstance(value, list):
            allowed[key] = [sanitize_summary(item) if isinstance(item, dict) else item for item in value[:10]]
        elif isinstance(value, (str, int, float, bool)) or value is None:
            allowed[key] = value
    return allowed
