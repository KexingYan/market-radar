from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.market_event import EventType

SUPPORTED_SYMBOL_PATTERN = r"^[A-Z][A-Z0-9.-]{0,9}$"
MAX_SNOOZE_MINUTES = 7 * 24 * 60


class AlertRuleType(StrEnum):
    PRICE_CHANGE_ABSOLUTE = "price_change_absolute"
    VOLUME_RATIO = "volume_ratio"
    EVENT_IMPORTANCE = "event_importance"
    EVENT_TYPE = "event_type"
    PRICE_AND_VOLUME = "price_and_volume"


class AlertSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSymbolScope(StrEnum):
    WATCHLIST = "watchlist"
    ALL_AVAILABLE = "all_available"
    SPECIFIC_SYMBOLS = "specific_symbols"


class AlertStatus(StrEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    EXPIRED = "expired"


class PriceDirection(StrEnum):
    ANY = "any"
    UP = "up"
    DOWN = "down"


class StrictAlertModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class PriceChangeRuleParameters(StrictAlertModel):
    threshold_percent: float = Field(ge=0.1, le=100)
    direction: PriceDirection = PriceDirection.ANY


class VolumeRatioRuleParameters(StrictAlertModel):
    threshold_ratio: float = Field(ge=1.0, le=100)


class EventImportanceRuleParameters(StrictAlertModel):
    minimum_importance: int = Field(ge=0, le=100)


class EventTypeRuleParameters(StrictAlertModel):
    event_types: list[EventType] = Field(min_length=1, max_length=10)
    minimum_importance: int = Field(default=0, ge=0, le=100)


class PriceAndVolumeRuleParameters(StrictAlertModel):
    minimum_absolute_change_percent: float = Field(ge=0.1, le=100)
    minimum_volume_ratio: float = Field(ge=1.0, le=100)


PARAMETER_MODEL_BY_RULE_TYPE: dict[AlertRuleType, type[BaseModel]] = {
    AlertRuleType.PRICE_CHANGE_ABSOLUTE: PriceChangeRuleParameters,
    AlertRuleType.VOLUME_RATIO: VolumeRatioRuleParameters,
    AlertRuleType.EVENT_IMPORTANCE: EventImportanceRuleParameters,
    AlertRuleType.EVENT_TYPE: EventTypeRuleParameters,
    AlertRuleType.PRICE_AND_VOLUME: PriceAndVolumeRuleParameters,
}


class AlertRuleBase(StrictAlertModel):
    name: str = Field(min_length=1, max_length=80)
    rule_type: AlertRuleType
    severity: AlertSeverity
    symbol_scope: AlertSymbolScope
    symbols: list[str] = Field(default_factory=list, max_length=20)
    cooldown_seconds: int = Field(ge=60, le=604800)
    parameters: dict[str, Any]
    is_enabled: bool = True

    @field_validator("name")
    @classmethod
    def reject_markup(cls, value: str) -> str:
        if "<" in value or ">" in value:
            raise ValueError("rule name must not contain markup")
        return value.strip()

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, symbols: list[str]) -> list[str]:
        normalized = [symbol.upper() for symbol in symbols]
        for symbol in normalized:
            if not __import__("re").fullmatch(SUPPORTED_SYMBOL_PATTERN, symbol):
                raise ValueError("invalid_symbol")
        return normalized

    @model_validator(mode="after")
    def validate_scope_and_parameters(self) -> "AlertRuleBase":
        if self.symbol_scope == AlertSymbolScope.SPECIFIC_SYMBOLS and not self.symbols:
            raise ValueError("specific_symbols requires at least one symbol")
        if self.symbol_scope != AlertSymbolScope.SPECIFIC_SYMBOLS and self.symbols:
            raise ValueError("symbols are only allowed with specific_symbols scope")
        self.parameters = validate_rule_parameters(self.rule_type, self.parameters)
        return self


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(StrictAlertModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    severity: AlertSeverity | None = None
    symbol_scope: AlertSymbolScope | None = None
    symbols: list[str] | None = Field(default=None, max_length=20)
    cooldown_seconds: int | None = Field(default=None, ge=60, le=604800)
    parameters: dict[str, Any] | None = None
    is_enabled: bool | None = None

    @field_validator("name")
    @classmethod
    def reject_markup(cls, value: str | None) -> str | None:
        if value is not None and ("<" in value or ">" in value):
            raise ValueError("rule name must not contain markup")
        return value.strip() if value is not None else None

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, symbols: list[str] | None) -> list[str] | None:
        if symbols is None:
            return None
        normalized = [symbol.upper() for symbol in symbols]
        for symbol in normalized:
            if not __import__("re").fullmatch(SUPPORTED_SYMBOL_PATTERN, symbol):
                raise ValueError("invalid_symbol")
        return normalized


