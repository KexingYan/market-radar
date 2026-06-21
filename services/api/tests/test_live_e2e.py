from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api.routes.live as live_route
from app.alerts.service import AlertService
from app.domain.market_event import EventType, MarketEvent, Sentiment
from app.domain.quote import QuoteSnapshot
from app.domain.watchlist import WatchlistItem
from app.live_e2e import LIVE_E2E_SYMBOL, LiveAaplE2EService
from app.main import app
from app.providers.base import ProviderReason, ProviderUnavailableError
from app.repositories.memory import create_memory_repositories
from app.services.archive import ArchiveService


class FakeMoomooProvider:
    def __init__(self, error: bool = False) -> None:
        self.error = error
        self.calls: list[list[str] | None] = []

    async def get_quotes(self, symbols: list[str] | None = None) -> list[QuoteSnapshot]:
        self.calls.append(symbols)
        if self.error:
            raise ProviderUnavailableError(ProviderReason.opend_unavailable)
        assert symbols is not None
        return [
            QuoteSnapshot(
                symbol=symbol,
                display_name=f"{symbol} Inc.",
                market="US",
                currency="USD",
                provider="moomoo",
                price=Decimal("123.45"),
                previous_close=Decimal("120.00"),
                change=Decimal("3.45"),
                change_percent=Decimal("2.875"),
                volume=100,
                average_volume_20d=100,
                market_status="snapshot",
                timestamp=datetime(2026, 6, 21, tzinfo=UTC),
                is_delayed=True,
            )
            for symbol in symbols
        ]


class FakeSecProvider:
    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent

    async def get_ticker_mapping(self) -> dict[str, dict[str, Any]]:
        return {
            "AAPL": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
            "NVDA": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA Corp."},
            "MSFT": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp."},
            "TSLA": {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla Inc."},
            "AMD": {"cik_str": 2488, "ticker": "AMD", "title": "Advanced Micro Devices Inc."},
            "GOOG": {"cik_str": 1652044, "ticker": "GOOG", "title": "Alphabet Inc."},
        }

    async def get_company_submissions(self, cik: str) -> dict[str, Any]:
        return {"filings": {"recent": {"form": ["8-K"], "filingDate": ["2026-06-20"], "accessionNumber": ["0000320193-26-000001"], "primaryDocument": ["aapl-8k.htm"]}}}

    def submissions_to_events(self, symbol: str, company: dict[str, Any], submissions: dict[str, Any], forms: set[str]):
        return [
            MarketEvent(
                id="sec-AAPL-test",
                event_type=EventType.regulatory_filing,
                title="Apple Inc. submitted Form 8-K",
                summary="Apple Inc. submitted Form 8-K.",
                source_name="SEC EDGAR",
                source_url="https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/aapl-8k.htm",
                published_at=datetime(2026, 6, 20, tzinfo=UTC),
                received_at=datetime(2026, 6, 20, tzinfo=UTC),
                affected_symbols=["AAPL"],
                importance_score=85,
                reliability_score=100,
                sentiment=Sentiment.neutral,
                confidence=1.0,
                is_mock=False,
            )
        ]


def _service(moomoo_provider: FakeMoomooProvider | None = None) -> LiveAaplE2EService:
    repos = create_memory_repositories()
    archive = ArchiveService(repos["quotes"], repos["events"], repos["reports"])

    def alert_factory(quote_provider, event_provider):
        return AlertService(
            rule_repository=repos["alert_rules"],
            alert_repository=repos["alerts"],
            watchlist_repository=repos["watchlist"],
            quote_provider=quote_provider,
            event_provider=event_provider,
        )

    return LiveAaplE2EService(
        archive_service=archive,
        alert_service_factory=alert_factory,
        job_run_repository=repos["job_runs"],
        sec_provider_factory=lambda user_agent: FakeSecProvider(user_agent),
        quote_provider_factory=lambda: moomoo_provider or FakeMoomooProvider(),
    )


@pytest.mark.asyncio
async def test_live_e2e_service_redacts_real_payload_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "MarketRadar/0.1 contact@example.test")
    result = await _service().run()
    text = str(result.model_dump(mode="json")).lower()

    assert result.symbol == LIVE_E2E_SYMBOL
    assert result.sec.request_count == 2
    assert result.sec.success is True
    assert result.moomoo.success is True
    assert result.moomoo.snapshot_rows == 1
    assert result.moomoo.quote_context_closed is True
    assert result.quote_archive.inserted == 1
    assert result.event_archive.inserted == 1
    assert result.report.generated is True
    assert result.job_run.saved is True
    assert "123.45" not in text
    assert "contact@example.test" not in text
    assert "user-agent" not in text
    assert "account" not in text


