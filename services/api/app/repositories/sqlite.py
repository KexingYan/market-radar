import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable

from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.alerts.models import (
    AlertItem,
    AlertRule,
    AlertRuleCreate,
    AlertRuleType,
    AlertRuleUpdate,
    AlertSeverity,
    AlertStatus,
    AlertSummary,
    AlertSymbolScope,
)
from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot
from app.domain.report import MarketReport, ReportType
from app.domain.watchlist import WatchlistItem
from app.jobs.models import (
    DEFAULT_JOBS,
    JobErrorCode,
    JobRun,
    JobRunStatus,
    JobTriggerType,
    JobType,
    ScheduledJob,
    ScheduledJobUpdate,
)
from app.repositories.models import (
    AlertRow,
    AlertRuleRow,
    Base,
    EventSymbolRow,
    JobLockRow,
    JobRunRow,
    MarketEventRow,
    QuoteSnapshotRow,
    ReportRow,
    ScheduledJobRow,
    WatchlistSymbolRow,
)

SUPPORTED_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DB_PATH = PROJECT_ROOT / ".runtime" / "data" / "market-radar.db"
DEFAULT_TEST_DB_DIR = PROJECT_ROOT / ".runtime" / "test-data"


@dataclass(frozen=True)
class SaveSummary:
    inserted: int = 0
    duplicates: int = 0
    failed: int = 0


def ensure_project_db_path(path: Path) -> Path:
    resolved = path.resolve()
    allowed = (PROJECT_ROOT / ".runtime" / "data").resolve()
    allowed_test = DEFAULT_TEST_DB_DIR.resolve()
    if allowed not in resolved.parents and allowed_test not in resolved.parents:
        raise ValueError("SQLite database path must stay inside project runtime storage.")
    return resolved


