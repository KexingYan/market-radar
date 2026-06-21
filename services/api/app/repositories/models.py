from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


class QuoteSnapshotRow(Base):
    __tablename__ = "quote_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    market: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(12))
    provider: Mapped[str] = mapped_column(String(32))
    price: Mapped[float] = mapped_column(Numeric(20, 6))
    previous_close: Mapped[float] = mapped_column(Numeric(20, 6))
    change: Mapped[float] = mapped_column(Numeric(20, 6))
    change_percent: Mapped[float] = mapped_column(Numeric(20, 6))
    volume: Mapped[int] = mapped_column(Integer)
    average_volume_20d: Mapped[int] = mapped_column(Integer)
    market_status: Mapped[str] = mapped_column(String(64))
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    is_delayed: Mapped[bool] = mapped_column(Boolean)
    is_mock: Mapped[bool] = mapped_column(Boolean)
    deduplication_key: Mapped[str] = mapped_column(String(160), unique=True)

    __table_args__ = (
        Index("ix_quote_symbol_source_timestamp", "symbol", "source_timestamp"),
        Index("ix_quote_symbol_recorded_at", "symbol", "recorded_at"),
    )


class MarketEventRow(Base):
    __tablename__ = "market_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_event_id: Mapped[str] = mapped_column(String(160), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text)
    source_name: Mapped[str] = mapped_column(String(120))
    source_url: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    importance_score: Mapped[int] = mapped_column(Integer)
    reliability_score: Mapped[int] = mapped_column(Integer)
    sentiment: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Numeric(5, 4))
    is_mock: Mapped[bool] = mapped_column(Boolean)
    content_hash: Mapped[str] = mapped_column(String(96), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    symbols: Mapped[list["EventSymbolRow"]] = relationship(cascade="all, delete-orphan")


class EventSymbolRow(Base):
    __tablename__ = "event_symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("market_events.id"))
    symbol: Mapped[str] = mapped_column(String(32), index=True)

    __table_args__ = (UniqueConstraint("event_id", "symbol", name="uq_event_symbol"),)


class ReportRow(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[str] = mapped_column(String(160), index=True)
    report_type: Mapped[str] = mapped_column(String(32), index=True)
    report_date: Mapped[str] = mapped_column(String(10), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    provider_summary: Mapped[str] = mapped_column(String(120))
    is_mock: Mapped[bool] = mapped_column(Boolean)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    payload_json: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(96))

    __table_args__ = (UniqueConstraint("report_type", "report_date", "content_hash", name="uq_report_content"),)


class WatchlistSymbolRow(Base):
    __tablename__ = "watchlist_symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    market: Mapped[str] = mapped_column(String(32))
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class AlertRuleRow(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    rule_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32))
    parameters_json: Mapped[str] = mapped_column(Text)
    symbol_scope: Mapped[str] = mapped_column(String(32))
    symbols_json: Mapped[str] = mapped_column(Text, default="[]")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    cooldown_seconds: Mapped[int] = mapped_column(Integer)
    is_system_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (Index("ix_alert_rule_type_enabled", "rule_type", "is_enabled"),)


class AlertRow(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    rule_id: Mapped[str] = mapped_column(String(160), index=True)
    alert_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    symbol: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(160), index=True, nullable=True)
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean)
    deduplication_key: Mapped[str] = mapped_column(String(160), unique=True)
    metadata_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_alert_rule_symbol_triggered", "rule_id", "symbol", "triggered_at"),
        Index("ix_alert_status_triggered", "status", "triggered_at"),
    )


class ScheduledJobRow(Base):
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    job_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    interval_seconds: Mapped[int] = mapped_column(Integer)
    timeout_seconds: Mapped[int] = mapped_column(Integer)
    max_retries: Mapped[int] = mapped_column(Integer)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (Index("ix_scheduled_job_type_enabled", "job_type", "is_enabled"),)


class JobRunRow(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    job_id: Mapped[str] = mapped_column(String(160), index=True)
    job_key: Mapped[str] = mapped_column(String(80), index=True)
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer)
    trigger_type: Mapped[str] = mapped_column(String(32), index=True)
    input_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    result_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(240), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_job_run_type_status", "job_type", "status"),
        Index("ix_job_run_trigger_created", "trigger_type", "created_at"),
    )


class JobLockRow(Base):
    __tablename__ = "job_locks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    lock_owner: Mapped[str] = mapped_column(String(160))
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
