from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.jobs.executor import JobExecutionError
from app.jobs.models import (
    JobRun,
    JobRunResult,
    JobRunStatus,
    JobTriggerType,
    JobType,
    ScheduledJob,
    ScheduledJobUpdate,
    SchedulerStatus,
)
from app.jobs.service import job_service
from app.repositories import job_run_repository

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.get("/jobs")
async def list_jobs(
    enabled_only: bool = Query(default=False),
    job_type: JobType | None = Query(default=None),
) -> list[ScheduledJob]:
    return await job_service.list_jobs(enabled_only=enabled_only, job_type=job_type.value if job_type else None)


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> ScheduledJob:
    job = await job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/jobs/{job_id}")
async def update_job(job_id: str, payload: ScheduledJobUpdate) -> ScheduledJob:
    job = await job_service.update_job(job_id, payload)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/pipeline/run")
async def run_pipeline() -> JobRunResult:
    return await job_service.run_pipeline()


@router.post("/jobs/{job_id}/run")
async def run_job(job_id: str) -> JobRunResult:
    try:
        result = await job_service.run_job(job_id)
    except JobExecutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result.error_code and result.error_code.value == "already_running":
        raise HTTPException(status_code=409, detail="already_running")
    return result


@router.get("/job-runs")
async def list_job_runs(
    job_type: JobType | None = Query(default=None),
    status: JobRunStatus | None = Query(default=None),
    trigger_type: JobTriggerType | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    before: datetime | None = Query(default=None),
    after: datetime | None = Query(default=None),
) -> list[JobRun]:
    return await job_run_repository.list_runs(
        job_type=job_type.value if job_type else None,
        status=status,
        trigger_type=trigger_type,
        limit=limit,
        before=before,
        after=after,
    )


@router.get("/job-runs/{run_id}")
async def get_job_run(run_id: str) -> JobRun:
    run = await job_run_repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Job run not found")
    return run


@router.get("/scheduler/status")
async def scheduler_status() -> SchedulerStatus:
    return await job_service.scheduler_status()

