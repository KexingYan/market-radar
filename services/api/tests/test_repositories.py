from datetime import UTC, datetime

import pytest

from app.domain.market_event import EventType, MarketEvent, Sentiment
from app.domain.quote import QuoteSnapshot
from app.domain.watchlist import WatchlistItem
from app.repositories.memory import create_memory_repositories
from app.reports.engine import build_close_report


@pytest.mark.asyncio
async def test_sqlite_memory_initializes_and_saves_quotes() -> None:
    repos = create_memory_repositories()
    quote = _quote("AAPL")

    result = await repos["quotes"].save_snapshots([quote])
    duplicate = await repos["quotes"].save_snapshots([quote])
    history = await repos["quotes"].get_history("AAPL")

    assert result.inserted == 1
    assert duplicate.duplicates == 1
    assert history[0].symbol == "AAPL"


@pytest.mark.asyncio
async def test_event_save_deduplicates_and_preserves_symbols() -> None:
    repos = create_memory_repositories()
    event = _event("event-1")

    result = await repos["events"].save_events([event])
    duplicate = await repos["events"].save_events([event])
    stored = await repos["events"].get_event("event-1")

    assert result.inserted == 1
    assert duplicate.duplicates == 1
    assert stored is not None
    assert stored.affected_symbols == ["AAPL", "MSFT"]


@pytest.mark.asyncio
async def test_report_save_is_idempotent() -> None:
    repos = create_memory_repositories()
    report = build_close_report([_quote("AAPL")], [_event("event-1")], datetime(2024, 1, 15, tzinfo=UTC))

    result = await repos["reports"].save_report(report)
    duplicate = await repos["reports"].save_report(report)
    reports = await repos["reports"].list_reports()

    assert result.inserted == 1
    assert duplicate.duplicates == 1
    assert len(reports) == 1


@pytest.mark.asyncio
async def test_watchlist_add_duplicate_delete_and_history_is_preserved() -> None:
    repos = create_memory_repositories()
    item = WatchlistItem(symbol="AAPL", display_name="Apple", market="US")
    await repos["quotes"].save_snapshots([_quote("AAPL")])

    added = await repos["watchlist"].add_symbol(item)
    with pytest.raises(ValueError):
        await repos["watchlist"].add_symbol(item)
    removed = await repos["watchlist"].remove_symbol("AAPL")
    history = await repos["quotes"].get_history("AAPL")

    assert added.symbol == "AAPL"
    assert removed is True
    assert history


@pytest.mark.asyncio
async def test_watchlist_limit_is_one_hundred() -> None:
    repos = create_memory_repositories()
    for index in range(100):
        await repos["watchlist"].add_symbol(
            WatchlistItem(symbol=f"A{index}", display_name=f"Item {index}", market="US")
        )

    with pytest.raises(ValueError):
        await repos["watchlist"].add_symbol(WatchlistItem(symbol="B100", display_name="Overflow", market="US"))


def test_storage_status_does_not_expose_path() -> None:
    repos = create_memory_repositories()
    status = repos["metrics"].status()

    assert status["database_location_type"] == "project_runtime"
    assert "path" not in status


def _quote(symbol: str) -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol=symbol,
        display_name=f"{symbol} Mock",
        market="US",
        currency="USD",
        provider="mock",
        price="101.00",
        previous_close="100.00",
        change="1.00",
        change_percent="1.00",
        volume=100,
        average_volume_20d=100,
        market_status="mock_closed",
        timestamp="2024-01-15T21:00:00Z",
        is_delayed=True,
    )


def _event(event_id: str) -> MarketEvent:
    return MarketEvent(
        id=event_id,
        event_type=EventType.company_announcement,
        title="演示事件：本地归档测试",
        summary="Mock event",
        source_name="Mock Data Provider",
        source_url="mock://event",
        published_at="2024-01-15T10:00:00Z",
        received_at="2024-01-15T10:00:00Z",
        affected_symbols=["AAPL", "MSFT"],
        importance_score=80,
        reliability_score=100,
        sentiment=Sentiment.neutral,
        confidence=1.0,
        is_mock=True,
    )