@pytest.mark.asyncio
async def test_live_e2e_moomoo_unavailable_falls_back_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "MarketRadar/0.1 contact@example.test")
    result = await _service(FakeMoomooProvider(error=True)).run()

    assert result.moomoo.attempted is True
    assert result.moomoo.success is False
    assert result.moomoo.snapshot_rows == 0
    assert result.moomoo.fallback_used is True


@pytest.mark.asyncio
async def test_watchlist_refresh_empty_watchlist_falls_back_to_aapl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "MarketRadar/0.1 contact@example.test")

    result = await _service().run_watchlist_refresh([])

    assert result.symbols == ["AAPL"]
    assert result.fallback_symbol_used is True
    assert result.moomoo.snapshot_rows == 1
    assert result.sec.request_count == 2


@pytest.mark.asyncio
async def test_watchlist_refresh_uses_maximum_five_supported_symbols(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "MarketRadar/0.1 contact@example.test")
    watchlist = [
        WatchlistItem(symbol="AAPL", display_name="Apple", market="US"),
        WatchlistItem(symbol="NVDA", display_name="NVIDIA", market="US"),
        WatchlistItem(symbol="0700.HK", display_name="Unsupported", market="HK"),
        WatchlistItem(symbol="MSFT", display_name="Microsoft", market="US"),
        WatchlistItem(symbol="TSLA", display_name="Tesla", market="US"),
        WatchlistItem(symbol="AMD", display_name="AMD", market="US"),
        WatchlistItem(symbol="GOOG", display_name="Alphabet", market="US"),
    ]

    result = await _service().run_watchlist_refresh(watchlist)

    assert result.symbols == ["AAPL", "NVDA", "MSFT", "TSLA", "AMD"]
    assert result.fallback_symbol_used is False
    assert result.moomoo.snapshot_rows == 5
    assert result.sec.request_count <= 6
    assert result.sec.request_count <= 8


def test_live_endpoint_has_no_symbol_parameter_and_redacts(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        async def run(self):
            return (await _service().run()).model_copy(update={"symbol": "AAPL"})

    monkeypatch.setenv("SEC_USER_AGENT", "MarketRadar/0.1 contact@example.test")
    monkeypatch.setattr(live_route, "service", FakeService())
    response = TestClient(app).post("/api/v1/live/aapl-e2e", json={"symbol": "MSFT"})

    assert response.status_code == 200
    payload = response.json()
    text = str(payload).lower()
    assert payload["symbol"] == "AAPL"
    assert "price" not in text
    assert "email" not in text
    assert "user_agent" not in text
    assert "account" not in text


def test_watchlist_refresh_endpoint_does_not_accept_external_symbols_and_redacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeService:
        async def run_watchlist_refresh(self, watchlist):
            return await _service().run_watchlist_refresh([])

    monkeypatch.setenv("SEC_USER_AGENT", "MarketRadar/0.1 contact@example.test")
    monkeypatch.setattr(live_route, "service", FakeService())
    response = TestClient(app).post("/api/v1/live/watchlist-refresh", json={"symbols": ["MSFT"]})

    assert response.status_code == 200
    payload = response.json()
    text = str(payload).lower()
    assert payload["symbols"] == ["AAPL"]
    assert "price" not in text
    assert "email" not in text
    assert "user_agent" not in text
    assert "account" not in text
    assert "holdings" not in text
    assert "assets" not in text
    assert "orders" not in text
