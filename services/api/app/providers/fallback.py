from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot
from app.providers.base import ProviderReason, ProviderStatus, ProviderUnavailableError
from app.providers.mock import MockMarketDataProvider


class QuoteFallbackProvider:
    def __init__(
        self,
        configured: str,
        primary: object | None,
        fallback: MockMarketDataProvider,
    ) -> None:
        self.configured = configured
        self.primary = primary
        self.fallback = fallback
        self.last_status = ProviderStatus(
            configured=configured,
            active="mock",
            available=configured == "mock",
            reason=None if configured == "mock" else ProviderReason.live_validation_not_attempted,
        )

    async def get_quotes(self, symbols: list[str] | None = None) -> list[QuoteSnapshot]:
        if self.configured == "mock" or self.primary is None:
            self.last_status = ProviderStatus(configured=self.configured, active="mock", available=True)
            return await self.fallback.get_quotes(symbols)
        try:
            quotes = await self.primary.get_quotes(symbols or [])  # type: ignore[attr-defined]
            self.last_status = ProviderStatus(configured=self.configured, active=self.configured, available=True)
            return quotes
        except ProviderUnavailableError as exc:
            self.last_status = ProviderStatus(
                configured=self.configured,
                active="mock",
                available=False,
                reason=exc.reason,
            )
            return await self.fallback.get_quotes(symbols)

    async def get_quote(self, symbol: str) -> QuoteSnapshot | None:
        quotes = await self.get_quotes([symbol])
        return next((quote for quote in quotes if quote.symbol.upper() == symbol.upper()), None)


class EventFallbackProvider:
    def __init__(
        self,
        configured: str,
        primary: object | None,
        fallback: MockMarketDataProvider,
    ) -> None:
        self.configured = configured
        self.primary = primary
        self.fallback = fallback
        self.last_status = ProviderStatus(
            configured=configured,
            active="mock",
            available=configured == "mock",
            reason=None if configured == "mock" else ProviderReason.missing_user_agent,
        )

    async def get_events(
        self,
        symbols: list[str] | None = None,
        minimum_importance: int | None = None,
        forms: list[str] | None = None,
        limit: int = 50,
    ) -> list[MarketEvent]:
        if self.configured == "mock" or self.primary is None:
            self.last_status = ProviderStatus(configured=self.configured, active="mock", available=True)
            return await self.fallback.get_events(symbols=symbols, minimum_importance=minimum_importance)
        try:
            events = await self.primary.get_events(  # type: ignore[attr-defined]
                symbols=symbols,
                minimum_importance=minimum_importance,
                forms=forms,
                limit=limit,
            )
            self.last_status = ProviderStatus(configured=self.configured, active=self.configured, available=True)
            return events
        except ProviderUnavailableError as exc:
            self.last_status = ProviderStatus(
                configured=self.configured,
                active="mock",
                available=False,
                reason=exc.reason,
            )
            return await self.fallback.get_events(symbols=symbols, minimum_importance=minimum_importance)
