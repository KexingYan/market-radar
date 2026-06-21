from typing import Any, Protocol

from app.providers.base import ProviderReason, ProviderUnavailableError
from app.providers.moomoo_runtime import MoomooRuntimeIsolationError, configure_moomoo_runtime


class MoomooQuoteContext(Protocol):
    def get_market_snapshot(self, symbols: list[str]) -> tuple[int, Any]:
        ...

    def close(self) -> None:
        ...


class MoomooSDKAdapter(Protocol):
    def open_quote_context(self, host: str, port: int) -> MoomooQuoteContext:
        ...


class RealMoomooSDKAdapter:
    def open_quote_context(self, host: str, port: int) -> MoomooQuoteContext:
        if host != "127.0.0.1" or port != 11111:
            raise ProviderUnavailableError(ProviderReason.opend_unavailable)
        try:
            configure_moomoo_runtime()
        except (MoomooRuntimeIsolationError, OSError) as exc:
            raise ProviderUnavailableError(ProviderReason.sdk_runtime_isolation_failed) from exc
        try:
            from moomoo import OpenQuoteContext  # type: ignore
        except ImportError as exc:
            raise ProviderUnavailableError(ProviderReason.sdk_missing) from exc
        except (PermissionError, OSError) as exc:
            raise ProviderUnavailableError(ProviderReason.sdk_logging_blocked) from exc
        return OpenQuoteContext(host=host, port=port)


class MoomooReturnCode:
    ok = 0
