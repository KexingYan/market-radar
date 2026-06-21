from fastapi import APIRouter, HTTPException, Query

from app.domain.quote import QuoteSnapshot
from app.providers.registry import quote_provider

router = APIRouter(prefix="/api/v1/quotes", tags=["quotes"])
provider = quote_provider


@router.get("")
async def list_quotes(symbols: str | None = Query(default=None)) -> list[QuoteSnapshot]:
    requested = [item.strip() for item in symbols.split(",") if item.strip()] if symbols else None
    return await provider.get_quotes(requested)


@router.get("/{symbol}")
async def get_quote(symbol: str) -> QuoteSnapshot:
    quote = await provider.get_quote(symbol)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote
