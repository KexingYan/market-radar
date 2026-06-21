from pydantic import BaseModel


class WatchlistItem(BaseModel):
    symbol: str
    display_name: str
    market: str
    note: str = "Local watchlist item."
    is_mock: bool = True
