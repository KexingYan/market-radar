import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.jobs.models import JobTriggerType
from app.jobs.service import create_job_executor, due_enabled_jobs
from app.repositories.sqlite import PROJECT_ROOT

STATUS_PATH = PROJECT_ROOT / ".runtime" / "scheduler" / "status.json"


class ForegroundScheduler:
    def __init__(self, check_interval_seconds: int = 5) -> None:
        self._check_interval_seconds = check_interval_seconds
        self._executor = create_job_executor()
        self._stopped = False

    async def run(self, run_once: bool = False) -> dict[str, object]:
        jobs = await due_enabled_jobs()
        self._write_status(running=True, enabled_jobs=len(jobs))
        if not jobs:
            self._write_status(running=False, enabled_jobs=0, message="No scheduled jobs are enabled.")
            return {"message": "No scheduled jobs are enabled.", "enabled_jobs": 0}
        completed = 0
        try:
            while not self._stopped:
                due = await due_enabled_jobs()
                for job in due[:1]:
                    await self._executor.run_job(job.id, JobTriggerType.SCHEDULER)
                    completed += 1
                if run_once:
                    break
                await asyncio.sleep(self._check_interval_seconds)
        finally:
            self._write_status(running=False, enabled_jobs=len(await due_enabled_jobs()), completed_runs=completed)
        return {"completed_runs": completed}

    def stop(self) -> None:
        self._stopped = True

    def _write_status(self, running: bool, enabled_jobs: int, **extra: object) -> None:
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "mode": "foreground_only",
            "running": running,
            "enabled_jobs": enabled_jobs,
            "updated_at": datetime.now(UTC).isoformat(),
            **extra,
        }
        STATUS_PATH.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def scheduler_status_file_is_running(max_age_seconds: int = 60) -> bool:
    if not STATUS_PATH.exists():
        return False
    try:
        payload = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        updated = datetime.fromisoformat(payload.get("updated_at", ""))
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=UTC)
        return bool(payload.get("running")) and datetime.now(UTC) - updated <= timedelta(seconds=max_age_seconds)
    except (ValueError, OSError, json.JSONDecodeError):
        return False

