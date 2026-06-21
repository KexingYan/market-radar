import os
import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict

from app.alerts.models import AlertEvaluationRequest, AlertEvaluationResult
from app.alerts.service import AlertService
from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot
from app.jobs.models import JobRun, JobRunStatus, JobTriggerType, JobType
from app.providers.base import ProviderUnavailableError
from app.providers.moomoo_quotes import SUPPORTED_SYMBOL_RE, MoomooQuoteProvider
from app.providers.sec_edgar import SUPPORTED_FORMS, SecEdgarEventProvider
from app.reports.engine import build_intraday_report
from app.services.archive import ArchiveResult, ArchiveService

LIVE_E2E_SYMBOL = "AAPL"
MAX_WATCHLIST_REFRESH_SYMBOLS = 5


class LiveE2EModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SecE2ESummary(LiveE2EModel):
    attempted: bool
    success: bool
    request_count: int
    filings_parsed: int
    fallback_used: bool


class MoomooE2ESummary(LiveE2EModel):
    attempted: bool
    success: bool
    snapshot_rows: int
    quote_context_closed: bool
    fallback_used: bool


class ArchiveE2ESummary(LiveE2EModel):
    inserted: int
    duplicates: int
    failed: int


class ReportE2ESummary(LiveE2EModel):
    generated: bool
    archived: int
    duplicate: int
    failed: int


class AlertE2ESummary(LiveE2EModel):
    evaluated_rules: int
    evaluated_symbols: int
    created_alerts: int
    duplicate_alerts: int
    cooldown_suppressed: int
    mock_data_used: bool


class JobRunE2ESummary(LiveE2EModel):
    saved: bool
    status: str


class LiveAaplE2EResponse(LiveE2EModel):
    symbol: str
    sec: SecE2ESummary
    moomoo: MoomooE2ESummary
    quote_archive: ArchiveE2ESummary
    event_archive: ArchiveE2ESummary
    report: ReportE2ESummary
    alerts: AlertE2ESummary
    job_run: JobRunE2ESummary
    trading_enabled: bool = False
    paid_data_enabled: bool = False


class LiveWatchlistRefreshResponse(LiveE2EModel):
    symbols: list[str]
    fallback_symbol_used: bool
    sec: SecE2ESummary
    moomoo: MoomooE2ESummary
    quote_archive: ArchiveE2ESummary
    event_archive: ArchiveE2ESummary
    report: ReportE2ESummary
    alerts: AlertE2ESummary
    job_run: JobRunE2ESummary
    trading_enabled: bool = False
    paid_data_enabled: bool = False


class QuoteProvider(Protocol):
    async def get_quotes(self, symbols: list[str] | None = None) -> list[QuoteSnapshot]:
        ...


class EventProvider(Protocol):
    async def get_events(
        self,
        symbols: list[str] | None = None,
        minimum_importance: int | None = None,
    ) -> list[MarketEvent]:
        ...


class StaticQuoteProvider:
    def __init__(self, quotes: list[QuoteSnapshot]) -> None:
        self._quotes = quotes

    async def get_quotes(self, symbols: list[str] | None = None) -> list[QuoteSnapshot]:
        requested = {symbol.upper() for symbol in (symbols or [])}
        if not requested:
            return self._quotes
        return [quote for quote in self._quotes if quote.symbol.upper() in requested]

    async def get_quote(self, symbol: str) -> QuoteSnapshot | None:
        quotes = await self.get_quotes([symbol])
        return quotes[0] if quotes else None


class StaticEventProvider:
    def __init__(self, events: list[MarketEvent]) -> None:
        self._events = events

    async def get_events(
        self,
        symbols: list[str] | None = None,
        minimum_importance: int | None = None,
    ) -> list[MarketEvent]:
        requested = {symbol.upper() for symbol in (symbols or [])}
        events = self._events
        if requested:
            events = [event for event in events if requested.intersection({item.upper() for item in event.affected_symbols})]
        if minimum_importance is not None:
            events = [event for event in events if event.importance_score >= minimum_importance]
        return events


