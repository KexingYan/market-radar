import asyncio
import builtins
import os
import sys
from pathlib import Path

import pytest

from app.providers.base import ProviderReason, ProviderUnavailableError
from app.providers.fallback import QuoteFallbackProvider
from app.providers.mock import MockMarketDataProvider
import app.providers.moomoo_adapter as moomoo_adapter_module
from app.providers.moomoo_adapter import MoomooSDKAdapter
from app.providers.moomoo_quotes import MoomooQuoteProvider
from app.providers.moomoo_runtime import MoomooRuntimeIsolationError, configure_moomoo_runtime
from app.providers.registry import quote_provider


class FakeQuoteContext:
    def __init__(self, payload=None, result_code: int = 0, error: Exception | None = None) -> None:
        self.payload = payload or [
            {
                "code": "US.AAPL",
                "name": "Apple Inc.",
                "last_price": "190.50",
                "prev_close_price": "188.00",
                "volume": 123,
                "average_volume_20d": 456,
            }
        ]
        self.result_code = result_code
        self.error = error
        self.closed = False

    def get_market_snapshot(self, symbols: list[str]):
        if self.error:
            raise self.error
        return self.result_code, self.payload

    def close(self) -> None:
        self.closed = True


class FakeMoomooSDKAdapter(MoomooSDKAdapter):
    def __init__(self, context: FakeQuoteContext | None = None, error: ProviderUnavailableError | None = None) -> None:
        self.context = context or FakeQuoteContext()
        self.error = error
        self.open_calls = 0
        self.last_host: str | None = None
        self.last_port: int | None = None

    def open_quote_context(self, host: str, port: int) -> FakeQuoteContext:
        self.open_calls += 1
        self.last_host = host
        self.last_port = port
        if self.error:
            raise self.error
        return self.context


def test_host_and_port_are_fixed() -> None:
    provider = MoomooQuoteProvider(adapter=FakeMoomooSDKAdapter())

    assert provider.host == "127.0.0.1"
    assert provider.port == 11111


def test_symbol_mapping_and_unsupported_symbols() -> None:
    assert MoomooQuoteProvider.to_moomoo_symbol("AAPL") == "US.AAPL"
    assert MoomooQuoteProvider.to_moomoo_symbol("NVDA") == "US.NVDA"
    with pytest.raises(ProviderUnavailableError):
        MoomooQuoteProvider.to_moomoo_symbol("0700.HK")
    with pytest.raises(ProviderUnavailableError):
        MoomooQuoteProvider.to_moomoo_symbol("000001.SZ")


@pytest.mark.asyncio
async def test_maximum_twenty_symbols() -> None:
    provider = MoomooQuoteProvider(adapter=FakeMoomooSDKAdapter())

    with pytest.raises(ProviderUnavailableError):
        await provider.get_quotes([f"A{i}" for i in range(21)])


@pytest.mark.asyncio
async def test_success_closes_context_and_returns_moomoo_quote() -> None:
    context = FakeQuoteContext()
    adapter = FakeMoomooSDKAdapter(context=context)
    provider = MoomooQuoteProvider(adapter=adapter, request_interval_seconds=0)

    quotes = await provider.get_quotes(["AAPL"])

    assert adapter.last_host == "127.0.0.1"
    assert adapter.last_port == 11111
    assert context.closed is True
    assert quotes[0].symbol == "AAPL"
    assert quotes[0].provider == "moomoo"


@pytest.mark.asyncio
async def test_exception_closes_context() -> None:
    context = FakeQuoteContext(error=ProviderUnavailableError(ProviderReason.invalid_response))
    provider = MoomooQuoteProvider(adapter=FakeMoomooSDKAdapter(context=context), request_interval_seconds=0)

    with pytest.raises(ProviderUnavailableError):
        await provider.get_quotes(["AAPL"])

    assert context.closed is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason",
    [
        ProviderReason.sdk_missing,
        ProviderReason.opend_unavailable,
        ProviderReason.opend_not_logged_in,
        ProviderReason.quote_permission_unavailable,
        ProviderReason.timeout,
        ProviderReason.invalid_response,
        ProviderReason.sdk_runtime_isolation_failed,
        ProviderReason.sdk_logging_blocked,
    ],
)
async def test_fallback_reasons_return_mock(reason: ProviderReason) -> None:
    adapter = FakeMoomooSDKAdapter(error=ProviderUnavailableError(reason))
    primary = MoomooQuoteProvider(adapter=adapter, request_interval_seconds=0)
    fallback = QuoteFallbackProvider(configured="moomoo", primary=primary, fallback=MockMarketDataProvider())

    quotes = await fallback.get_quotes(["AAPL"])

    assert quotes[0].provider == "mock"
    assert fallback.last_status.active == "mock"
    assert fallback.last_status.reason == reason


