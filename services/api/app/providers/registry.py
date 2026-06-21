from app.config import settings
from app.providers.base import ProviderStatus, ProvidersStatusResponse
from app.providers.fallback import EventFallbackProvider, QuoteFallbackProvider
from app.providers.mock import MockMarketDataProvider
from app.providers.moomoo_quotes import MoomooQuoteProvider
from app.providers.sec_edgar import SecEdgarEventProvider

mock_provider = MockMarketDataProvider()
quote_provider = QuoteFallbackProvider(
    configured=settings.market_data_provider,
    primary=MoomooQuoteProvider() if settings.market_data_provider == "moomoo" else None,
    fallback=mock_provider,
)
event_provider = EventFallbackProvider(
    configured=settings.event_data_provider,
    primary=SecEdgarEventProvider(settings.sec_user_agent) if settings.event_data_provider == "sec" else None,
    fallback=mock_provider,
)


def provider_status() -> ProvidersStatusResponse:
    return ProvidersStatusResponse(
        free_only_mode=settings.free_only_mode,
        quotes=quote_provider.last_status
        if quote_provider.last_status
        else ProviderStatus(configured=settings.market_data_provider, active="mock", available=True),
        events=event_provider.last_status
        if event_provider.last_status
        else ProviderStatus(configured=settings.event_data_provider, active="mock", available=True),
        trading_enabled=False,
        paid_data_enabled=False,
    )
