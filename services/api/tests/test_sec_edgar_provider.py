import pytest
import httpx

from app.providers.base import ProviderReason, ProviderUnavailableError
from app.providers.fallback import EventFallbackProvider
from app.providers.mock import MockMarketDataProvider
from app.providers.sec_edgar import SecEdgarEventProvider


TICKERS = {
    "0": {
        "cik_str": 320193,
        "ticker": "AAPL",
        "title": "Apple Inc.",
    }
}

SUBMISSIONS = {
    "filings": {
        "recent": {
            "form": ["8-K", "4"],
            "filingDate": ["2024-01-15", "2024-01-16"],
            "accessionNumber": ["0000320193-24-000001", "0000320193-24-000002"],
            "primaryDocument": ["aapl-20240115.htm", ""],
        }
    }
}


@pytest.mark.asyncio
async def test_missing_user_agent_does_not_send_request() -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = SecEdgarEventProvider(user_agent=None, client=client)
        with pytest.raises(ProviderUnavailableError) as exc:
            await provider.get_events(symbols=["AAPL"])

    assert exc.value.reason == ProviderReason.missing_user_agent
    assert called is False


@pytest.mark.asyncio
async def test_missing_user_agent_falls_back_to_mock() -> None:
    provider = EventFallbackProvider(
        configured="sec",
        primary=SecEdgarEventProvider(user_agent=None),
        fallback=MockMarketDataProvider(),
    )

    events = await provider.get_events(symbols=["AAPL"])

    assert events
    assert all(event.is_mock for event in events)
    assert provider.last_status.active == "mock"
    assert provider.last_status.reason == ProviderReason.missing_user_agent


@pytest.mark.asyncio
async def test_user_agent_is_sent_to_mock_transport() -> None:
    seen_user_agents: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_user_agents.append(request.headers["User-Agent"])
        if request.url.host == "www.sec.gov":
            return httpx.Response(200, json=TICKERS, request=request)
        return httpx.Response(200, json=SUBMISSIONS, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = SecEdgarEventProvider("MarketRadar/0.1 offline-test-agent", client=client)
        await provider.get_events(symbols=["AAPL"])

    assert seen_user_agents
    assert set(seen_user_agents) == {"MarketRadar/0.1 offline-test-agent"}


def test_only_sec_official_domains_are_allowed() -> None:
    with pytest.raises(ProviderUnavailableError):
        SecEdgarEventProvider("ua")._validate_url("https://example.com/data.json")
    with pytest.raises(ProviderUnavailableError):
        SecEdgarEventProvider("ua")._validate_url("http://www.sec.gov/files/company_tickers.json")


def test_ticker_to_cik_mapping() -> None:
    mapping = SecEdgarEventProvider("ua").parse_ticker_mapping(TICKERS)

    assert mapping["AAPL"]["cik_str"] == 320193


def test_8k_conversion_to_regulatory_filing() -> None:
    provider = SecEdgarEventProvider("ua")
    event = provider.submissions_to_events(
        "AAPL",
        TICKERS["0"],
        SUBMISSIONS,
        forms={"8-K"},
    )[0]

    assert event.event_type == "regulatory_filing"
    assert event.source_name == "SEC EDGAR"
    assert event.is_mock is False
    assert event.reliability_score == 100
    assert event.sentiment == "neutral"
    assert event.confidence == 1.0
    assert event.importance_score == 85


def test_sec_rate_limit_configuration() -> None:
    provider = SecEdgarEventProvider("ua")

    assert provider._request_interval_seconds >= 0.5


@pytest.mark.asyncio
async def test_429_retries_once() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, request=request)
        return httpx.Response(200, json=TICKERS, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = SecEdgarEventProvider("ua", client=client, request_interval_seconds=0)
        mapping = await provider.get_ticker_mapping()

    assert calls == 2
    assert "AAPL" in mapping


@pytest.mark.asyncio
async def test_non_us_symbols_do_not_send_submissions_request() -> None:
    seen_hosts: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_hosts.append(request.url.host)
        return httpx.Response(200, json=TICKERS, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = SecEdgarEventProvider("ua", client=client)
        events = await provider.get_events(symbols=["0700.HK", "000001.SZ"])

    assert events == []
    assert seen_hosts == ["www.sec.gov"]


def test_accession_link_generation_and_missing_document_fallback() -> None:
    provider = SecEdgarEventProvider("ua")
    events = provider.submissions_to_events(
        "AAPL",
        TICKERS["0"],
        SUBMISSIONS,
        forms={"8-K", "4"},
    )

    assert events[0].source_url == "https://www.sec.gov/Archives/edgar/data/320193/000032019324000001/aapl-20240115.htm"
    assert events[1].source_url == "https://www.sec.gov/Archives/edgar/data/320193/000032019324000002/"
