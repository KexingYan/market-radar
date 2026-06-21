from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ReportType(StrEnum):
    premarket = "premarket"
    intraday = "intraday"
    close = "close"


class EventImportanceGroup(StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class MarketMoveAlert(BaseModel):
    symbol: str
    display_name: str
    alert_type: str
    description: str
    change_percent: float
    volume_ratio: float | None = None


class EventDigestItem(BaseModel):
    id: str
    title: str
    event_type: str
    source_name: str
    affected_symbols: list[str]
    importance_score: int = Field(ge=0, le=100)
    group: EventImportanceGroup
    published_at: datetime
    is_mock: bool


class MarketReport(BaseModel):
    id: str
    report_type: ReportType
    title: str
    generated_at: datetime
    data_source: str
    summary: str
    key_points: list[str]
    event_groups: dict[EventImportanceGroup, list[EventDigestItem]]
    market_move_alerts: list[MarketMoveAlert]
    disclaimer: str = "仅供信息展示，不构成投资建议。"
    is_mock: bool
