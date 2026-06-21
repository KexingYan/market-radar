from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EventType(StrEnum):
    breaking_news = "breaking_news"
    company_announcement = "company_announcement"
    earnings = "earnings"
    guidance = "guidance"
    macro_event = "macro_event"
    price_spike = "price_spike"
    volume_spike = "volume_spike"
    regulatory_filing = "regulatory_filing"
    dividend = "dividend"
    share_buyback = "share_buyback"
    management_change = "management_change"


class Sentiment(StrEnum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class MarketEvent(BaseModel):
    id: str
    event_type: EventType
    title: str
    summary: str
    source_name: str
    source_url: str
    published_at: datetime
    received_at: datetime
    affected_symbols: list[str]
    importance_score: int = Field(ge=0, le=100)
    reliability_score: int = Field(ge=0, le=100)
    sentiment: Sentiment
    confidence: float = Field(ge=0, le=1)
    is_mock: bool
