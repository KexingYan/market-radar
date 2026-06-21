from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from app.alerts.models import AlertEvaluationRequest
from app.alerts.service import AlertService
from app.domain.report import ReportType
from app.providers.base import EventDataProvider, MarketDataProvider
from app.reports.engine import build_close_report, build_intraday_report, build_premarket_report
from app.services.archive import ArchiveService


class WatchlistReader(Protocol):
    async def list_symbols(self):
        ...


@dataclass(frozen=True)
class TaskContext:
    quote_provider: MarketDataProvider
    event_provider: EventDataProvider
    watchlist_repository: WatchlistReader
    archive_service: ArchiveService
    alert_service: AlertService


async def collect_quotes(context: TaskContext) -> dict[str, Any]:
    symbols = [item.symbol for item in await context.watchlist_repository.list_symbols()]
    if len(symbols) > 20:
        symbols = symbols[:20]
    quotes = await context.quote_provider.get_quotes(symbols or None)  # type: ignore[arg-type]
    archive = await context.archive_service.archive_quotes(quotes)
    return {
        "requested_symbols": len(symbols),
        "received_quotes": len(quotes),
        "archived_quotes": archive.inserted,
        "duplicate_quotes": archive.duplicates,
        "failed_quotes": archive.failed,
        "provider": "mock" if all(quote.provider == "mock" for quote in quotes) else "mixed",
        "mock_data_used": any(quote.provider == "mock" for quote in quotes),
    }


async def collect_events(context: TaskContext) -> dict[str, Any]:
    symbols = [item.symbol for item in await context.watchlist_repository.list_symbols()]
    events = await context.event_provider.get_events(symbols=symbols or None)
    archive = await context.archive_service.archive_events(events)
    return {
        "requested_symbols": len(symbols),
        "received_events": len(events),
        "archived_events": archive.inserted,
        "duplicate_events": archive.duplicates,
        "failed_events": archive.failed,
        "provider": "mock" if all(event.is_mock for event in events) else "mixed",
        "mock_data_used": any(event.is_mock for event in events),
    }


async def archive_market_data(context: TaskContext) -> dict[str, Any]:
    quotes = await context.quote_provider.get_quotes(None)  # type: ignore[arg-type]
    events = await context.event_provider.get_events()
    quote_archive = await context.archive_service.archive_quotes(quotes)
    event_archive = await context.archive_service.archive_events(events)
    return {
        "received_quotes": len(quotes),
        "archived_quotes": quote_archive.inserted,
        "duplicate_quotes": quote_archive.duplicates,
        "received_events": len(events),
        "archived_events": event_archive.inserted,
        "duplicate_events": event_archive.duplicates,
        "mock_data_used": any(quote.provider == "mock" for quote in quotes) or any(event.is_mock for event in events),
    }


async def generate_premarket_report(context: TaskContext) -> dict[str, Any]:
    return await _generate_report(context, ReportType.premarket)


async def generate_intraday_report(context: TaskContext) -> dict[str, Any]:
    return await _generate_report(context, ReportType.intraday)


async def generate_close_report(context: TaskContext) -> dict[str, Any]:
    return await _generate_report(context, ReportType.close)


async def evaluate_alerts(context: TaskContext) -> dict[str, Any]:
    symbols = [item.symbol for item in await context.watchlist_repository.list_symbols()]
    result = await context.alert_service.evaluate(
        AlertEvaluationRequest(symbols=symbols[:20], include_quotes=True, include_events=True)
    )
    return result.model_dump(mode="json")


async def _generate_report(context: TaskContext, report_type: ReportType) -> dict[str, Any]:
    quotes = await context.quote_provider.get_quotes(None)  # type: ignore[arg-type]
    events = await context.event_provider.get_events()
    if report_type == ReportType.premarket:
        report = build_premarket_report(quotes, events, datetime.now(UTC))
    elif report_type == ReportType.close:
        report = build_close_report(quotes, events, datetime.now(UTC))
    else:
        report = build_intraday_report(quotes, events, datetime.now(UTC))
    archive = await context.archive_service.archive_report(report)
    return {
        "report_type": report.report_type.value,
        "report_date": report.generated_at.date().isoformat(),
        "archived": archive.inserted,
        "duplicate": archive.duplicates,
        "failed": archive.failed,
        "is_mock": report.is_mock,
    }
