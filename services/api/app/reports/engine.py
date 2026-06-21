from datetime import UTC, datetime
from decimal import Decimal

from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot
from app.domain.report import EventDigestItem, EventImportanceGroup, MarketMoveAlert, MarketReport, ReportType


def build_premarket_report(
    quotes: list[QuoteSnapshot],
    events: list[MarketEvent],
    generated_at: datetime | None = None,
) -> MarketReport:
    return _build_report(ReportType.premarket, "盘前 Mock 市场报告", quotes, events, generated_at)


def build_intraday_report(
    quotes: list[QuoteSnapshot],
    events: list[MarketEvent],
    generated_at: datetime | None = None,
) -> MarketReport:
    return _build_report(ReportType.intraday, "盘中重大事件摘要", quotes, events, generated_at)


def build_close_report(
    quotes: list[QuoteSnapshot],
    events: list[MarketEvent],
    generated_at: datetime | None = None,
) -> MarketReport:
    return _build_report(ReportType.close, "收盘 Mock 市场报告", quotes, events, generated_at)


def sort_and_deduplicate_events(events: list[MarketEvent]) -> list[MarketEvent]:
    best_by_key: dict[tuple[str, str, tuple[str, ...]], MarketEvent] = {}
    for event in events:
        key = (
            event.event_type.value,
            event.title.strip().lower(),
            tuple(sorted(symbol.upper() for symbol in event.affected_symbols)),
        )
        current = best_by_key.get(key)
        if current is None or _event_sort_key(event) < _event_sort_key(current):
            best_by_key[key] = event
    return sorted(best_by_key.values(), key=_event_sort_key)


def group_for_importance(score: int) -> EventImportanceGroup:
    if score >= 85:
        return EventImportanceGroup.critical
    if score >= 70:
        return EventImportanceGroup.high
    if score >= 50:
        return EventImportanceGroup.medium
    return EventImportanceGroup.low


def detect_market_moves(quotes: list[QuoteSnapshot]) -> list[MarketMoveAlert]:
    alerts: list[MarketMoveAlert] = []
    for quote in quotes:
        change_percent = float(quote.change_percent)
        volume_ratio = _volume_ratio(quote)
        if abs(change_percent) >= 3:
            direction = "上涨" if change_percent > 0 else "下跌"
            alerts.append(
                MarketMoveAlert(
                    symbol=quote.symbol,
                    display_name=quote.display_name,
                    alert_type="price_move",
                    description=f"{quote.symbol} Mock价格{direction} {change_percent:.2f}%。",
                    change_percent=change_percent,
                    volume_ratio=volume_ratio,
                )
            )
        if volume_ratio is not None and volume_ratio >= 1.5:
            alerts.append(
                MarketMoveAlert(
                    symbol=quote.symbol,
                    display_name=quote.display_name,
                    alert_type="volume_move",
                    description=f"{quote.symbol} Mock成交量约为20日均量的 {volume_ratio:.2f} 倍。",
                    change_percent=change_percent,
                    volume_ratio=volume_ratio,
                )
            )
    return sorted(alerts, key=lambda alert: (alert.alert_type, -abs(alert.change_percent), alert.symbol))


def _build_report(
    report_type: ReportType,
    title: str,
    quotes: list[QuoteSnapshot],
    events: list[MarketEvent],
    generated_at: datetime | None,
) -> MarketReport:
    timestamp = generated_at or datetime.now(UTC)
    sorted_events = sort_and_deduplicate_events(events)
    event_items = [_to_digest_item(event) for event in sorted_events]
    groups: dict[EventImportanceGroup, list[EventDigestItem]] = {
        EventImportanceGroup.critical: [],
        EventImportanceGroup.high: [],
        EventImportanceGroup.medium: [],
        EventImportanceGroup.low: [],
    }
    for item in event_items:
        groups[item.group].append(item)

    alerts = detect_market_moves(quotes)
    key_points = _key_points(report_type, quotes, event_items, alerts)
    return MarketReport(
        id=f"{report_type.value}-{timestamp.strftime('%Y%m%d')}",
        report_type=report_type,
        title=title,
        generated_at=timestamp,
        data_source="mock",
        summary=_summary(report_type, event_items, alerts),
        key_points=key_points,
        event_groups=groups,
        market_move_alerts=alerts,
        is_mock=all(event.is_mock for event in events) and all(quote.provider == "mock" for quote in quotes),
    )


def _to_digest_item(event: MarketEvent) -> EventDigestItem:
    return EventDigestItem(
        id=event.id,
        title=event.title,
        event_type=event.event_type.value,
        source_name=event.source_name,
        affected_symbols=event.affected_symbols,
        importance_score=event.importance_score,
        group=group_for_importance(event.importance_score),
        published_at=event.published_at,
        is_mock=event.is_mock,
    )


def _event_sort_key(event: MarketEvent) -> tuple[int, datetime, str]:
    return (-event.importance_score, event.published_at, event.id)


def _volume_ratio(quote: QuoteSnapshot) -> float | None:
    if quote.average_volume_20d <= 0:
        return None
    return float(Decimal(quote.volume) / Decimal(quote.average_volume_20d))


def _summary(
    report_type: ReportType,
    events: list[EventDigestItem],
    alerts: list[MarketMoveAlert],
) -> str:
    label = {
        ReportType.premarket: "盘前",
        ReportType.intraday: "盘中",
        ReportType.close: "收盘",
    }[report_type]
    return f"{label}报告基于 Mock 行情和事件生成，包含 {len(events)} 条去重事件和 {len(alerts)} 条规则异动。"


def _key_points(
    report_type: ReportType,
    quotes: list[QuoteSnapshot],
    events: list[EventDigestItem],
    alerts: list[MarketMoveAlert],
) -> list[str]:
    high_events = [event for event in events if event.importance_score >= 70]
    delayed_count = sum(1 for quote in quotes if quote.is_delayed)
    return [
        f"覆盖 {len(quotes)} 条 Mock 行情快照。",
        f"识别 {len(high_events)} 条高重要性或关键事件。",
        f"检测到 {len(alerts)} 条规则行情异动。",
        f"{delayed_count} 条行情标记为延迟或演示数据。",
        "本报告仅使用规则整理，不包含预测或方向性结论。",
    ]
