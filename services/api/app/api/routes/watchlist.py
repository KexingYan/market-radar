from fastapi import APIRouter, HTTPException

from app.domain.watchlist import WatchlistItem
from app.repositories import watchlist_repository

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


@router.get("")
async def list_watchlist() -> list[WatchlistItem]:
    return await watchlist_repository.list_symbols()


@router.post("")
async def add_watchlist_item(item: WatchlistItem) -> WatchlistItem:
    try:
        return await watchlist_repository.add_symbol(item)
    except ValueError as exc:
        reason = str(exc)
        if reason == "watchlist_symbol_exists":
            raise HTTPException(status_code=409, detail="Watchlist symbol already exists") from exc
        if reason == "watchlist_limit_reached":
            raise HTTPException(status_code=400, detail="Watchlist limit reached") from exc
        raise HTTPException(status_code=422, detail="Invalid symbol") from exc


@router.delete("/{symbol}")
async def remove_watchlist_item(symbol: str) -> dict[str, bool]:
    try:
        removed = await watchlist_repository.remove_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid symbol") from exc
    return {"removed": removed}
