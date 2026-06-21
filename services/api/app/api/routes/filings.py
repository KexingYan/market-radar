from fastapi import APIRouter, Query

from app.domain.market_event import MarketEvent
from app.providers.sec_edgar import SUPPORTED_FORMS
from app.providers.registry import event_provider

router = APIRouter(prefix="/api/v1/filings", tags=["filings"])


@router.get("")
async def list_filings(
    symbols: str = Query(default="", max_length=120),
    forms: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[MarketEvent]:
    requested_symbols = [item.strip().upper() for item in symbols.split(",") if item.strip()]
    requested_forms = [item.strip().upper() for item in forms.split(",") if item.strip()] if forms else None
    if len(requested_symbols) > 10:
        requested_symbols = requested_symbols[:10]
    if requested_forms is not None:
        requested_forms = [form for form in requested_forms if form in SUPPORTED_FORMS]
    return await event_provider.get_events(symbols=requested_symbols, forms=requested_forms, limit=limit)