def create_session_factory(db_path: Path | str | None = None) -> sessionmaker[Session]:
    if db_path in {None, ""}:
        path = ensure_project_db_path(DEFAULT_DB_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{path.as_posix()}"
    elif str(db_path) == ":memory:":
        url = "sqlite:///:memory:"
        engine = create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        return sessionmaker(engine, expire_on_commit=False)
    else:
        path = ensure_project_db_path(Path(db_path))
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{path.as_posix()}"
    engine = create_engine(url, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


class SQLiteQuoteRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def save_snapshots(self, snapshots: list[QuoteSnapshot]) -> SaveSummary:
        inserted = 0
        duplicates = 0
        with self._session_factory() as session:
            for snapshot in snapshots:
                row = _quote_to_row(snapshot)
                session.add(row)
                try:
                    session.commit()
                    inserted += 1
                except IntegrityError:
                    session.rollback()
                    duplicates += 1
        return SaveSummary(inserted=inserted, duplicates=duplicates)

    async def get_latest(self, symbols: list[str] | None = None) -> list[QuoteSnapshot]:
        with self._session_factory() as session:
            stmt = select(QuoteSnapshotRow).order_by(QuoteSnapshotRow.recorded_at.desc())
            if symbols:
                stmt = stmt.where(QuoteSnapshotRow.symbol.in_([s.upper() for s in symbols]))
            rows = session.execute(stmt.limit(500)).scalars().all()
        latest: dict[str, QuoteSnapshotRow] = {}
        for row in rows:
            latest.setdefault(row.symbol, row)
        return [_row_to_quote(row) for row in latest.values()]

    async def get_history(
        self,
        symbol: str,
        limit: int = 100,
        before: datetime | None = None,
        after: datetime | None = None,
    ) -> list[QuoteSnapshot]:
        _validate_symbol(symbol)
        limit = min(limit, 500)
        with self._session_factory() as session:
            stmt = select(QuoteSnapshotRow).where(QuoteSnapshotRow.symbol == symbol.upper())
            if before:
                stmt = stmt.where(QuoteSnapshotRow.recorded_at <= before)
            if after:
                stmt = stmt.where(QuoteSnapshotRow.recorded_at >= after)
            rows = session.execute(stmt.order_by(QuoteSnapshotRow.recorded_at.desc()).limit(limit)).scalars().all()
        return [_row_to_quote(row) for row in rows]


class SQLiteEventRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def save_events(self, events: list[MarketEvent]) -> SaveSummary:
        inserted = 0
        duplicates = 0
        with self._session_factory() as session:
            for event in events:
                row = _event_to_row(event)
                session.add(row)
                try:
                    session.commit()
                    inserted += 1
                except IntegrityError:
                    session.rollback()
                    duplicates += 1
        return SaveSummary(inserted=inserted, duplicates=duplicates)

    async def get_event(self, event_id: str) -> MarketEvent | None:
        with self._session_factory() as session:
            row = session.execute(
                select(MarketEventRow).where(MarketEventRow.external_event_id == event_id)
            ).scalar_one_or_none()
            if row is None:
                return None
            symbols = [item.symbol for item in row.symbols]
        return _row_to_event(row, symbols)

    async def list_events(
        self,
        symbol: str | None = None,
        event_type: str | None = None,
        minimum_importance: int | None = None,
        limit: int = 100,
    ) -> list[MarketEvent]:
        limit = min(limit, 500)
        with self._session_factory() as session:
            stmt = select(MarketEventRow)
            if symbol:
                _validate_symbol(symbol)
                stmt = stmt.join(EventSymbolRow).where(EventSymbolRow.symbol == symbol.upper())
            if event_type:
                stmt = stmt.where(MarketEventRow.event_type == event_type)
            if minimum_importance is not None:
                stmt = stmt.where(MarketEventRow.importance_score >= minimum_importance)
            rows = session.execute(stmt.order_by(MarketEventRow.published_at.desc()).limit(limit)).scalars().all()
            result = [_row_to_event(row, [item.symbol for item in row.symbols]) for row in rows]
        return result


class SQLiteReportRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def save_report(self, report: MarketReport) -> SaveSummary:
        row = _report_to_row(report)
        with self._session_factory() as session:
            session.add(row)
            try:
                session.commit()
                return SaveSummary(inserted=1)
            except IntegrityError:
                session.rollback()
                existing = session.execute(
                    select(ReportRow).where(
                        ReportRow.report_type == row.report_type,
                        ReportRow.report_date == row.report_date,
                        ReportRow.content_hash == row.content_hash,
                    )
                ).scalar_one_or_none()
                if existing:
                    existing.report_id = row.report_id
                    existing.payload_json = row.payload_json
                    existing.generated_at = row.generated_at
                    session.commit()
                return SaveSummary(duplicates=1)

    async def get_report(self, report_id: str) -> MarketReport | None:
        with self._session_factory() as session:
            row = session.execute(
                select(ReportRow)
                .where(ReportRow.report_id == report_id)
                .order_by(ReportRow.generated_at.desc(), ReportRow.id.desc())
                .limit(1)
            ).scalar_one_or_none()
        return _row_to_report(row) if row else None

    async def list_reports(
        self,
        report_type: ReportType | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
    ) -> list[MarketReport]:
        limit = min(limit, 500)
        with self._session_factory() as session:
            stmt = select(ReportRow)
            if report_type:
                stmt = stmt.where(ReportRow.report_type == report_type.value)
            if date_from:
                stmt = stmt.where(ReportRow.generated_at >= date_from)
            if date_to:
                stmt = stmt.where(ReportRow.generated_at <= date_to)
            rows = session.execute(stmt.order_by(ReportRow.generated_at.desc()).limit(limit)).scalars().all()
        return [_row_to_report(row) for row in rows]


class SQLiteWatchlistRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def list_symbols(self) -> list[WatchlistItem]:
        with self._session_factory() as session:
            rows = session.execute(
                select(WatchlistSymbolRow).where(WatchlistSymbolRow.is_enabled.is_(True)).order_by(WatchlistSymbolRow.position)
            ).scalars().all()
        return [_row_to_watchlist(row) for row in rows]

    async def add_symbol(self, item: WatchlistItem) -> WatchlistItem:
        _validate_symbol(item.symbol)
        with self._session_factory() as session:
            count = session.scalar(select(func.count()).select_from(WatchlistSymbolRow).where(WatchlistSymbolRow.is_enabled.is_(True))) or 0
            if count >= 100:
                raise ValueError("watchlist_limit_reached")
            existing = session.execute(
                select(WatchlistSymbolRow).where(WatchlistSymbolRow.symbol == item.symbol.upper())
            ).scalar_one_or_none()
            if existing:
                if existing.is_enabled:
                    raise ValueError("watchlist_symbol_exists")
                existing.is_enabled = True
                existing.display_name = item.display_name
                existing.market = item.market
            else:
                session.add(
                    WatchlistSymbolRow(
                        symbol=item.symbol.upper(),
                        display_name=item.display_name,
                        market=item.market,
                        position=int(count),
                        is_enabled=True,
                    )
                )
            session.commit()
        return item

    async def remove_symbol(self, symbol: str) -> bool:
        _validate_symbol(symbol)
        with self._session_factory() as session:
            row = session.execute(
                select(WatchlistSymbolRow).where(WatchlistSymbolRow.symbol == symbol.upper())
            ).scalar_one_or_none()
            if row is None or not row.is_enabled:
                return False
            row.is_enabled = False
            session.commit()
            return True


class SQLiteAlertRuleRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def ensure_default_rules(self) -> None:
        with self._session_factory() as session:
            existing_count = session.scalar(select(func.count()).select_from(AlertRuleRow)) or 0
            if existing_count > 0:
                return
            now = datetime.now(UTC)
            for rule in _default_alert_rules(now):
                session.add(_alert_rule_to_row(rule))
            session.commit()

    async def list_rules(self, enabled_only: bool = False, rule_type: str | None = None) -> list[AlertRule]:
        with self._session_factory() as session:
            stmt = select(AlertRuleRow).order_by(AlertRuleRow.created_at.asc())
            if enabled_only:
                stmt = stmt.where(AlertRuleRow.is_enabled.is_(True))
            if rule_type:
                stmt = stmt.where(AlertRuleRow.rule_type == rule_type)
            rows = session.execute(stmt).scalars().all()
        return [_row_to_alert_rule(row) for row in rows]

    async def get_rule(self, rule_id: str) -> AlertRule | None:
        with self._session_factory() as session:
            row = session.execute(select(AlertRuleRow).where(AlertRuleRow.rule_id == rule_id)).scalar_one_or_none()
        return _row_to_alert_rule(row) if row else None

    async def create_rule(self, rule: AlertRule) -> AlertRule:
        with self._session_factory() as session:
            session.add(_alert_rule_to_row(rule))
            session.commit()
        return rule

    async def update_rule(self, rule_id: str, patch: AlertRuleUpdate) -> AlertRule | None:
        with self._session_factory() as session:
            row = session.execute(select(AlertRuleRow).where(AlertRuleRow.rule_id == rule_id)).scalar_one_or_none()
            if row is None:
                return None
            current = _row_to_alert_rule(row)
            merged = current.model_dump(mode="json")
            patch_data = patch.model_dump(exclude_unset=True)
            merged.update(patch_data)
            candidate = AlertRule.model_validate(merged)
            row.name = candidate.name
            row.severity = candidate.severity.value
            row.parameters_json = json.dumps(candidate.parameters, sort_keys=True)
            row.symbol_scope = candidate.symbol_scope.value
            row.symbols_json = json.dumps(candidate.symbols, sort_keys=True)
            row.is_enabled = candidate.is_enabled
            row.cooldown_seconds = candidate.cooldown_seconds
            row.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(row)
        return _row_to_alert_rule(row)

    async def set_enabled(self, rule_id: str, enabled: bool) -> AlertRule | None:
        return await self.update_rule(rule_id, AlertRuleUpdate(is_enabled=enabled))


class SQLiteAlertRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def save_alerts(self, alerts: list[AlertItem]) -> SaveSummary:
        inserted = 0
        duplicates = 0
        with self._session_factory() as session:
            for alert in alerts:
                session.add(_alert_to_row(alert))
                try:
                    session.commit()
                    inserted += 1
                except IntegrityError:
                    session.rollback()
                    duplicates += 1
        return SaveSummary(inserted=inserted, duplicates=duplicates)

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
        limit = min(limit, 200)
        now = datetime.now(UTC)
        with self._session_factory() as session:
            stmt = select(AlertRow)
            if status:
                stmt = stmt.where(AlertRow.status == status.value)
            if severity:
                stmt = stmt.where(AlertRow.severity == severity)
            if symbol:
                _validate_symbol(symbol)
                stmt = stmt.where(AlertRow.symbol == symbol.upper())
            if rule_type:
                stmt = stmt.where(AlertRow.alert_type == rule_type)
            if before:
                stmt = stmt.where(AlertRow.triggered_at <= before)
            if after:
                stmt = stmt.where(AlertRow.triggered_at >= after)
            if not include_snoozed:
                stmt = stmt.where(
                    (AlertRow.status != AlertStatus.SNOOZED.value)
                    | (AlertRow.snoozed_until.is_(None))
                    | (AlertRow.snoozed_until <= now)
                )
            rows = session.execute(stmt.order_by(AlertRow.triggered_at.desc()).limit(limit)).scalars().all()
        return [_row_to_alert(row, now=now) for row in rows]

    async def get_alert(self, alert_id: str) -> AlertItem | None:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            row = session.execute(select(AlertRow).where(AlertRow.alert_id == alert_id)).scalar_one_or_none()
        return _row_to_alert(row, now=now) if row else None

    async def acknowledge(self, alert_id: str, acknowledged_at: datetime) -> AlertItem | None:
        with self._session_factory() as session:
            row = session.execute(select(AlertRow).where(AlertRow.alert_id == alert_id)).scalar_one_or_none()
            if row is None:
                return None
            row.status = AlertStatus.ACKNOWLEDGED.value
            row.acknowledged_at = acknowledged_at
            row.updated_at = acknowledged_at
            session.commit()
            session.refresh(row)
        return _row_to_alert(row, now=acknowledged_at)

    async def snooze(self, alert_id: str, snoozed_until: datetime) -> AlertItem | None:
        with self._session_factory() as session:
            row = session.execute(select(AlertRow).where(AlertRow.alert_id == alert_id)).scalar_one_or_none()
            if row is None:
                return None
            row.status = AlertStatus.SNOOZED.value
            row.snoozed_until = snoozed_until
            row.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(row)
        return _row_to_alert(row, now=datetime.now(UTC))

    async def find_recent_for_cooldown(self, rule_id: str, symbol: str, since: datetime) -> AlertItem | None:
        with self._session_factory() as session:
            row = session.execute(
                select(AlertRow)
                .where(AlertRow.rule_id == rule_id, AlertRow.symbol == symbol.upper(), AlertRow.triggered_at >= since)
                .order_by(AlertRow.triggered_at.desc())
                .limit(1)
            ).scalar_one_or_none()
        return _row_to_alert(row, now=datetime.now(UTC)) if row else None

    async def summary(self, now: datetime) -> AlertSummary:
        with self._session_factory() as session:
            new_count = session.scalar(select(func.count()).select_from(AlertRow).where(AlertRow.status == AlertStatus.NEW.value)) or 0
            acknowledged = session.scalar(
                select(func.count()).select_from(AlertRow).where(AlertRow.status == AlertStatus.ACKNOWLEDGED.value)
            ) or 0
            snoozed = session.scalar(select(func.count()).select_from(AlertRow).where(AlertRow.status == AlertStatus.SNOOZED.value)) or 0
            high_or_critical = session.scalar(
                select(func.count()).select_from(AlertRow).where(AlertRow.severity.in_(["high", "critical"]))
            ) or 0
            latest = session.scalar(select(func.max(AlertRow.triggered_at)))
        return AlertSummary(
            new=new_count,
            acknowledged=acknowledged,
            snoozed=snoozed,
            high_or_critical=high_or_critical,
            latest_triggered_at=latest,
        )


class SQLiteJobRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def ensure_default_jobs(self) -> None:
        with self._session_factory() as session:
            existing_count = session.scalar(select(func.count()).select_from(ScheduledJobRow)) or 0
            if existing_count > 0:
                return
            now = datetime.now(UTC)
            for item in DEFAULT_JOBS:
                job = ScheduledJob(
                    id=f"job-{item.job_key}",
                    **item.model_dump(),
                    created_at=now,
                    updated_at=now,
                )
                session.add(_job_to_row(job))
            session.commit()

    async def list_jobs(self, enabled_only: bool = False, job_type: str | None = None) -> list[ScheduledJob]:
        with self._session_factory() as session:
            stmt = select(ScheduledJobRow).order_by(ScheduledJobRow.created_at.asc())
            if enabled_only:
                stmt = stmt.where(ScheduledJobRow.is_enabled.is_(True))
            if job_type:
                stmt = stmt.where(ScheduledJobRow.job_type == job_type)
            rows = session.execute(stmt).scalars().all()
        return [_row_to_job(row) for row in rows]

    async def get_job(self, job_id: str) -> ScheduledJob | None:
        with self._session_factory() as session:
            row = session.execute(select(ScheduledJobRow).where(ScheduledJobRow.job_id == job_id)).scalar_one_or_none()
        return _row_to_job(row) if row else None

    async def get_job_by_key(self, job_key: str) -> ScheduledJob | None:
        with self._session_factory() as session:
            row = session.execute(select(ScheduledJobRow).where(ScheduledJobRow.job_key == job_key)).scalar_one_or_none()
        return _row_to_job(row) if row else None

    async def update_job(self, job_id: str, patch: ScheduledJobUpdate) -> ScheduledJob | None:
        with self._session_factory() as session:
            row = session.execute(select(ScheduledJobRow).where(ScheduledJobRow.job_id == job_id)).scalar_one_or_none()
            if row is None:
                return None
            data = patch.model_dump(exclude_unset=True)
            for key, value in data.items():
                setattr(row, key, value)
            row.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(row)
        return _row_to_job(row)

    async def mark_run_schedule(self, job_id: str, last_run_at: datetime, next_run_at: datetime | None) -> None:
        with self._session_factory() as session:
            row = session.execute(select(ScheduledJobRow).where(ScheduledJobRow.job_id == job_id)).scalar_one_or_none()
            if row is None:
                return
            row.last_run_at = last_run_at
            row.next_run_at = next_run_at
            row.updated_at = datetime.now(UTC)
            session.commit()


class SQLiteJobRunRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def create_run(self, run: JobRun) -> JobRun:
        with self._session_factory() as session:
            session.add(_job_run_to_row(run))
            session.commit()
        return run

    async def update_run(self, run_id: str, **fields: object) -> JobRun | None:
        with self._session_factory() as session:
            row = session.execute(select(JobRunRow).where(JobRunRow.run_id == run_id)).scalar_one_or_none()
            if row is None:
                return None
            for key, value in fields.items():
                if key in {"input_summary", "result_summary"}:
                    setattr(row, f"{key}_json", json.dumps(value, sort_keys=True))
                elif key in {"status", "trigger_type", "error_code"} and value is not None and hasattr(value, "value"):
                    setattr(row, key, value.value)
                else:
                    setattr(row, key, value.value if hasattr(value, "value") else value)
            session.commit()
            session.refresh(row)
        return _row_to_job_run(row)

    async def get_run(self, run_id: str) -> JobRun | None:
        with self._session_factory() as session:
            row = session.execute(select(JobRunRow).where(JobRunRow.run_id == run_id)).scalar_one_or_none()
        return _row_to_job_run(row) if row else None

    async def list_runs(
        self,
        job_type: str | None = None,
        status: JobRunStatus | None = None,
        trigger_type: JobTriggerType | None = None,
        limit: int = 100,
        before: datetime | None = None,
        after: datetime | None = None,
    ) -> list[JobRun]:
        limit = min(limit, 200)
        with self._session_factory() as session:
            stmt = select(JobRunRow)
            if job_type:
                stmt = stmt.where(JobRunRow.job_type == job_type)
            if status:
                stmt = stmt.where(JobRunRow.status == status.value)
            if trigger_type:
                stmt = stmt.where(JobRunRow.trigger_type == trigger_type.value)
            if before:
                stmt = stmt.where(JobRunRow.created_at <= before)
            if after:
                stmt = stmt.where(JobRunRow.created_at >= after)
            rows = session.execute(stmt.order_by(JobRunRow.created_at.desc()).limit(limit)).scalars().all()
        return [_row_to_job_run(row) for row in rows]


class SQLiteJobLockRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def acquire(self, job_key: str, lock_owner: str, expires_at: datetime, now: datetime) -> bool:
        with self._session_factory() as session:
            existing = session.execute(select(JobLockRow).where(JobLockRow.job_key == job_key)).scalar_one_or_none()
            if existing and _ensure_utc(existing.expires_at) and (_ensure_utc(existing.expires_at) or now) > now:
                return False
            if existing:
                existing.lock_owner = lock_owner
                existing.acquired_at = now
                existing.expires_at = expires_at
            else:
                session.add(JobLockRow(job_key=job_key, lock_owner=lock_owner, acquired_at=now, expires_at=expires_at))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                return False
        return True

    async def release(self, job_key: str, lock_owner: str) -> None:
        with self._session_factory() as session:
            row = session.execute(
                select(JobLockRow).where(JobLockRow.job_key == job_key, JobLockRow.lock_owner == lock_owner)
            ).scalar_one_or_none()
            if row is None:
                return
            session.delete(row)
            session.commit()


class StorageMetrics:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def status(self) -> dict[str, int | bool | str]:
        with self._session_factory() as session:
            return {
                "backend": "sqlite",
                "database_ready": True,
                "database_location_type": "project_runtime",
                "quotes_count": session.scalar(select(func.count()).select_from(QuoteSnapshotRow)) or 0,
                "events_count": session.scalar(select(func.count()).select_from(MarketEventRow)) or 0,
                "reports_count": session.scalar(select(func.count()).select_from(ReportRow)) or 0,
                "watchlist_count": session.scalar(select(func.count()).select_from(WatchlistSymbolRow).where(WatchlistSymbolRow.is_enabled.is_(True))) or 0,
                "alert_rules_count": session.scalar(select(func.count()).select_from(AlertRuleRow)) or 0,
                "enabled_alert_rules_count": session.scalar(
                    select(func.count()).select_from(AlertRuleRow).where(AlertRuleRow.is_enabled.is_(True))
                ) or 0,
                "alerts_count": session.scalar(select(func.count()).select_from(AlertRow)) or 0,
                "new_alerts_count": session.scalar(
                    select(func.count()).select_from(AlertRow).where(AlertRow.status == AlertStatus.NEW.value)
                ) or 0,
                "scheduled_jobs_count": session.scalar(select(func.count()).select_from(ScheduledJobRow)) or 0,
                "enabled_jobs_count": session.scalar(
                    select(func.count()).select_from(ScheduledJobRow).where(ScheduledJobRow.is_enabled.is_(True))
                ) or 0,
                "job_runs_count": session.scalar(select(func.count()).select_from(JobRunRow)) or 0,
                "running_jobs_count": session.scalar(
                    select(func.count()).select_from(JobRunRow).where(JobRunRow.status == JobRunStatus.RUNNING.value)
                ) or 0,
                "failed_job_runs_count": session.scalar(
                    select(func.count()).select_from(JobRunRow).where(JobRunRow.status == JobRunStatus.FAILED.value)
                ) or 0,
                "automatic_deletion_enabled": False,
            }

    def retention_preview(self, quote_retention_days: int = 30) -> dict[str, int | bool]:
        cutoff = datetime.now(UTC) - timedelta(days=quote_retention_days)
        with self._session_factory() as session:
            eligible = session.scalar(
                select(func.count()).select_from(QuoteSnapshotRow).where(QuoteSnapshotRow.recorded_at < cutoff)
            ) or 0
        return {
            "quote_retention_days": quote_retention_days,
            "eligible_quote_rows": eligible,
            "automatic_deletion_enabled": False,
        }


def _quote_to_row(snapshot: QuoteSnapshot) -> QuoteSnapshotRow:
    key = _hash_text(f"{snapshot.symbol}|{snapshot.provider}|{snapshot.timestamp.isoformat()}")
    return QuoteSnapshotRow(
        symbol=snapshot.symbol.upper(),
        display_name=snapshot.display_name,
        market=snapshot.market,
        currency=snapshot.currency,
        provider=snapshot.provider,
        price=snapshot.price,
        previous_close=snapshot.previous_close,
        change=snapshot.change,
        change_percent=snapshot.change_percent,
        volume=snapshot.volume,
        average_volume_20d=snapshot.average_volume_20d,
        market_status=snapshot.market_status,
        source_timestamp=snapshot.timestamp,
        is_delayed=snapshot.is_delayed,
        is_mock=snapshot.provider == "mock",
        deduplication_key=key,
    )


def _row_to_quote(row: QuoteSnapshotRow) -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol=row.symbol,
        display_name=row.display_name,
        market=row.market,
        currency=row.currency,
        provider=row.provider,
        price=row.price,
        previous_close=row.previous_close,
        change=row.change,
        change_percent=row.change_percent,
        volume=row.volume,
        average_volume_20d=row.average_volume_20d,
        market_status=row.market_status,
        timestamp=row.source_timestamp,
        is_delayed=row.is_delayed,
    )


def _event_to_row(event: MarketEvent) -> MarketEventRow:
    content_hash = _hash_text(
        json.dumps(
            {
                "event_type": event.event_type.value,
                "title": event.title,
                "source_name": event.source_name,
                "published_at": event.published_at.isoformat(),
                "symbols": sorted(event.affected_symbols),
            },
            sort_keys=True,
        )
    )
    row = MarketEventRow(
        external_event_id=event.id,
        event_type=event.event_type.value,
        title=event.title,
        summary=event.summary,
        source_name=event.source_name,
        source_url=event.source_url,
        published_at=event.published_at,
        received_at=event.received_at,
        importance_score=event.importance_score,
        reliability_score=event.reliability_score,
        sentiment=event.sentiment.value,
        confidence=event.confidence,
        is_mock=event.is_mock,
        content_hash=content_hash,
    )
    row.symbols = [EventSymbolRow(symbol=symbol.upper()) for symbol in event.affected_symbols]
    return row


def _row_to_event(row: MarketEventRow, symbols: list[str]) -> MarketEvent:
    return MarketEvent(
        id=row.external_event_id,
        event_type=row.event_type,
        title=row.title,
        summary=row.summary,
        source_name=row.source_name,
        source_url=row.source_url,
        published_at=row.published_at,
        received_at=row.received_at,
        affected_symbols=symbols,
        importance_score=row.importance_score,
        reliability_score=row.reliability_score,
        sentiment=row.sentiment,
        confidence=float(row.confidence),
        is_mock=row.is_mock,
    )


def _report_to_row(report: MarketReport) -> ReportRow:
    payload = report.model_dump_json()
    stable_payload = json.dumps(
        {
            "report_type": report.report_type.value,
            "summary": report.summary,
            "key_points": report.key_points,
            "event_groups": {
                key.value if hasattr(key, "value") else str(key): [item.model_dump(mode="json") for item in value]
                for key, value in report.event_groups.items()
            },
            "market_move_alerts": [item.model_dump(mode="json") for item in report.market_move_alerts],
            "is_mock": report.is_mock,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return ReportRow(
        report_id=report.id,
        report_type=report.report_type.value,
        report_date=report.generated_at.date().isoformat(),
        generated_at=report.generated_at,
        provider_summary=report.data_source,
        is_mock=report.is_mock,
        schema_version=1,
        payload_json=payload,
        content_hash=_hash_text(stable_payload),
    )


def _row_to_report(row: ReportRow) -> MarketReport:
    return MarketReport.model_validate_json(row.payload_json)


def _row_to_watchlist(row: WatchlistSymbolRow) -> WatchlistItem:
    return WatchlistItem(
        symbol=row.symbol,
        display_name=row.display_name,
        market=row.market,
        note="Local watchlist item.",
        is_mock=True,
    )


def _default_alert_rules(now: datetime) -> list[AlertRule]:
    defaults = [
        AlertRuleCreate(
            name="Watchlist price move",
            rule_type=AlertRuleType.PRICE_CHANGE_ABSOLUTE,
            severity=AlertSeverity.HIGH,
            symbol_scope=AlertSymbolScope.WATCHLIST,
            cooldown_seconds=1800,
            parameters={"threshold_percent": 3.0, "direction": "any"},
        ),
        AlertRuleCreate(
            name="Watchlist volume spike",
            rule_type=AlertRuleType.VOLUME_RATIO,
            severity=AlertSeverity.MEDIUM,
            symbol_scope=AlertSymbolScope.WATCHLIST,
            cooldown_seconds=1800,
            parameters={"threshold_ratio": 2.0},
        ),
        AlertRuleCreate(
            name="High importance event",
            rule_type=AlertRuleType.EVENT_IMPORTANCE,
            severity=AlertSeverity.HIGH,
            symbol_scope=AlertSymbolScope.WATCHLIST,
            cooldown_seconds=3600,
            parameters={"minimum_importance": 80},
        ),
        AlertRuleCreate(
            name="Price and volume confirmation",
            rule_type=AlertRuleType.PRICE_AND_VOLUME,
            severity=AlertSeverity.CRITICAL,
            symbol_scope=AlertSymbolScope.WATCHLIST,
            cooldown_seconds=3600,
            parameters={"minimum_absolute_change_percent": 3.0, "minimum_volume_ratio": 2.0},
        ),
    ]
    return [
        AlertRule(
            id=f"default-{item.rule_type.value}",
            **item.model_dump(),
            is_system_default=True,
            created_at=now,
            updated_at=now,
        )
        for item in defaults
    ]


def _alert_rule_to_row(rule: AlertRule) -> AlertRuleRow:
    return AlertRuleRow(
        rule_id=rule.id,
        name=rule.name,
        rule_type=rule.rule_type.value,
        severity=rule.severity.value,
        parameters_json=json.dumps(rule.parameters, sort_keys=True),
        symbol_scope=rule.symbol_scope.value,
        symbols_json=json.dumps(rule.symbols, sort_keys=True),
        is_enabled=rule.is_enabled,
        cooldown_seconds=rule.cooldown_seconds,
        is_system_default=rule.is_system_default,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _row_to_alert_rule(row: AlertRuleRow) -> AlertRule:
    return AlertRule(
        id=row.rule_id,
        name=row.name,
        rule_type=row.rule_type,
        severity=row.severity,
        parameters=json.loads(row.parameters_json),
        symbol_scope=row.symbol_scope,
        symbols=json.loads(row.symbols_json),
        is_enabled=row.is_enabled,
        cooldown_seconds=row.cooldown_seconds,
        is_system_default=row.is_system_default,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _alert_to_row(alert: AlertItem) -> AlertRow:
    return AlertRow(
        alert_id=alert.id,
        rule_id=alert.rule_id,
        alert_type=alert.alert_type.value,
        severity=alert.severity.value,
        title=alert.title,
        message=alert.message,
        symbol=alert.symbol.upper() if alert.symbol else None,
        event_id=alert.event_id,
        source_timestamp=alert.source_timestamp,
        triggered_at=alert.triggered_at,
        status=alert.status.value,
        acknowledged_at=alert.acknowledged_at,
        snoozed_until=alert.snoozed_until,
        is_mock=alert.is_mock,
        deduplication_key=alert.deduplication_key,
        metadata_json=json.dumps(alert.metadata, sort_keys=True),
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


def _row_to_alert(row: AlertRow, now: datetime) -> AlertItem:
    status = row.status
    snoozed_until = _ensure_utc(row.snoozed_until)
    if status == AlertStatus.SNOOZED.value and snoozed_until is not None and snoozed_until <= now:
        status = AlertStatus.NEW.value
    return AlertItem(
        id=row.alert_id,
        rule_id=row.rule_id,
        alert_type=row.alert_type,
        severity=row.severity,
        title=row.title,
        message=row.message,
        symbol=row.symbol,
        event_id=row.event_id,
        source_timestamp=_ensure_utc(row.source_timestamp),
        triggered_at=_ensure_utc(row.triggered_at) or row.triggered_at,
        status=status,
        acknowledged_at=_ensure_utc(row.acknowledged_at),
        snoozed_until=snoozed_until,
        is_mock=row.is_mock,
        deduplication_key=row.deduplication_key,
        metadata=json.loads(row.metadata_json),
        created_at=_ensure_utc(row.created_at) or row.created_at,
        updated_at=_ensure_utc(row.updated_at) or row.updated_at,
    )


def alert_from_candidate(candidate: "object") -> AlertItem:
    now = datetime.now(UTC)
    return AlertItem(
        id=f"alert-{uuid.uuid4().hex}",
        rule_id=getattr(candidate, "rule_id"),
        alert_type=getattr(candidate, "alert_type"),
        severity=getattr(candidate, "severity"),
        title=getattr(candidate, "title"),
        message=getattr(candidate, "message"),
        symbol=getattr(candidate, "symbol"),
        event_id=getattr(candidate, "event_id"),
        source_timestamp=getattr(candidate, "source_timestamp"),
        triggered_at=getattr(candidate, "triggered_at"),
        status=AlertStatus.NEW,
        acknowledged_at=None,
        snoozed_until=None,
        is_mock=getattr(candidate, "is_mock"),
        deduplication_key=getattr(candidate, "deduplication_key"),
        metadata=getattr(candidate, "metadata"),
        created_at=now,
        updated_at=now,
    )


def _job_to_row(job: ScheduledJob) -> ScheduledJobRow:
    return ScheduledJobRow(
        job_id=job.id,
        job_key=job.job_key,
        job_type=job.job_type.value,
        display_name=job.display_name,
        is_enabled=job.is_enabled,
        interval_seconds=job.interval_seconds,
        timeout_seconds=job.timeout_seconds,
        max_retries=job.max_retries,
        last_run_at=job.last_run_at,
        next_run_at=job.next_run_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _row_to_job(row: ScheduledJobRow) -> ScheduledJob:
    return ScheduledJob(
        id=row.job_id,
        job_key=row.job_key,
        job_type=row.job_type,
        display_name=row.display_name,
        is_enabled=row.is_enabled,
        interval_seconds=row.interval_seconds,
        timeout_seconds=row.timeout_seconds,
        max_retries=row.max_retries,
        last_run_at=_ensure_utc(row.last_run_at),
        next_run_at=_ensure_utc(row.next_run_at),
        created_at=_ensure_utc(row.created_at) or row.created_at,
        updated_at=_ensure_utc(row.updated_at) or row.updated_at,
    )


def _job_run_to_row(run: JobRun) -> JobRunRow:
    return JobRunRow(
        run_id=run.id,
        job_id=run.job_id,
        job_key=run.job_key,
        job_type=run.job_type.value,
        status=run.status.value,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_ms=run.duration_ms,
        attempt=run.attempt,
        trigger_type=run.trigger_type.value,
        input_summary_json=json.dumps(run.input_summary, sort_keys=True),
        result_summary_json=json.dumps(run.result_summary, sort_keys=True),
        error_code=run.error_code.value if run.error_code else None,
        error_message=run.error_message,
        created_at=run.created_at,
    )


def _row_to_job_run(row: JobRunRow) -> JobRun:
    return JobRun(
        id=row.run_id,
        job_id=row.job_id,
        job_key=row.job_key,
        job_type=row.job_type,
        status=row.status,
        started_at=_ensure_utc(row.started_at),
        finished_at=_ensure_utc(row.finished_at),
        duration_ms=row.duration_ms,
        attempt=row.attempt,
        trigger_type=row.trigger_type,
        input_summary=json.loads(row.input_summary_json),
        result_summary=json.loads(row.result_summary_json),
        error_code=row.error_code,
        error_message=row.error_message,
        created_at=_ensure_utc(row.created_at) or row.created_at,
    )


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_symbol(symbol: str) -> None:
    if not SUPPORTED_SYMBOL_RE.fullmatch(symbol.upper()):
        raise ValueError("invalid_symbol")


def _ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
