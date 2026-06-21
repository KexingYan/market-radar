import asyncio
import re
from datetime import UTC, datetime
from decimal import Decimal
from time import monotonic
from typing import Any

from app.domain.quote import QuoteSnapshot
from app.providers.base import ProviderReason, ProviderUnavailableError
from app.providers.moomoo_adapter import MoomooSDKAdapter, RealMoomooSDKAdapter

SUPPORTED_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


class MoomooQuoteProvider:
    host = "127.0.0.1"
    port = 11111
    provider_name = "moomoo"

    def __init__(
        self,
        adapter: MoomooSDKAdapter | None = None,
        cache_ttl_seconds: float = 3,
        request_interval_seconds: float = 1,
    ) -> None:
        self._adapter = adapter or RealMoomooSDKAdapter()
        self._cache_ttl_seconds = cache_ttl_seconds
        self._request_interval_seconds = request_interval_seconds
        self._cache: dict[str, tuple[float, QuoteSnapshot]] = {}
        self._last_request_at = 0.0
        self.last_reason: ProviderReason = ProviderReason.live_validation_not_attempted

    @staticmethod
    def to_moomoo_symbol(symbol: str) -> str:
        normalized = symbol.upper()
        if not SUPPORTED_SYMBOL_RE.fullmatch(normalized):
            raise ProviderUnavailableError(ProviderReason.unsupported_symbol)
        if "." in normalized:
            raise ProviderUnavailableError(ProviderReason.unsupported_symbol)
        return f"US.{normalized}"

    async def get_quotes(self, symbols: list[str] | None = None) -> list[QuoteSnapshot]:
        requested = symbols or []
        if len(requested) > 20:
            raise ProviderUnavailableError(ProviderReason.unsupported_symbol)
        if not requested:
            return []

        now = monotonic()
        cached: list[QuoteSnapshot] = []
        missing: list[str] = []
        for symbol in requested:
            normalized = symbol.upper()
            cache_item = self._cache.get(normalized)
            if cache_item and now - cache_item[0] <= self._cache_ttl_seconds:
                cached.append(cache_item[1])
            else:
                missing.append(normalized)

        if missing:
            fetched = await self._fetch_quotes(missing)
            fetched_by_symbol = {quote.symbol: quote for quote in fetched}
            for symbol, quote in fetched_by_symbol.items():
                self._cache[symbol] = (monotonic(), quote)
            cached.extend(fetched_by_symbol.values())
        return cached

    async def get_quote(self, symbol: str) -> QuoteSnapshot | None:
        quotes = await self.get_quotes([symbol])
        return quotes[0] if quotes else None

    async def _fetch_quotes(self, symbols: list[str]) -> list[QuoteSnapshot]:
        moomoo_symbols = [self.to_moomoo_symbol(symbol) for symbol in symbols]
        elapsed = monotonic() - self._last_request_at
        if elapsed < self._request_interval_seconds:
            await asyncio.sleep(self._request_interval_seconds - elapsed)

        context = None
        try:
            context = self._adapter.open_quote_context(self.host, self.port)
            result_code, payload = await asyncio.wait_for(
                asyncio.to_thread(context.get_market_snapshot, moomoo_symbols),
                timeout=5,
            )
            self._last_request_at = monotonic()
            if result_code != 0:
                reason = self._reason_from_payload(payload)
                self.last_reason = reason
                raise ProviderUnavailableError(reason)
            quotes = self._convert_payload(payload)
            self.last_reason = ProviderReason.live_validation_not_attempted
            return quotes
        except TimeoutError as exc:
            self.last_reason = ProviderReason.timeout
            raise ProviderUnavailableError(ProviderReason.timeout) from exc
        finally:
            if context is not None:
                context.close()

    def _convert_payload(self, payload: Any) -> list[QuoteSnapshot]:
        rows: list[dict[str, Any]]
        if hasattr(payload, "to_dict"):
            rows = payload.to_dict("records")
        elif isinstance(payload, list):
            rows = payload
        else:
            raise ProviderUnavailableError(ProviderReason.invalid_response)

        quotes: list[QuoteSnapshot] = []
        for row in rows:
            symbol = str(row.get("code", "")).replace("US.", "")
            if not symbol:
                raise ProviderUnavailableError(ProviderReason.invalid_response)
            price = Decimal(str(row.get("last_price", row.get("price", "0"))))
            previous_close = Decimal(str(row.get("prev_close_price", row.get("previous_close", price))))
            change = price - previous_close
            change_percent = (change / previous_close * Decimal("100")) if previous_close else Decimal("0")
            quotes.append(
                QuoteSnapshot(
                    symbol=symbol,
                    display_name=str(row.get("name", symbol)),
                    market="US",
                    currency="USD",
                    provider=self.provider_name,
                    price=price,
                    previous_close=previous_close,
                    change=change,
                    change_percent=change_percent,
                    volume=int(row.get("volume", 0)),
                    average_volume_20d=int(row.get("average_volume_20d", 0)),
                    market_status=str(row.get("market_status", "snapshot")),
                    timestamp=datetime.now(UTC),
                    is_delayed=True,
                )
            )
        return quotes

    @staticmethod
    def _reason_from_payload(payload: Any) -> ProviderReason:
        text = str(payload).lower()
        if "login" in text:
            return ProviderReason.opend_not_logged_in
        if "permission" in text:
            return ProviderReason.quote_permission_unavailable
        if "connection" in text or "opend" in text:
            return ProviderReason.opend_unavailable
        return ProviderReason.invalid_response
