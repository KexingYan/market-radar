from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.alerts.service import AlertService
from app.jobs.executor import JobExecutor
from app.jobs.models import (
    JobRun,
    JobRunStatus,
    JobTriggerType,
    JobType,
    ScheduledJobCreate,
    ScheduledJobUpdate,
)
from app.jobs.scheduler import ForegroundScheduler, scheduler_status_file_is_running
from app.jobs.tasks import TaskContext
from app.main import app
from app.providers.mock import MockMarketDataProvider
from app.repositories.memory import create_memory_repositories
from app.services.archive import ArchiveService

client = TestClient(app)


def test_job_model_validation() -> None:
    job = ScheduledJobCreate(
        job_key="collect_quotes",
        job_type=JobType.COLLECT_QUOTES,
        display_name="Collect",
        interval_seconds=60,
        timeout_seconds=5,
        max_retries=0,
    )

    assert job.is_enabled is False


@pytest.mark.parametrize(
    "payload",
    [
        {"job_key": "bad key!", "job_type": "collect_quotes", "display_name": "x", "interval_seconds": 60, "timeout_seconds": 5, "max_retries": 0},
        {"job_key": "x", "job_type": "bad", "display_name": "x", "interval_seconds": 60, "timeout_seconds": 5, "max_retries": 0},
        {"job_key": "x", "job_type": "collect_quotes", "display_name": "x", "interval_seconds": 59, "timeout_seconds": 5, "max_retries": 0},
        {"job_key": "x", "job_type": "collect_quotes", "display_name": "x", "interval_seconds": 604801, "timeout_seconds": 5, "max_retries": 0},
        {"job_key": "x", "job_type": "collect_quotes", "display_name": "x", "interval_seconds": 60, "timeout_seconds": 4, "max_retries": 0},
        {"job_key": "x", "job_type": "collect_quotes", "display_name": "x", "interval_seconds": 60, "timeout_seconds": 601, "max_retries": 0},
        {"job_key": "x", "job_type": "collect_quotes", "display_name": "x", "interval_seconds": 60, "timeout_seconds": 5, "max_retries": 4},
        {"job_key": "x", "job_type": "collect_quotes", "display_name": "x", "interval_seconds": 60, "timeout_seconds": 5, "max_retries": 0, "command": "echo bad"},
    ],
)
def test_job_model_rejects_invalid_values(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ScheduledJobCreate.model_validate(payload)


@pytest.mark.asyncio
async def test_job_repository_defaults_update_runs_locks_and_status() -> None:
    repos = create_memory_repositories()
    await repos["jobs"].ensure_default_jobs()
    await repos["jobs"].ensure_default_jobs()
    jobs = await repos["jobs"].list_jobs()

    assert len(jobs) == 5
    assert all(not job.is_enabled for job in jobs)

    updated = await repos["jobs"].update_job(jobs[0].id, ScheduledJobUpdate(is_enabled=True, interval_seconds=120))
    assert updated is not None and updated.is_enabled is True and updated.interval_seconds == 120

    run = _job_run(jobs[0].id, jobs[0].job_key, jobs[0].job_type)
    await repos["job_runs"].create_run(run)
    await repos["job_runs"].update_run(run.id, status=JobRunStatus.SUCCEEDED, result_summary={"received_quotes": 4})
    runs = await repos["job_runs"].list_runs(status=JobRunStatus.SUCCEEDED)

    now = datetime.now(UTC)
    acquired = await repos["job_locks"].acquire(jobs[0].job_key, "owner-1", now + timedelta(seconds=60), now)
    conflict = await repos["job_locks"].acquire(jobs[0].job_key, "owner-2", now + timedelta(seconds=60), now)
    await repos["job_locks"].release(jobs[0].job_key, "owner-1")
    acquired_again = await repos["job_locks"].acquire(jobs[0].job_key, "owner-3", now + timedelta(seconds=60), now)
    status = repos["metrics"].status()

    assert runs[0].result_summary["received_quotes"] == 4
    assert acquired is True
    assert conflict is False
    assert acquired_again is True
    assert status["scheduled_jobs_count"] == 5
    assert status["enabled_jobs_count"] == 1
    assert status["job_runs_count"] == 1


@pytest.mark.asyncio
async def test_expired_job_lock_can_be_recovered() -> None:
    repos = create_memory_repositories()
    await repos["jobs"].ensure_default_jobs()
    job = (await repos["jobs"].list_jobs())[0]
    now = datetime.now(UTC)

    acquired = await repos["job_locks"].acquire(job.job_key, "old", now - timedelta(seconds=1), now - timedelta(seconds=60))
    recovered = await repos["job_locks"].acquire(job.job_key, "new", now + timedelta(seconds=60), now)

    assert acquired is True
    assert recovered is True


@pytest.mark.asyncio
async def test_executor_runs_mock_quote_task_and_records_safe_summary() -> None:
    repos = create_memory_repositories()
    executor = _executor(repos)
    await repos["jobs"].ensure_default_jobs()
    job = await repos["jobs"].get_job_by_key("collect_quotes")

    result = await executor.run_job(job.id)
    runs = await repos["job_runs"].list_runs()

    assert result.status == JobRunStatus.SUCCEEDED
    assert result.result_summary["received_quotes"] >= 1
    assert "password" not in str(runs[0].result_summary).lower()
    assert "token" not in str(runs[0].result_summary).lower()


@pytest.mark.asyncio
async def test_executor_repeated_job_returns_already_running_when_locked() -> None:
    repos = create_memory_repositories()
    executor = _executor(repos)
    await repos["jobs"].ensure_default_jobs()
    job = await repos["jobs"].get_job_by_key("collect_events")
    now = datetime.now(UTC)
    await repos["job_locks"].acquire(job.job_key, "external", now + timedelta(seconds=60), now)

    result = await executor.run_job(job.id)

    assert result.status == JobRunStatus.SKIPPED
    assert result.error_code is not None and result.error_code.value == "already_running"


@pytest.mark.asyncio
async def test_full_pipeline_records_child_runs_and_is_idempotent() -> None:
    repos = create_memory_repositories()
    executor = _executor(repos)
    await repos["jobs"].ensure_default_jobs()

    first = await executor.run_pipeline()
    second = await executor.run_pipeline()
    runs = await repos["job_runs"].list_runs()

    assert first.status == JobRunStatus.SUCCEEDED
    assert second.status == JobRunStatus.SUCCEEDED
    assert len([run for run in runs if run.trigger_type == JobTriggerType.PIPELINE]) >= 5
    assert first.result_summary["pipeline_status"] in {"succeeded", "partial"}


def test_jobs_api_list_patch_run_pipeline_runs_and_scheduler_status() -> None:
    jobs = client.get("/api/v1/jobs")
    assert jobs.status_code == 200
    assert len(jobs.json()) >= 5
    job_id = next(item["id"] for item in jobs.json() if item["job_key"] == "collect_quotes")

    patched = client.patch(f"/api/v1/jobs/{job_id}", json={"is_enabled": False, "interval_seconds": 300})
    run = client.post(f"/api/v1/jobs/{job_id}/run")
    pipeline = client.post("/api/v1/jobs/pipeline/run")
    runs = client.get("/api/v1/job-runs?limit=10")
    scheduler = client.get("/api/v1/scheduler/status")
    storage = client.get("/api/v1/storage/status")

    assert patched.status_code == 200
    assert run.status_code == 200
    assert pipeline.status_code == 200
    assert runs.status_code == 200
    assert scheduler.status_code == 200
    assert scheduler.json()["mode"] == "foreground_only"
    assert scheduler.json()["background_service_installed"] is False
    assert "scheduled_jobs_count" in storage.json()


def test_jobs_api_validates_limits_and_bad_ids() -> None:
    bad_limit = client.get("/api/v1/job-runs?limit=999")
    bad_type = client.get("/api/v1/jobs?job_type=collect_quotes;DROP TABLE job_runs")
    missing = client.get("/api/v1/jobs/not-a-job")

    assert bad_limit.status_code == 422
    assert bad_type.status_code == 422
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_foreground_scheduler_no_enabled_jobs_exits_and_status_file_is_stopped() -> None:
    scheduler = ForegroundScheduler(check_interval_seconds=1)
    result = await scheduler.run(run_once=True)

    assert result["enabled_jobs"] == 0
    assert scheduler_status_file_is_running() is False


def test_runtime_job_code_has_no_shell_service_scheduler_or_trading_calls() -> None:
    runtime_root = Path(__file__).resolve().parents[1] / "app"
    forbidden = [
        "subprocess.Popen",
        "os.system",
        "shell=True",
        "schtasks",
        "sc.exe",
        "New-Service",
        "Register-ScheduledTask",
        "eval(",
        "exec(",
        "place_order",
        "unlock_trade",
        "OpenSecTradeContext",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in runtime_root.rglob("*.py") if "__pycache__" not in path.parts)

    for item in forbidden:
        assert item not in text


def _executor(repos: dict[str, object]) -> JobExecutor:
    provider = MockMarketDataProvider()
    archive = ArchiveService(repos["quotes"], repos["events"], repos["reports"])
    alert_service = AlertService(
        rule_repository=repos["alert_rules"],
        alert_repository=repos["alerts"],
        watchlist_repository=repos["watchlist"],
        quote_provider=provider,
        event_provider=provider,
    )
    context = TaskContext(
        quote_provider=provider,
        event_provider=provider,
        watchlist_repository=repos["watchlist"],
        archive_service=archive,
        alert_service=alert_service,
    )

    async def no_wait(_: float) -> None:
        return None

    return JobExecutor(repos["jobs"], repos["job_runs"], repos["job_locks"], context, sleep_seconds=no_wait)


def _job_run(job_id: str, job_key: str, job_type: JobType) -> JobRun:
    now = datetime.now(UTC)
    return JobRun(
        id="run-test",
        job_id=job_id,
        job_key=job_key,
        job_type=job_type,
        status=JobRunStatus.RUNNING,
        started_at=now,
        finished_at=None,
        duration_ms=None,
        attempt=1,
        trigger_type=JobTriggerType.MANUAL,
        input_summary={"job_key": job_key},
        result_summary={},
        created_at=now,
    )

