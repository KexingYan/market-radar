from datetime import datetime
from typing import Protocol

from app.alerts.models import AlertItem, AlertRule, AlertRuleUpdate, AlertStatus, AlertSummary
from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot
from app.domain.report import MarketReport, ReportType
from app.domain.watchlist import WatchlistItem
from app.jobs.models import JobRun, JobRunStatus, JobTriggerType, ScheduledJob, ScheduledJobUpdate


class SaveResult(Protocol):
    inserted: int
    duplicates: int
    failed: int


class QuoteRepository(Protocol):
    async def save_snapshots(self, snapshots: list[QuoteSnapshot]) -> SaveResult:
        ...

    async def get_latest(self, symbols: list[str] | None = None) -> list[QuoteSnapshot]:
        ...

    async def get_history(
        self,
        symbol: str,
        limit: int = 100,
        before: datetime | None = None,
        after: datetime | None = None,
    ) -> list[QuoteSnapshot]:
        ...


class EventRepository(Protocol):
    async def save_events(self, events: list[MarketEvent]) -> SaveResult:
        ...

    async def get_event(self, event_id: str) -> MarketEvent | None:
        ...

    async def list_events(
        self,
        symbol: str | None = None,
        event_type: str | None = None,
        minimum_importance: int | None = None,
        limit: int = 100,
    ) -> list[MarketEvent]:
        ...


class ReportRepository(Protocol):
    async def save_report(self, report: MarketReport) -> SaveResult:
        ...

    async def get_report(self, report_id: str) -> MarketReport | None:
        ...

    async def list_reports(
        self,
        report_type: ReportType | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
    ) -> list[MarketReport]:
        ...


class WatchlistRepository(Protocol):
    async def list_symbols(self) -> list[WatchlistItem]:
        ...

    async def add_symbol(self, item: WatchlistItem) -> WatchlistItem:
        ...

    async def remove_symbol(self, symbol: str) -> bool:
        ...


class AlertRuleRepository(Protocol):
    async def ensure_default_rules(self) -> None:
        ...

    async def list_rules(self, enabled_only: bool = False, rule_type: str | None = None) -> list[AlertRule]:
        ...

    async def get_rule(self, rule_id: str) -> AlertRule | None:
        ...

    async def create_rule(self, rule: AlertRule) -> AlertRule:
        ...

    async def update_rule(self, rule_id: str, patch: AlertRuleUpdate) -> AlertRule | None:
        ...

    async def set_enabled(self, rule_id: str, enabled: bool) -> AlertRule | None:
        ...


class AlertRepository(Protocol):
    async def save_alerts(self, alerts: list[AlertItem]) -> SaveResult:
        ...

    async def list_alerts(
        self,
        status: AlertStatus | None = None,
        severity: str | None = None,
        symbol: str | None = None,
        rule_type: str | None = None,
        limit: int = 50,
        before: datetime | None = None,
        after: datetime | None = None,
        include_snoozed: bool = False,
    ) -> list[AlertItem]:
        ...

    async def get_alert(self, alert_id: str) -> AlertItem | None:
        ...

    async def acknowledge(self, alert_id: str, acknowledged_at: datetime) -> AlertItem | None:
        ...

    async def snooze(self, alert_id: str, snoozed_until: datetime) -> AlertItem | None:
        ...

    async def find_recent_for_cooldown(self, rule_id: str, symbol: str, since: datetime) -> AlertItem | None:
        ...

    async def summary(self, now: datetime) -> AlertSummary:
        ...


class JobRepository(Protocol):
    async def ensure_default_jobs(self) -> None:
        ...

    async def list_jobs(self, enabled_only: bool = False, job_type: str | None = None) -> list[ScheduledJob]:
        ...

    async def get_job(self, job_id: str) -> ScheduledJob | None:
        ...

    async def get_job_by_key(self, job_key: str) -> ScheduledJob | None:
        ...

    async def update_job(self, job_id: str, patch: ScheduledJobUpdate) -> ScheduledJob | None:
        ...

    async def mark_run_schedule(self, job_id: str, last_run_at: datetime, next_run_at: datetime | None) -> None:
        ...


class JobRunRepository(Protocol):
    async def create_run(self, run: JobRun) -> JobRun:
        ...

    async def update_run(self, run_id: str, **fields: object) -> JobRun | None:
        ...

    async def get_run(self, run_id: str) -> JobRun | None:
        ...

    async def list_runs(
        self,
        job_type: str | None = None,
        status: JobRunStatus | None = None,
        trigger_type: JobTriggerType | None = None,
        limit: int = 100,
        before: datetime | None = None,
        after: datetime | None = None,
    ) -> list[JobRun]:
        ...


class JobLockRepository(Protocol):
    async def acquire(self, job_key: str, lock_owner: str, expires_at: datetime, now: datetime) -> bool:
        ...

    async def release(self, job_key: str, lock_owner: str) -> None:
        ...
