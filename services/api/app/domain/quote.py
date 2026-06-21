from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class QuoteSnapshot(BaseModel):
    symbol: str
    display_name: str
    market: str
    currency: str
    provider: str = "mock"
    price: Decimal
    previous_close: Decimal
    change: Decimal
    change_percent: Decimal
    volume: int = Field(ge=0)
    average_volume_20d: int = Field(ge=0)
    market_status: str
    timestamp: datetime
    is_delayed: bool
