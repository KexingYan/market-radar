from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.alerts.engine import AlertEngine
from app.alerts.models import (
    AlertEvaluationRequest,
    AlertRule,
    AlertRuleCreate,
    AlertRuleType,
    AlertRuleUpdate,
    AlertSeverity,
    AlertSnoozeRequest,
    AlertStatus,
    AlertSymbolScope,
)
from app.alerts.service import AlertService
from app.domain.market_event import EventType, MarketEvent, Sentiment
from app.domain.quote import QuoteSnapshot
from app.domain.watchlist import WatchlistItem
from app.main import app
from app.providers.mock import MockMarketDataProvider
from app.repositories.memory import create_memory_repositories
from app.repositories.sqlite import alert_from_candidate

client = TestClient(app)


def test_alert_rule_parameter_validation_accepts_supported_rules() -> None:
    price = _rule_create(AlertRuleType.PRICE_CHANGE_ABSOLUTE, {"threshold_percent": 3.0, "direction": "any"})
    volume = _rule_create(AlertRuleType.VOLUME_RATIO, {"threshold_ratio": 2.0})
    event = _rule_create(AlertRuleType.EVENT_IMPORTANCE, {"minimum_importance": 80})
    event_type = _rule_create(
        AlertRuleType.EVENT_TYPE,
        {"event_types": ["regulatory_filing", "earnings"], "minimum_importance": 50},
    )
    composite = _rule_create(
        AlertRuleType.PRICE_AND_VOLUME,
        {"minimum_absolute_change_percent": 3.0, "minimum_volume_ratio": 2.0},
    )

    assert price.parameters["threshold_percent"] == 3.0
    assert volume.parameters["threshold_ratio"] == 2.0
    assert event.parameters["minimum_importance"] == 80
    assert event_type.parameters["event_types"] == ["regulatory_filing", "earnings"]
    assert composite.parameters["minimum_volume_ratio"] == 2.0


