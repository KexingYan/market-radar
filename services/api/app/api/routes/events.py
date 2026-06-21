from fastapi import APIRouter, HTTPException, Query

from app.domain.market_event import MarketEvent
from app.providers.registry import event_provider

router = APIRouter(prefix="/api/v1/events", tags=["events"])
provider = event_provider


@router.get("")
async def list_events(
    symbols: str | None = Query(default=None),
    minimum_importance: int | None = Query(default=None, ge=0, le=100),
) -> list[MarketEvent]:
    requested = [item.strip() for item in symbols.split(",") if item.strip()] if symbols else None
    return await provider.get_events(symbols=requested, minimum_importance=minimum_importance)


@router.get("/{event_id}")
async def get_event(event_id: str) -> MarketEvent:
    events = await provider.get_events()
    event = next((item for item in events if item.id == event_id), None)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
