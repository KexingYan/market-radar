from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain.market_event import EventType, MarketEvent, Sentiment
from app.domain.quote import QuoteSnapshot
from app.main import app
from app.reports.engine import (
    build_close_report,
    build_intraday_report,
    build_premarket_report,
    detect_market_moves,
    group_for_importance,
    sort_and_deduplicate_events,
)

client = TestClient(app)


def test_report_endpoints_return_mock_reports() -> None:
    for path, report_type in [
        ("/api/v1/reports/premarket", "premarket"),
        ("/api/v1/reports/intraday", "intraday"),
        ("/api/v1/reports/close", "close"),
    ]:
        response = client.get(path)

        assert response.status_code == 200
        payload = response.json()
        assert payload["report_type"] == report_type
        assert payload["data_source"] == "mock"
        assert payload["is_mock"] is True
        assert payload["disclaimer"] == "仅供信息展示，不构成投资建议。"
        assert "market_move_alerts" in payload
        assert "event_groups" in payload


def test_event_sort_and_dedup_keeps_highest_importance() -> None:
    low = _event("a", "Same title", 50, "2024-01-15T10:00:00+00:00")
    high = _event("b", "Same title", 80, "2024-01-15T09:00:00+00:00")
    other = _event("c", "Other title", 70, "2024-01-15T08:00:00+00:00")

    result = sort_and_deduplicate_events([low, high, other])

    assert [event.id for event in result] == ["b", "c"]


def test_importance_groups_are_deterministic() -> None:
    assert group_for_importance(90) == "critical"
    assert group_for_importance(70) == "high"
    assert group_for_importance(50) == "medium"
    assert group_for_importance(49) == "low"


def test_market_move_alerts_detect_price_and_volume_moves() -> None:
    quote = _quote(change_percent="3.50", volume=300, average_volume_20d=100)

    alerts = detect_market_moves([quote])

    assert {alert.alert_type for alert in alerts} == {"price_move", "volume_move"}
    assert all(alert.symbol == "AAPL" for alert in alerts)


def test_market_move_alerts_ignore_small_moves() -> None:
    quote = _quote(change_percent="0.50", volume=100, average_volume_20d=100)

    alerts = detect_market_moves([quote])

    assert alerts == []


def test_report_builders_do_not_generate_investment_advice() -> None:
    quotes = [_quote(change_percent="4.00", volume=300, average_volume_20d=100)]
    events = [_event("event-1", "演示事件：重大公告", 85, "2024-01-15T10:00:00+00:00")]
    generated_at = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)

    reports = [
        build_premarket_report(quotes, events, generated_at),
        build_intraday_report(quotes, events, generated_at),
        build_close_report(quotes, events, generated_at),
    ]

    forbidden = ["买入", "卖出", "目标价", "投资建议", "AI 摘要"]
    for report in reports:
        text = " ".join([report.summary, *report.key_points])
        assert report.is_mock is True
        assert not any(term in text for term in forbidden)


def _quote(change_percent: str, volume: int, average_volume_20d: int) -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol="AAPL",
        display_name="Apple Mock",
        market="US",
        currency="USD",
        provider="mock",
        price="104.00",
        previous_close="100.00",
        change="4.00",
        change_percent=change_percent,
        volume=volume,
        average_volume_20d=average_volume_20d,
        market_status="mock_closed",
        timestamp="2024-01-15T21:00:00Z",
        is_delayed=True,
    )


def _event(event_id: str, title: str, score: int, published_at: str) -> MarketEvent:
    return MarketEvent(
        id=event_id,
        event_type=EventType.company_announcement,
        title=title,
        summary="Mock event",
        source_name="Mock Data Provider",
        source_url="mock://event",
        published_at=published_at,
        received_at=published_at,
        affected_symbols=["AAPL"],
        importance_score=score,
        reliability_score=100,
        sentiment=Sentiment.neutral,
        confidence=1.0,
        is_mock=True,
    )
