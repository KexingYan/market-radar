import pytest

from app.domain.quote import QuoteSnapshot
from app.live_validation import (
    is_valid_sec_user_agent,
    redacted_result_dict,
    run_moomoo_live_smoke,
    run_sec_live_smoke,
)
from app.providers.base import ProviderReason, ProviderUnavailableError


def test_sec_user_agent_validation_rejects_empty_and_sensitive_values() -> None:
    assert is_valid_sec_user_agent(None) is False
    assert is_valid_sec_user_agent("") is False
    assert is_valid_sec_user_agent("MarketRadar/0.1") is False
    assert is_valid_sec_user_agent("MarketRadar/0.1 Bearer secret user@example.test") is False
    assert is_valid_sec_user_agent("MarketRadar/0.1 contact@example.test") is True


@pytest.mark.asyncio
async def test_missing_sec_user_agent_does_not_request_sec() -> None:
    result = await run_sec_live_smoke(None)

    assert result.requested_sec is False
    assert result.request_count == 0
    assert result.fallback_used is True


@pytest.mark.asyncio
async def test_moomoo_unavailable_result_falls_back_without_sensitive_data() -> None:
    class UnavailableProvider:
        async def get_quotes(self, symbols):
            raise ProviderUnavailableError(ProviderReason.opend_unavailable)

    result = await run_moomoo_live_smoke(UnavailableProvider())  # type: ignore[arg-type]
    redacted = redacted_result_dict(result)
    text = str(redacted).lower()

    assert result.attempted_localhost_11111 is True
    assert result.snapshot_returned is False
    assert result.fallback_used is True
    assert result.output_real_price is False
    assert result.read_account is False
    assert "price" not in text or "output_real_price" in text
    assert "account_id" not in text


@pytest.mark.asyncio
async def test_moomoo_success_result_does_not_expose_price() -> None:
    class SuccessProvider:
        async def get_quotes(self, symbols):
            return [
                QuoteSnapshot(
                    symbol="AAPL",
                    display_name="Apple",
                    market="US",
                    currency="USD",
                    provider="moomoo",
                    price="1.23",
                    previous_close="1.00",
                    change="0.23",
                    change_percent="23.0",
                    volume=1,
                    average_volume_20d=1,
                    market_status="snapshot",
                    timestamp="2024-01-15T10:00:00Z",
                    is_delayed=True,
                )
            ]

    result = await run_moomoo_live_smoke(SuccessProvider())  # type: ignore[arg-type]
    text = str(redacted_result_dict(result))

    assert result.snapshot_returned is True
    assert result.output_real_price is False
    assert "1.23" not in text