class AlertRule(AlertRuleBase):
    id: str
    is_system_default: bool = False
    created_at: datetime
    updated_at: datetime


class AlertCandidate(StrictAlertModel):
    rule_id: str
    alert_type: AlertRuleType
    severity: AlertSeverity
    title: str
    message: str
    symbol: str | None = None
    event_id: str | None = None
    source_timestamp: datetime | None = None
    triggered_at: datetime
    is_mock: bool
    metadata: dict[str, Any]
    deduplication_key: str


class AlertItem(StrictAlertModel):
    id: str
    rule_id: str
    alert_type: AlertRuleType
    severity: AlertSeverity
    title: str
    message: str
    symbol: str | None = None
    event_id: str | None = None
    source_timestamp: datetime | None = None
    triggered_at: datetime
    status: AlertStatus
    acknowledged_at: datetime | None = None
    snoozed_until: datetime | None = None
    is_mock: bool
    deduplication_key: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class AlertEvaluationRequest(StrictAlertModel):
    symbols: list[str] = Field(default_factory=list, max_length=20)
    include_quotes: bool = True
    include_events: bool = True

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, symbols: list[str]) -> list[str]:
        normalized = [symbol.upper() for symbol in symbols]
        for symbol in normalized:
            if not __import__("re").fullmatch(SUPPORTED_SYMBOL_PATTERN, symbol):
                raise ValueError("invalid_symbol")
        return normalized


class AlertEvaluationResult(StrictAlertModel):
    evaluated_rules: int
    evaluated_symbols: int
    created_alerts: int
    duplicate_alerts: int
    cooldown_suppressed: int
    mock_data_used: bool


class AlertSnoozeRequest(StrictAlertModel):
    duration_minutes: Literal[15, 60, 240, 1440] | None = None
    snoozed_until: datetime | None = None

    @model_validator(mode="after")
    def validate_duration(self) -> "AlertSnoozeRequest":
        if self.duration_minutes is None and self.snoozed_until is None:
            raise ValueError("duration_minutes or snoozed_until is required")
        if self.duration_minutes is not None and self.snoozed_until is not None:
            raise ValueError("provide only one snooze option")
        target = self.target_time(datetime.now(UTC))
        if target <= datetime.now(UTC):
            raise ValueError("snooze target must be in the future")
        if target > datetime.now(UTC) + timedelta(minutes=MAX_SNOOZE_MINUTES):
            raise ValueError("snooze target must be within 7 days")
        return self

    def target_time(self, now: datetime) -> datetime:
        if self.snoozed_until is not None:
            if self.snoozed_until.tzinfo is None:
                return self.snoozed_until.replace(tzinfo=UTC)
            return self.snoozed_until.astimezone(UTC)
        return now + timedelta(minutes=int(self.duration_minutes or 0))


class AlertSummary(StrictAlertModel):
    new: int
    acknowledged: int
    snoozed: int
    high_or_critical: int
    latest_triggered_at: datetime | None


def validate_rule_parameters(rule_type: AlertRuleType, parameters: dict[str, Any]) -> dict[str, Any]:
    model = PARAMETER_MODEL_BY_RULE_TYPE[rule_type]
    return model.model_validate(parameters).model_dump(mode="json")