@pytest.mark.asyncio
async def test_invalid_response_falls_back_to_mock() -> None:
    context = FakeQuoteContext(payload={"bad": "shape"})
    fallback = QuoteFallbackProvider(
        configured="moomoo",
        primary=MoomooQuoteProvider(adapter=FakeMoomooSDKAdapter(context=context), request_interval_seconds=0),
        fallback=MockMarketDataProvider(),
    )

    quotes = await fallback.get_quotes(["AAPL"])

    assert quotes[0].provider == "mock"
    assert fallback.last_status.reason == ProviderReason.invalid_response


@pytest.mark.asyncio
async def test_timeout_falls_back_to_mock() -> None:
    context = FakeQuoteContext(error=TimeoutError())
    fallback = QuoteFallbackProvider(
        configured="moomoo",
        primary=MoomooQuoteProvider(adapter=FakeMoomooSDKAdapter(context=context), request_interval_seconds=0),
        fallback=MockMarketDataProvider(),
    )

    quotes = await fallback.get_quotes(["AAPL"])

    assert quotes[0].provider == "mock"
    assert fallback.last_status.reason == ProviderReason.timeout


def test_default_mock_configuration_does_not_instantiate_context() -> None:
    assert quote_provider.configured == "mock"
    assert quote_provider.primary is None


def test_live_validation_status_is_not_attempted() -> None:
    provider = MoomooQuoteProvider(adapter=FakeMoomooSDKAdapter())

    assert provider.last_reason == ProviderReason.live_validation_not_attempted


def test_runtime_code_has_no_trading_calls() -> None:
    app_dir = Path("services/api/app")
    forbidden = [
        "OpenSecTradeContext",
        "OpenFutureTradeContext",
        "OpenCryptoTradeContext",
        "unlock_trade",
        "place_order",
        "modify_order",
        "cancel_order",
        "get_acc_list",
        "accinfo_query",
        "position_list_query",
        "order_list_query",
        "deal_list_query",
        "history_order_list_query",
        "history_deal_list_query",
    ]

    runtime_text = "\n".join(path.read_text(encoding="utf-8") for path in app_dir.rglob("*.py"))

    for item in forbidden:
        assert item not in runtime_text


def test_no_real_connection_is_made_by_fake_adapter() -> None:
    adapter = FakeMoomooSDKAdapter()

    assert adapter.open_calls == 0


def test_configure_moomoo_runtime_uses_project_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = Path(".").resolve()
    paths = configure_moomoo_runtime(project_root)
    expected_root = (project_root / ".runtime" / "moomoo").resolve()

    for path in (paths.root, paths.logs, paths.cache, paths.tmp):
        assert path.is_relative_to(expected_root)

    assert paths.logs == expected_root / "logs"
    assert paths.cache == expected_root / "cache"
    assert paths.tmp == expected_root / "tmp"
    assert os.environ["appdata"] == str(expected_root)
    assert os.environ["APPDATA"] == str(expected_root)
    assert os.environ["HOME"] == str(expected_root)
    assert os.environ["TMP"] == str(paths.tmp)
    assert os.environ["TEMP"] == str(paths.tmp)


def test_moomoo_runtime_is_git_ignored() -> None:
    ignore_text = Path(".gitignore").read_text(encoding="utf-8")

    assert ".runtime/" in ignore_text


def test_importing_provider_modules_does_not_import_moomoo_sdk() -> None:
    assert "moomoo" not in sys.modules


def test_default_mock_configuration_does_not_import_moomoo_sdk() -> None:
    assert quote_provider.configured == "mock"
    assert "moomoo" not in sys.modules


def test_fake_adapter_tests_do_not_import_real_sdk() -> None:
    FakeMoomooSDKAdapter()

    assert "moomoo" not in sys.modules


def test_runtime_isolation_failure_does_not_import_sdk_or_open_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_runtime():
        raise MoomooRuntimeIsolationError("blocked")

    monkeypatch.setattr(moomoo_adapter_module, "configure_moomoo_runtime", fail_runtime)
    adapter = moomoo_adapter_module.RealMoomooSDKAdapter()

    with pytest.raises(ProviderUnavailableError) as exc_info:
        adapter.open_quote_context("127.0.0.1", 11111)

    assert exc_info.value.reason == ProviderReason.sdk_runtime_isolation_failed
    assert "moomoo" not in sys.modules


def test_sdk_logging_blocked_returns_safe_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "moomoo":
            raise PermissionError("blocked logging setup")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    adapter = moomoo_adapter_module.RealMoomooSDKAdapter()

    with pytest.raises(ProviderUnavailableError) as exc_info:
        adapter.open_quote_context("127.0.0.1", 11111)

    assert exc_info.value.reason == ProviderReason.sdk_logging_blocked
    assert "blocked logging setup" not in str(exc_info.value)