@pytest.mark.parametrize(
    ("rule_type", "parameters"),
    [
        (AlertRuleType.PRICE_CHANGE_ABSOLUTE, {"threshold_percent": -1.0, "direction": "any"}),
        (AlertRuleType.PRICE_CHANGE_ABSOLUTE, {"threshold_percent": float("nan"), "direction": "any"}),
        (AlertRuleType.VOLUME_RATIO, {"threshold_ratio": float("inf")}),
        (AlertRuleType.EVENT_IMPORTANCE, {"minimum_importance": 101}),
        (AlertRuleType.PRICE_AND_VOLUME, {"minimum_absolute_change_percent": 3.0}),
    ],
)
def test_alert_rule_parameter_validation_rejects_invalid_values(rule_type: AlertRuleType, parameters: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _rule_create(rule_type, parameters)


def test_specific_symbols_validation_limits_and_symbols() -> None:
    with pytest.raises(ValidationError):
        AlertRuleCreate(
            name="Too many",
            rule_type=AlertRuleType.VOLUME_RATIO,
            severity=AlertSeverity.MEDIUM,
            symbol_scope=AlertSymbolScope.SPECIFIC_SYMBOLS,
            symbols=[f"A{i}" for i in range(21)],
            cooldown_seconds=1800,
            parameters={"threshold_ratio": 2.0},
        )

    with pytest.raises(ValidationError):
        AlertRuleCreate(
            name="Bad symbol",
            rule_type=AlertRuleType.VOLUME_RATIO,
            severity=AlertSeverity.MEDIUM,
            symbol_scope=AlertSymbolScope.SPECIFIC_SYMBOLS,
            symbols=["AAPL;DROP TABLE alerts"],
            cooldown_seconds=1800,
            parameters={"threshold_ratio": 2.0},
        )


def test_alert_rule_rejects_unknown_fields_and_bad_cooldown() -> None:
    with pytest.raises(ValidationError):
        AlertRuleCreate(
            name="Bad",
            rule_type=AlertRuleType.VOLUME_RATIO,
            severity=AlertSeverity.MEDIUM,
            symbol_scope=AlertSymbolScope.WATCHLIST,
            cooldown_seconds=30,
            parameters={"threshold_ratio": 2.0},
            expression="volume > 1",  # type: ignore[call-arg]
        )


def test_engine_price_volume_event_and_scope_rules() -> None:
    engine = AlertEngine()
    now = datetime(2024, 1, 16, tzinfo=UTC)
    rules = [
        _rule(AlertRuleType.PRICE_CHANGE_ABSOLUTE, {"threshold_percent": 3.0, "direction": "any"}),
        _rule(AlertRuleType.VOLUME_RATIO, {"threshold_ratio": 2.0}),
        _rule(AlertRuleType.EVENT_IMPORTANCE, {"minimum_importance": 80}),
        _rule(AlertRuleType.PRICE_AND_VOLUME, {"minimum_absolute_change_percent": 3.0, "minimum_volume_ratio": 2.0}),
    ]

    candidates = engine.evaluate(
        quotes=[_quote("AAPL", change_percent=3.4, volume=300, average_volume_20d=100)],
        events=[_event("event-1", ["AAPL"], importance=85)],
        rules=rules,
        watchlist_symbols=["AAPL"],
        now=now,
    )

    assert {candidate.alert_type for candidate in candidates} == {
        AlertRuleType.PRICE_CHANGE_ABSOLUTE,
        AlertRuleType.VOLUME_RATIO,
        AlertRuleType.EVENT_IMPORTANCE,
        AlertRuleType.PRICE_AND_VOLUME,
    }
    assert all(candidate.is_mock for candidate in candidates)
    assert all("buy" not in candidate.message.lower() and "sell" not in candidate.message.lower() for candidate in candidates)


def test_engine_direction_and_zero_average_volume() -> None:
    engine = AlertEngine()
    now = datetime(2024, 1, 16, tzinfo=UTC)
    up_rule = _rule(AlertRuleType.PRICE_CHANGE_ABSOLUTE, {"threshold_percent": 3.0, "direction": "up"})
    down_rule = _rule(AlertRuleType.PRICE_CHANGE_ABSOLUTE, {"threshold_percent": 3.0, "direction": "down"})
    volume_rule = _rule(AlertRuleType.VOLUME_RATIO, {"threshold_ratio": 2.0})

    down_candidates = engine.evaluate([_quote("AAPL", change_percent=-4.0)], [], [up_rule], ["AAPL"], now)
    up_candidates = engine.evaluate([_quote("AAPL", change_percent=4.0)], [], [down_rule], ["AAPL"], now)
    volume_candidates = engine.evaluate(
        [_quote("AAPL", change_percent=0.5, volume=1000, average_volume_20d=0)],
        [],
        [volume_rule],
        ["AAPL"],
        now,
    )

    assert down_candidates == []
    assert up_candidates == []
    assert volume_candidates == []


def test_engine_event_type_filter_and_non_scope_symbol() -> None:
    engine = AlertEngine()
    rule = _rule(
        AlertRuleType.EVENT_TYPE,
        {"event_types": ["earnings"], "minimum_importance": 70},
        symbols=["AAPL"],
        scope=AlertSymbolScope.SPECIFIC_SYMBOLS,
    )

    candidates = engine.evaluate(
        [],
        [_event("event-1", ["MSFT"], EventType.earnings, 90), _event("event-2", ["AAPL"], EventType.earnings, 90)],
        [rule],
        [],
        datetime(2024, 1, 16, tzinfo=UTC),
    )

    assert len(candidates) == 1
    assert candidates[0].symbol == "AAPL"


@pytest.mark.asyncio
async def test_alert_repositories_default_rules_idempotent_and_status_counts() -> None:
    repos = create_memory_repositories()

    await repos["alert_rules"].ensure_default_rules()
    await repos["alert_rules"].ensure_default_rules()
    rules = await repos["alert_rules"].list_rules()
    status = repos["metrics"].status()

    assert len(rules) == 4
    assert status["alert_rules_count"] == 4
    assert status["enabled_alert_rules_count"] == 4


@pytest.mark.asyncio
async def test_alert_repository_save_dedupe_acknowledge_and_snooze() -> None:
    repos = create_memory_repositories()
    await repos["alert_rules"].ensure_default_rules()
    rule = (await repos["alert_rules"].list_rules())[0]
    candidate = AlertEngine().evaluate(
        [_quote("AAPL", change_percent=3.5)],
        [],
        [rule],
        ["AAPL"],
        datetime(2024, 1, 16, tzinfo=UTC),
    )[0]
    alert = alert_from_candidate(candidate)

    first = await repos["alerts"].save_alerts([alert])
    duplicate = await repos["alerts"].save_alerts([alert])
    acknowledged = await repos["alerts"].acknowledge(alert.id, datetime(2024, 1, 16, 1, tzinfo=UTC))
    snoozed = await repos["alerts"].snooze(alert.id, datetime.now(UTC) + timedelta(minutes=15))

    assert first.inserted == 1
    assert duplicate.duplicates == 1
    assert acknowledged is not None and acknowledged.status == AlertStatus.ACKNOWLEDGED
    assert snoozed is not None and snoozed.status == AlertStatus.SNOOZED


@pytest.mark.asyncio
async def test_alert_service_deduplication_and_cooldown_persist_in_repository() -> None:
    repos = create_memory_repositories()
    service = AlertService(
        rule_repository=repos["alert_rules"],
        alert_repository=repos["alerts"],
        watchlist_repository=repos["watchlist"],
        quote_provider=MockMarketDataProvider(),
        event_provider=MockMarketDataProvider(),
    )
    await repos["watchlist"].add_symbol(WatchlistItem(symbol="AAPL", display_name="Apple", market="US"))

    first = await service.evaluate(AlertEvaluationRequest(symbols=["AAPL"], include_quotes=True, include_events=True))
    second = await service.evaluate(AlertEvaluationRequest(symbols=["AAPL"], include_quotes=True, include_events=True))

    assert first.evaluated_rules == 4
    assert first.created_alerts >= 1
    assert second.cooldown_suppressed >= 1 or second.duplicate_alerts >= 1


def test_alert_api_rules_evaluate_list_acknowledge_and_snooze() -> None:
    rules = client.get("/api/v1/alert-rules")
    assert rules.status_code == 200
    assert len(rules.json()) >= 4

    created_rule = client.post(
        "/api/v1/alert-rules",
        json={
            "name": f"API price alert {datetime.now(UTC).timestamp()}",
            "rule_type": "price_change_absolute",
            "severity": "high",
            "symbol_scope": "specific_symbols",
            "symbols": ["AAPL"],
            "cooldown_seconds": 1800,
            "parameters": {"threshold_percent": 0.5, "direction": "any"},
        },
    )
    assert created_rule.status_code == 201

    patched = client.patch(created_rule.json()["id"], json={})
    assert patched.status_code == 404

    updated = client.patch(f"/api/v1/alert-rules/{created_rule.json()['id']}", json={"is_enabled": True})
    assert updated.status_code == 200

    evaluated = client.post("/api/v1/alerts/evaluate", json={"symbols": ["AAPL"], "include_quotes": True, "include_events": True})
    listed = client.get("/api/v1/alerts?limit=10&include_snoozed=true")
    summary = client.get("/api/v1/alerts/summary")

    assert evaluated.status_code == 200
    assert listed.status_code == 200
    assert summary.status_code == 200
    if listed.json():
        alert_id = listed.json()[0]["id"]
        assert client.get(f"/api/v1/alerts/{alert_id}").status_code == 200
        assert client.post(f"/api/v1/alerts/{alert_id}/acknowledge").status_code == 200
        assert client.post(f"/api/v1/alerts/{alert_id}/snooze", json={"duration_minutes": 15}).status_code == 200


def test_alert_api_rejects_bad_inputs_and_sensitive_fields() -> None:
    bad_rule = client.post(
        "/api/v1/alert-rules",
        json={
            "name": "<script>alert(1)</script>",
            "rule_type": "price_change_absolute",
            "severity": "high",
            "symbol_scope": "specific_symbols",
            "symbols": ["AAPL"],
            "cooldown_seconds": 1800,
            "parameters": {"threshold_percent": 3.0, "direction": "any"},
        },
    )
    bad_eval = client.post("/api/v1/alerts/evaluate", json={"symbols": ["AAPL;DROP TABLE alerts"]})
    high_limit = client.get("/api/v1/alerts?limit=999")
    storage = client.get("/api/v1/storage/status")

    assert bad_rule.status_code == 422
    assert bad_eval.status_code == 422
    assert high_limit.status_code == 422
    assert "alert_rules_count" in storage.json()
    text = storage.text.lower()
    assert "password" not in text
    assert "token" not in text
    assert "api_key" not in text


def test_snooze_request_rejects_past_and_too_far_targets() -> None:
    with pytest.raises(ValidationError):
        AlertSnoozeRequest(snoozed_until=datetime.now(UTC) - timedelta(minutes=1))
    with pytest.raises(ValidationError):
        AlertSnoozeRequest(snoozed_until=datetime.now(UTC) + timedelta(days=8))


def test_runtime_alert_code_has_no_dynamic_expression_or_notification_trading_calls() -> None:
    runtime_root = Path(__file__).resolve().parents[1] / "app"
    forbidden = [
        "eval(",
        "exec(",
        "APNs",
        "Firebase",
        "place_order",
        "unlock_trade",
        "OpenSecTradeContext",
    ]
    lines = [
        line
        for path in runtime_root.rglob("*.py")
        if "__pycache__" not in path.parts
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    text = "\n".join(lines)

    for item in forbidden:
        assert item not in text
    assert not any("compile(" in line and "re.compile(" not in line for line in lines)


def _rule_create(rule_type: AlertRuleType, parameters: dict[str, object]) -> AlertRuleCreate:
    return AlertRuleCreate(
        name=f"Test {rule_type.value}",
        rule_type=rule_type,
        severity=AlertSeverity.HIGH,
        symbol_scope=AlertSymbolScope.WATCHLIST,
        cooldown_seconds=1800,
        parameters=parameters,
    )


def _rule(
    rule_type: AlertRuleType,
    parameters: dict[str, object],
    symbols: list[str] | None = None,
    scope: AlertSymbolScope = AlertSymbolScope.WATCHLIST,
) -> AlertRule:
    now = datetime(2024, 1, 16, tzinfo=UTC)
    payload = AlertRuleCreate(
        name=f"Rule {rule_type.value}",
        rule_type=rule_type,
        severity=AlertSeverity.HIGH,
        symbol_scope=scope,
        symbols=symbols or [],
        cooldown_seconds=1800,
        parameters=parameters,
    )
    return AlertRule(
        id=f"rule-{rule_type.value}",
        **payload.model_dump(),
        is_system_default=False,
        created_at=now,
        updated_at=now,
    )


def _quote(
    symbol: str,
    change_percent: float = 1.0,
    volume: int = 100,
    average_volume_20d: int = 100,
) -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol=symbol,
        display_name=f"{symbol} Mock",
        market="US",
        currency="USD",
        provider="mock",
        price="101.00",
        previous_close="100.00",
        change="1.00",
        change_percent=str(change_percent),
        volume=volume,
        average_volume_20d=average_volume_20d,
        market_status="mock_closed",
        timestamp="2024-01-15T21:00:00Z",
        is_delayed=True,
    )


def _event(
    event_id: str,
    symbols: list[str],
    event_type: EventType = EventType.regulatory_filing,
    importance: int = 85,
) -> MarketEvent:
    return MarketEvent(
        id=event_id,
        event_type=event_type,
        title="Mock alert event",
        summary="Mock event summary",
        source_name="Mock Data Provider",
        source_url="mock://event",
        published_at="2024-01-15T10:00:00Z",
        received_at="2024-01-15T10:00:00Z",
        affected_symbols=symbols,
        importance_score=importance,
        reliability_score=100,
        sentiment=Sentiment.neutral,
        confidence=1.0,
        is_mock=True,
    )
