from fastapi import APIRouter, Query

from app.domain.report import MarketReport
from app.providers.registry import event_provider, quote_provider
from app.repositories import event_repository, quote_repository, report_repository
from app.reports.engine import build_close_report, build_intraday_report, build_premarket_report
from app.services.archive import ArchiveService

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
archive_service = ArchiveService(quote_repository, event_repository, report_repository)


@router.get("/premarket")
async def premarket_report(archive: bool = Query(default=True)) -> MarketReport:
    quotes = await quote_provider.get_quotes()
    events = await event_provider.get_events()
    report = build_premarket_report(quotes, events)
    if archive:
        await archive_service.archive_quotes(quotes)
        await archive_service.archive_events(events)
        await archive_service.archive_report(report)
    return report


@router.get("/intraday")
async def intraday_report(archive: bool = Query(default=True)) -> MarketReport:
    quotes = await quote_provider.get_quotes()
    events = await event_provider.get_events()
    report = build_intraday_report(quotes, events)
    if archive:
        await archive_service.archive_quotes(quotes)
        await archive_service.archive_events(events)
        await archive_service.archive_report(report)
    return report


@router.get("/close")
async def close_report(archive: bool = Query(default=True)) -> MarketReport:
    quotes = await quote_provider.get_quotes()
    events = await event_provider.get_events()
    report = build_close_report(quotes, events)
    if archive:
        await archive_service.archive_quotes(quotes)
        await archive_service.archive_events(events)
        await archive_service.archive_report(report)
    return report
