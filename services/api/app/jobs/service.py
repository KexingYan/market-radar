from datetime import UTC, datetime

from app.alerts.service import AlertService
from app.jobs.executor import JobExecutor
from app.jobs.models import JobRunStatus, JobTriggerType, ScheduledJob, ScheduledJobUpdate, SchedulerStatus
from app.jobs.tasks import TaskContext
from app.providers.registry import event_provider, quote_provider
from app.repositories import (
    alert_repository,
    alert_rule_repository,
    event_repository,
    job_lock_repository,
    job_repository,
    job_run_repository,
    quote_repository,
    report_repository,
    storage_metrics,
    watchlist_repository,
)
from app.services.archive import ArchiveService


class JobService:
    def __init__(self, executor: JobExecutor) -> None:
        self._executor = executor

    async def list_jobs(self, enabled_only: bool = False, job_type: str | None = None) -> list[ScheduledJob]:
        await job_repository.ensure_default_jobs()
        return await job_repository.list_jobs(enabled_only=enabled_only, job_type=job_type)

    async def get_job(self, job_id: str) -> ScheduledJob | None:
        await job_repository.ensure_default_jobs()
        return await job_repository.get_job(job_id)

    async def update_job(self, job_id: str, patch: ScheduledJobUpdate) -> ScheduledJob | None:
        await job_repository.ensure_default_jobs()
        return await job_repository.update_job(job_id, patch)

    async def run_job(self, job_id: str):
        return await self._executor.run_job(job_id, JobTriggerType.MANUAL)

    async def run_pipeline(self):
        return await self._executor.run_pipeline(JobTriggerType.MANUAL)

    async def scheduler_status(self) -> SchedulerStatus:
        await job_repository.ensure_default_jobs()
        jobs = await job_repository.list_jobs(enabled_only=True)
        next_times = [job.next_run_at for job in jobs if job.next_run_at is not None]
        return SchedulerStatus(
            scheduler_enabled=False,
            scheduler_process_running=False,
            enabled_jobs=len(jobs),
            next_run_at=min(next_times) if next_times else None,
        )


def create_job_executor() -> JobExecutor:
    archive_service = ArchiveService(quote_repository, event_repository, report_repository)
    alert_service = AlertService(
        rule_repository=alert_rule_repository,
        alert_repository=alert_repository,
        watchlist_repository=watchlist_repository,
        quote_provider=quote_provider,
        event_provider=event_provider,
    )
    context = TaskContext(
        quote_provider=quote_provider,
        event_provider=event_provider,
        watchlist_repository=watchlist_repository,
        archive_service=archive_service,
        alert_service=alert_service,
    )
    return JobExecutor(job_repository, job_run_repository, job_lock_repository, context)


job_service = JobService(create_job_executor())


async def due_enabled_jobs(now: datetime | None = None) -> list[ScheduledJob]:
    await job_repository.ensure_default_jobs()
    current = now or datetime.now(UTC)
    return [
        job
        for job in await job_repository.list_jobs(enabled_only=True)
        if job.next_run_at is None or job.next_run_at <= current
    ]


def storage_status() -> dict[str, int | bool | str]:
    return storage_metrics.status()

