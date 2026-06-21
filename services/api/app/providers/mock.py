import json
from pathlib import Path
from typing import Any

from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot
from app.domain.watchlist import WatchlistItem


class MockMarketDataProvider:
    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or Path(__file__).resolve().parents[1] / "mock_data"

    async def get_quotes(self, symbols: list[str] | None = None) -> list[QuoteSnapshot]:
        quotes = [QuoteSnapshot.model_validate(item) for item in self._read_json("quotes.json")]
        if not symbols:
            return quotes
        requested = {symbol.upper() for symbol in symbols}
        return [quote for quote in quotes if quote.symbol.upper() in requested]

    async def get_quote(self, symbol: str) -> QuoteSnapshot | None:
        symbol_upper = symbol.upper()
        quotes = await self.get_quotes()
        return next((quote for quote in quotes if quote.symbol.upper() == symbol_upper), None)

    async def get_events(
        self,
        symbols: list[str] | None = None,
        minimum_importance: int | None = None,
    ) -> list[MarketEvent]:
        events = [MarketEvent.model_validate(item) for item in self._read_json("events.json")]
        if symbols:
            requested = {symbol.upper() for symbol in symbols}
            events = [
                event
                for event in events
                if requested.intersection({symbol.upper() for symbol in event.affected_symbols})
            ]
        if minimum_importance is not None:
            events = [event for event in events if event.importance_score >= minimum_importance]
        return events

    async def get_event(self, event_id: str) -> MarketEvent | None:
        events = await self.get_events()
        return next((event for event in events if event.id == event_id), None)

    async def get_watchlist(self) -> list[WatchlistItem]:
        return [WatchlistItem.model_validate(item) for item in self._read_json("watchlist.json")]

    def _read_json(self, file_name: str) -> list[dict[str, Any]]:
        path = (self._data_dir / file_name).resolve()
        data_dir = self._data_dir.resolve()
        if data_dir not in path.parents:
            raise ValueError("Mock data path must remain inside the configured data directory.")
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError(f"Expected a list in {file_name}.")
        return data