class LiveAaplE2EService:
    def __init__(
        self,
        archive_service: ArchiveService,
        alert_service_factory,
        job_run_repository,
        sec_provider_factory=lambda user_agent: SecEdgarEventProvider(user_agent),
        quote_provider_factory=lambda: MoomooQuoteProvider(cache_ttl_seconds=0, request_interval_seconds=0),
        max_sec_events: int = 50,
        max_sec_events_per_symbol: int = 10,
    ) -> None:
        self._archive = archive_service
        self._alert_service_factory = alert_service_factory
        self._job_runs = job_run_repository
        self._sec_provider_factory = sec_provider_factory
        self._quote_provider_factory = quote_provider_factory
        self._max_sec_events = max_sec_events
        self._max_sec_events_per_symbol = max_sec_events_per_symbol

    async def run(self) -> LiveAaplE2EResponse:
        started = datetime.now(UTC)
        quotes, moomoo_summary = await self._collect_moomoo_quotes([LIVE_E2E_SYMBOL])
        events, sec_summary = await self._collect_sec_events([LIVE_E2E_SYMBOL], max_events=self._max_sec_events)

        quote_archive = await self._archive.archive_quotes(quotes)
        event_archive = await self._archive.archive_events(events)

        report = build_intraday_report(quotes, events, started)
        report_archive = await self._archive.archive_report(report)

        alert_service = self._alert_service_factory(StaticQuoteProvider(quotes), StaticEventProvider(events))
        alert_result = await alert_service.evaluate(
            AlertEvaluationRequest(symbols=[LIVE_E2E_SYMBOL], include_quotes=True, include_events=True)
        )

        response = LiveAaplE2EResponse(
            symbol=LIVE_E2E_SYMBOL,
            sec=sec_summary,
            moomoo=moomoo_summary,
            quote_archive=_archive_summary(quote_archive),
            event_archive=_archive_summary(event_archive),
            report=ReportE2ESummary(
                generated=True,
                archived=report_archive.inserted,
                duplicate=report_archive.duplicates,
                failed=report_archive.failed,
            ),
            alerts=_alert_summary(alert_result),
            job_run=JobRunE2ESummary(saved=False, status="running"),
        )

        saved = await self._save_job_run(response, started)
        response.job_run = JobRunE2ESummary(saved=saved, status="succeeded" if saved else "failed")
        return response

    async def run_watchlist_refresh(self, watchlist_items) -> LiveWatchlistRefreshResponse:
        started = datetime.now(UTC)
        symbols = self._watchlist_symbols(watchlist_items)
        fallback_used = not symbols
        if fallback_used:
            symbols = [LIVE_E2E_SYMBOL]

        quotes, moomoo_summary = await self._collect_moomoo_quotes(symbols)
        events, sec_summary = await self._collect_sec_events(symbols, max_events=self._max_sec_events_per_symbol * len(symbols))

        quote_archive = await self._archive.archive_quotes(quotes)
        event_archive = await self._archive.archive_events(events)

        report = build_intraday_report(quotes, events, started)
        report_archive = await self._archive.archive_report(report)

        alert_service = self._alert_service_factory(StaticQuoteProvider(quotes), StaticEventProvider(events))
        alert_result = await alert_service.evaluate(
            AlertEvaluationRequest(symbols=symbols, include_quotes=True, include_events=True)
        )

        response = LiveWatchlistRefreshResponse(
            symbols=symbols,
            fallback_symbol_used=fallback_used,
            sec=sec_summary,
            moomoo=moomoo_summary,
            quote_archive=_archive_summary(quote_archive),
            event_archive=_archive_summary(event_archive),
            report=ReportE2ESummary(
                generated=True,
                archived=report_archive.inserted,
                duplicate=report_archive.duplicates,
                failed=report_archive.failed,
            ),
            alerts=_alert_summary(alert_result),
            job_run=JobRunE2ESummary(saved=False, status="running"),
        )
        saved = await self._save_watchlist_job_run(response, started)
        response.job_run = JobRunE2ESummary(saved=saved, status="succeeded" if saved else "failed")
        return response

    async def _collect_moomoo_quotes(self, symbols: list[str]) -> tuple[list[QuoteSnapshot], MoomooE2ESummary]:
        try:
            quotes = await self._quote_provider_factory().get_quotes(symbols)
            return quotes, MoomooE2ESummary(
                attempted=True,
                success=bool(quotes),
                snapshot_rows=len(quotes),
                quote_context_closed=True,
                fallback_used=not bool(quotes),
            )
        except ProviderUnavailableError:
            return [], MoomooE2ESummary(
                attempted=True,
                success=False,
                snapshot_rows=0,
                quote_context_closed=True,
                fallback_used=True,
            )

    async def _collect_sec_events(self, symbols: list[str], max_events: int) -> tuple[list[MarketEvent], SecE2ESummary]:
        user_agent = os.getenv("SEC_USER_AGENT")
        if not user_agent:
            return [], SecE2ESummary(attempted=False, success=False, request_count=0, filings_parsed=0, fallback_used=True)

        request_count = 0
        try:
            provider = self._sec_provider_factory(user_agent)
            mapping = await provider.get_ticker_mapping()
            request_count += 1
            events: list[MarketEvent] = []
            for symbol in symbols:
                record = mapping.get(symbol)
                if not record:
                    continue
                submissions = await provider.get_company_submissions(str(record["cik_str"]))
                request_count += 1
                events.extend(
                    provider.submissions_to_events(symbol, record, submissions, SUPPORTED_FORMS)[
                        : self._max_sec_events_per_symbol
                    ]
                )
            events = events[:max_events]
            if not events:
                return [], SecE2ESummary(
                    attempted=True,
                    success=False,
                    request_count=request_count,
                    filings_parsed=0,
                    fallback_used=True,
                )
            return events, SecE2ESummary(
                attempted=True,
                success=bool(events),
                request_count=request_count,
                filings_parsed=len(events),
                fallback_used=not bool(events),
            )
        except ProviderUnavailableError:
            return [], SecE2ESummary(
                attempted=True,
                success=False,
                request_count=request_count,
                filings_parsed=0,
                fallback_used=True,
            )

    @staticmethod
    def _watchlist_symbols(watchlist_items) -> list[str]:
        symbols: list[str] = []
        for item in watchlist_items:
            symbol = str(item.symbol).upper()
            if "." in symbol or not SUPPORTED_SYMBOL_RE.fullmatch(symbol):
                continue
            if symbol not in symbols:
                symbols.append(symbol)
            if len(symbols) >= MAX_WATCHLIST_REFRESH_SYMBOLS:
                break
        return symbols

    async def _save_job_run(self, response: LiveAaplE2EResponse, started: datetime) -> bool:
        finished = datetime.now(UTC)
        run = JobRun(
            id=f"run-{uuid.uuid4().hex}",
            job_id="live-aapl-e2e",
            job_key="live_aapl_e2e",
            job_type=JobType.FULL_PIPELINE,
            status=JobRunStatus.SUCCEEDED,
            started_at=started,
            finished_at=finished,
            duration_ms=int((finished - started).total_seconds() * 1000),
            attempt=1,
            trigger_type=JobTriggerType.MANUAL,
            input_summary={"symbol": LIVE_E2E_SYMBOL, "mode": "live_e2e"},
            result_summary=response.model_dump(mode="json", exclude={"job_run"}),
            error_code=None,
            error_message=None,
            created_at=started,
        )
        await self._job_runs.create_run(run)
        return True

    async def _save_watchlist_job_run(self, response: LiveWatchlistRefreshResponse, started: datetime) -> bool:
        finished = datetime.now(UTC)
        run = JobRun(
            id=f"run-{uuid.uuid4().hex}",
            job_id="live-watchlist-refresh",
            job_key="live_watchlist_refresh",
            job_type=JobType.FULL_PIPELINE,
            status=JobRunStatus.SUCCEEDED,
            started_at=started,
            finished_at=finished,
            duration_ms=int((finished - started).total_seconds() * 1000),
            attempt=1,
            trigger_type=JobTriggerType.MANUAL,
            input_summary={"symbol_count": len(response.symbols), "mode": "watchlist_live_refresh"},
            result_summary=response.model_dump(mode="json", exclude={"job_run"}),
            error_code=None,
            error_message=None,
            created_at=started,
        )
        await self._job_runs.create_run(run)
        return True


def _archive_summary(result: ArchiveResult) -> ArchiveE2ESummary:
    return ArchiveE2ESummary(inserted=result.inserted, duplicates=result.duplicates, failed=result.failed)


def _alert_summary(result: AlertEvaluationResult) -> AlertE2ESummary:
    return AlertE2ESummary(
        evaluated_rules=result.evaluated_rules,
        evaluated_symbols=result.evaluated_symbols,
        created_alerts=result.created_alerts,
        duplicate_alerts=result.duplicate_alerts,
        cooldown_suppressed=result.cooldown_suppressed,
        mock_data_used=result.mock_data_used,
    )
