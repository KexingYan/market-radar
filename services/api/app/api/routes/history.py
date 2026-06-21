from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot
from app.domain.report import MarketReport, ReportType
from app.repositories import event_repository, quote_repository, report_repository
from app.repositories.sqlite import SUPPORTED_SYMBOL_RE

router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("/quotes/{symbol}")
async def quote_history(
    symbol: str,
    limit: int = Query(default=100, ge=1, le=500),
    before: datetime | None = None,
    after: datetime | None = None,
) -> list[QuoteSnapshot]:
    _validate_symbol_or_422(symbol)
    return await quote_repository.get_history(symbol=symbol.upper(), limit=limit, before=before, after=after)


@router.get("/events")
async def event_history(
    symbol: str | None = None,
    event_type: str | None = None,
    minimum_importance: int | None = Query(default=None, ge=0, le=100),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[MarketEvent]:
    if symbol:
        _validate_symbol_or_422(symbol)
    return await event_repository.list_events(
        symbol=symbol.upper() if symbol else None,
        event_type=event_type,
        minimum_importance=minimum_importance,
        limit=limit,
    )


@router.get("/events/{event_id}")
async def event_detail(event_id: str) -> MarketEvent:
    event = await event_repository.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/reports")
async def report_history(
    report_type: ReportType | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[MarketReport]:
    return await report_repository.list_reports(
        report_type=report_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@router.get("/reports/{report_id}")
async def report_detail(report_id: str) -> MarketReport:
    report = await report_repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def _validate_symbol_or_422(symbol: str) -> None:
    if not SUPPORTED_SYMBOL_RE.fullmatch(symbol.upper()):
        raise HTTPException(status_code=422, detail="Invalid symbol")
