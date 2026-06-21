from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobType(StrEnum):
    COLLECT_QUOTES = "collect_quotes"
    COLLECT_EVENTS = "collect_events"
    ARCHIVE_MARKET_DATA = "archive_market_data"
    GENERATE_PREMARKET_REPORT = "generate_premarket_report"
    GENERATE_INTRADAY_REPORT = "generate_intraday_report"
    GENERATE_CLOSE_REPORT = "generate_close_report"
    EVALUATE_ALERTS = "evaluate_alerts"
    FULL_PIPELINE = "full_pipeline"


class JobRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"


class JobTriggerType(StrEnum):
    MANUAL = "manual"
    SCHEDULER = "scheduler"
    PIPELINE = "pipeline"


class JobErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    ALREADY_RUNNING = "already_running"
    TIMEOUT = "timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    STORAGE_ERROR = "storage_error"
    REPORT_GENERATION_ERROR = "report_generation_error"
    ALERT_EVALUATION_ERROR = "alert_evaluation_error"
    INTERNAL_ERROR = "internal_error"


class StrictJobModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ScheduledJobCreate(StrictJobModel):
    job_key: str = Field(min_length=1, max_length=80)
    job_type: JobType
    display_name: str = Field(min_length=1, max_length=120)
    is_enabled: bool = False
    interval_seconds: int = Field(ge=60, le=604800)
    timeout_seconds: int = Field(ge=5, le=600)
    max_retries: int = Field(ge=0, le=3)
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None

    @field_validator("job_key")
    @classmethod
    def validate_job_key(cls, value: str) -> str:
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("invalid_job_key")
        return value


class ScheduledJobUpdate(StrictJobModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    is_enabled: bool | None = None
    interval_seconds: int | None = Field(default=None, ge=60, le=604800)
    timeout_seconds: int | None = Field(default=None, ge=5, le=600)
    max_retries: int | None = Field(default=None, ge=0, le=3)


class ScheduledJob(ScheduledJobCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class JobRun(StrictJobModel):
    id: str
    job_id: str
    job_key: str
    job_type: JobType
    status: JobRunStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    attempt: int
    trigger_type: JobTriggerType
    input_summary: dict[str, Any] = Field(default_factory=dict)
    result_summary: dict[str, Any] = Field(default_factory=dict)
    error_code: JobErrorCode | None = None
    error_message: str | None = None
    created_at: datetime


class JobRunResult(StrictJobModel):
    run_id: str
    job_key: str
    job_type: JobType
    status: JobRunStatus
    attempts: int
    result_summary: dict[str, Any] = Field(default_factory=dict)
    error_code: JobErrorCode | None = None
    error_message: str | None = None


class SchedulerStatus(StrictJobModel):
    scheduler_enabled: bool = False
    scheduler_process_running: bool = False
    enabled_jobs: int
    next_run_at: datetime | None = None
    mode: str = "foreground_only"
    background_service_installed: bool = False


DEFAULT_JOBS: list[ScheduledJobCreate] = [
    ScheduledJobCreate(
        job_key="collect_quotes",
        job_type=JobType.COLLECT_QUOTES,
        display_name="Collect Mock Quotes",
        interval_seconds=300,
        timeout_seconds=30,
        max_retries=1,
    ),
    ScheduledJobCreate(
        job_key="collect_events",
        job_type=JobType.COLLECT_EVENTS,
        display_name="Collect Mock Events",
        interval_seconds=900,
        timeout_seconds=30,
        max_retries=1,
    ),
    ScheduledJobCreate(
        job_key="generate_intraday_report",
        job_type=JobType.GENERATE_INTRADAY_REPORT,
        display_name="Generate Intraday Report",
        interval_seconds=1800,
        timeout_seconds=60,
        max_retries=1,
    ),
    ScheduledJobCreate(
        job_key="evaluate_alerts",
        job_type=JobType.EVALUATE_ALERTS,
        display_name="Evaluate Alerts",
        interval_seconds=300,
        timeout_seconds=60,
        max_retries=1,
    ),
    ScheduledJobCreate(
        job_key="full_pipeline",
        job_type=JobType.FULL_PIPELINE,
        display_name="Run Full Mock Pipeline",
        interval_seconds=900,
        timeout_seconds=180,
        max_retries=1,
    ),
]


def utc_now() -> datetime:
    return datetime.now(UTC)

