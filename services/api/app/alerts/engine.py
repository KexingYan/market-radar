import hashlib
import json
from datetime import UTC, datetime
from typing import Iterable

from app.alerts.models import (
    AlertCandidate,
    AlertRule,
    AlertRuleType,
    AlertSeverity,
    AlertSymbolScope,
    PriceDirection,
)
from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot


class AlertEngine:
    def evaluate(
        self,
        quotes: list[QuoteSnapshot],
        events: list[MarketEvent],
        rules: list[AlertRule],
        watchlist_symbols: list[str],
        now: datetime | None = None,
    ) -> list[AlertCandidate]:
        current_time = now or datetime.now(UTC)
        watchlist = {symbol.upper() for symbol in watchlist_symbols}
        available_symbols = {quote.symbol.upper() for quote in quotes}
        for event in events:
            available_symbols.update(symbol.upper() for symbol in event.affected_symbols)

        candidates: list[AlertCandidate] = []
        for rule in rules:
            if not rule.is_enabled:
                continue
            scoped_symbols = self._scoped_symbols(rule, watchlist, available_symbols)
            if rule.rule_type == AlertRuleType.PRICE_CHANGE_ABSOLUTE:
                candidates.extend(self._evaluate_price_change(rule, quotes, scoped_symbols, current_time))
            elif rule.rule_type == AlertRuleType.VOLUME_RATIO:
                candidates.extend(self._evaluate_volume_ratio(rule, quotes, scoped_symbols, current_time))
            elif rule.rule_type == AlertRuleType.EVENT_IMPORTANCE:
                candidates.extend(self._evaluate_event_importance(rule, events, scoped_symbols, current_time))
            elif rule.rule_type == AlertRuleType.EVENT_TYPE:
                candidates.extend(self._evaluate_event_type(rule, events, scoped_symbols, current_time))
            elif rule.rule_type == AlertRuleType.PRICE_AND_VOLUME:
                candidates.extend(self._evaluate_price_and_volume(rule, quotes, scoped_symbols, current_time))
        return candidates

    def _scoped_symbols(
        self,
        rule: AlertRule,
        watchlist: set[str],
        available_symbols: set[str],
    ) -> set[str]:
        if rule.symbol_scope == AlertSymbolScope.WATCHLIST:
            return watchlist
        if rule.symbol_scope == AlertSymbolScope.ALL_AVAILABLE:
            return available_symbols
        return {symbol.upper() for symbol in rule.symbols}

    def _evaluate_price_change(
        self,
        rule: AlertRule,
        quotes: list[QuoteSnapshot],
        scoped_symbols: set[str],
        now: datetime,
    ) -> list[AlertCandidate]:
        threshold = float(rule.parameters["threshold_percent"])
        direction = PriceDirection(rule.parameters.get("direction", "any"))
        result: list[AlertCandidate] = []
        for quote in self._quotes_in_scope(quotes, scoped_symbols):
            change = float(quote.change_percent)
            if direction == PriceDirection.UP and change < threshold:
                continue
            if direction == PriceDirection.DOWN and change > -threshold:
                continue
            if direction == PriceDirection.ANY and abs(change) < threshold:
                continue
            result.append(
                self._candidate(
                    rule=rule,
                    symbol=quote.symbol,
                    source_timestamp=quote.timestamp,
                    triggered_at=now,
                    is_mock=quote.provider == "mock",
                    title=f"{quote.symbol} price move alert",
                    message=f"{quote.symbol} moved {change:.2f}%, exceeding the configured {threshold:.2f}% threshold.",
                    metadata={
                        "actual_change_percent": round(change, 4),
                        "threshold_percent": threshold,
                        "quote_provider": quote.provider,
                        "rule_type": rule.rule_type.value,
                        "is_delayed": quote.is_delayed,
                    },
                    bucket=f"change:{_bucket(change)}",
                )
            )
        return result

    def _evaluate_volume_ratio(
        self,
        rule: AlertRule,
        quotes: list[QuoteSnapshot],
        scoped_symbols: set[str],
        now: datetime,
    ) -> list[AlertCandidate]:
        threshold = float(rule.parameters["threshold_ratio"])
        result: list[AlertCandidate] = []
        for quote in self._quotes_in_scope(quotes, scoped_symbols):
            if quote.average_volume_20d <= 0:
                continue
            ratio = quote.volume / quote.average_volume_20d
            if ratio < threshold:
                continue
            result.append(
                self._candidate(
                    rule=rule,
                    symbol=quote.symbol,
                    source_timestamp=quote.timestamp,
                    triggered_at=now,
                    is_mock=quote.provider == "mock",
                    title=f"{quote.symbol} volume spike alert",
                    message=(
                        f"{quote.symbol} volume reached {ratio:.2f}x its 20-day average, "
                        f"exceeding the configured {threshold:.2f}x threshold."
                    ),
                    metadata={
                        "actual_volume_ratio": round(ratio, 4),
                        "threshold_ratio": threshold,
                        "quote_provider": quote.provider,
                        "rule_type": rule.rule_type.value,
                        "is_delayed": quote.is_delayed,
                    },
                    bucket=f"volume:{_bucket(ratio)}",
                )
            )
        return result

    def _evaluate_event_importance(
        self,
        rule: AlertRule,
        events: list[MarketEvent],
        scoped_symbols: set[str],
        now: datetime,
    ) -> list[AlertCandidate]:
        minimum = int(rule.parameters["minimum_importance"])
        result: list[AlertCandidate] = []
        for event, symbol in self._events_in_scope(events, scoped_symbols):
            if event.importance_score < minimum:
                continue
            result.append(
                self._event_candidate(
                    rule=rule,
                    event=event,
                    symbol=symbol,
                    now=now,
                    message=(
                        f"{event.event_type.value} for {symbol} has importance score "
                        f"{event.importance_score}, exceeding the configured threshold of {minimum}."
                    ),
                    metadata={"minimum_importance": minimum},
                )
            )
        return result

    def _evaluate_event_type(
        self,
        rule: AlertRule,
        events: list[MarketEvent],
        scoped_symbols: set[str],
        now: datetime,
    ) -> list[AlertCandidate]:
        event_types = set(rule.parameters["event_types"])
        minimum = int(rule.parameters.get("minimum_importance", 0))
        result: list[AlertCandidate] = []
        for event, symbol in self._events_in_scope(events, scoped_symbols):
            if event.event_type.value not in event_types or event.importance_score < minimum:
                continue
            result.append(
                self._event_candidate(
                    rule=rule,
                    event=event,
                    symbol=symbol,
                    now=now,
                    message=(
                        f"{event.event_type.value} event for {symbol} matched the configured event type filter "
                        f"with importance score {event.importance_score}."
                    ),
                    metadata={"event_types": sorted(event_types), "minimum_importance": minimum},
                )
            )
        return result

    def _evaluate_price_and_volume(
        self,
        rule: AlertRule,
        quotes: list[QuoteSnapshot],
        scoped_symbols: set[str],
        now: datetime,
    ) -> list[AlertCandidate]:
        change_threshold = float(rule.parameters["minimum_absolute_change_percent"])
        volume_threshold = float(rule.parameters["minimum_volume_ratio"])
        result: list[AlertCandidate] = []
        for quote in self._quotes_in_scope(quotes, scoped_symbols):
            if quote.average_volume_20d <= 0:
                continue
            change = abs(float(quote.change_percent))
            ratio = quote.volume / quote.average_volume_20d
            if change < change_threshold or ratio < volume_threshold:
                continue
            result.append(
                self._candidate(
                    rule=rule,
                    symbol=quote.symbol,
                    source_timestamp=quote.timestamp,
                    triggered_at=now,
                    is_mock=quote.provider == "mock",
                    title=f"{quote.symbol} price and volume confirmation",
                    message=(
                        f"{quote.symbol} moved {change:.2f}% and volume reached {ratio:.2f}x its 20-day average, "
                        f"exceeding the configured {change_threshold:.2f}% and {volume_threshold:.2f}x thresholds."
                    ),
                    metadata={
                        "actual_absolute_change_percent": round(change, 4),
                        "minimum_absolute_change_percent": change_threshold,
                        "actual_volume_ratio": round(ratio, 4),
                        "minimum_volume_ratio": volume_threshold,
                        "quote_provider": quote.provider,
                        "rule_type": rule.rule_type.value,
                        "is_delayed": quote.is_delayed,
                    },
                    bucket=f"combo:{_bucket(change)}:{_bucket(ratio)}",
                )
            )
        return result

    def _event_candidate(
        self,
        rule: AlertRule,
        event: MarketEvent,
        symbol: str,
        now: datetime,
        message: str,
        metadata: dict[str, object],
    ) -> AlertCandidate:
        merged_metadata = {
            **metadata,
            "actual_importance": event.importance_score,
            "event_source": event.source_name,
            "event_type": event.event_type.value,
            "rule_type": rule.rule_type.value,
        }
        return self._candidate(
            rule=rule,
            symbol=symbol,
            event_id=event.id,
            source_timestamp=event.published_at,
            triggered_at=now,
            is_mock=event.is_mock,
            title=f"{symbol} event alert",
            message=message,
            metadata=merged_metadata,
            bucket=f"event:{event.event_type.value}:{event.importance_score // 5}",
        )

    def _candidate(
        self,
        rule: AlertRule,
        symbol: str,
        source_timestamp: datetime | None,
        triggered_at: datetime,
        is_mock: bool,
        title: str,
        message: str,
        metadata: dict[str, object],
        bucket: str,
        event_id: str | None = None,
    ) -> AlertCandidate:
        key_payload = {
            "rule_id": rule.id,
            "symbol": symbol.upper(),
            "event_id": event_id,
            "source_timestamp": source_timestamp.isoformat() if source_timestamp else None,
            "alert_type": rule.rule_type.value,
            "bucket": bucket,
        }
        return AlertCandidate(
            rule_id=rule.id,
            alert_type=rule.rule_type,
            severity=rule.severity,
            title=title,
            message=message,
            symbol=symbol.upper(),
            event_id=event_id,
            source_timestamp=source_timestamp,
            triggered_at=triggered_at,
            is_mock=is_mock,
            metadata={"is_mock": is_mock, **metadata},
            deduplication_key=_hash_payload(key_payload),
        )

    def _quotes_in_scope(self, quotes: Iterable[QuoteSnapshot], scoped_symbols: set[str]) -> Iterable[QuoteSnapshot]:
        for quote in quotes:
            if quote.symbol.upper() in scoped_symbols:
                yield quote

    def _events_in_scope(self, events: Iterable[MarketEvent], scoped_symbols: set[str]) -> Iterable[tuple[MarketEvent, str]]:
        for event in events:
            for symbol in event.affected_symbols:
                normalized = symbol.upper()
                if normalized in scoped_symbols:
                    yield event, normalized


def _bucket(value: float) -> int:
    return int(abs(value) * 10)


def _hash_payload(payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

