from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel

from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot


class ProviderReason(StrEnum):
    sdk_missing = "sdk_missing"
    opend_unavailable = "opend_unavailable"
    opend_not_logged_in = "opend_not_logged_in"
    quote_permission_unavailable = "quote_permission_unavailable"
    timeout = "timeout"
    invalid_response = "invalid_response"
    unsupported_symbol = "unsupported_symbol"
    live_validation_not_attempted = "live_validation_not_attempted"
    missing_user_agent = "missing_user_agent"
    provider_error = "provider_error"
    sdk_runtime_isolation_failed = "sdk_runtime_isolation_failed"
    sdk_logging_blocked = "sdk_logging_blocked"


class ProviderStatus(BaseModel):
    configured: str
    active: str
    available: bool
    reason: ProviderReason | None = None


class ProvidersStatusResponse(BaseModel):
    free_only_mode: bool
    quotes: ProviderStatus
    events: ProviderStatus
    trading_enabled: bool = False
    paid_data_enabled: bool = False


class ProviderUnavailableError(Exception):
    def __init__(self, reason: ProviderReason, message: str | None = None) -> None:
        self.reason = reason
        super().__init__(message or reason.value)


class MarketDataProvider(Protocol):
    async def get_quotes(self, symbols: list[str]) -> list[QuoteSnapshot]:
        ...

    async def get_quote(self, symbol: str) -> QuoteSnapshot | None:
        ...

    async def get_events(
        self,
        symbols: list[str] | None = None,
        minimum_importance: int | None = None,
    ) -> list[MarketEvent]:
        ...


class EventDataProvider(Protocol):
    async def get_events(
        self,
        symbols: list[str] | None = None,
        minimum_importance: int | None = None,
    ) -> list[MarketEvent]:
        ...
