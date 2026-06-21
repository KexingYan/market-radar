from datetime import UTC, datetime, timedelta

from app.alerts.engine import AlertEngine
from app.alerts.models import (
    AlertEvaluationRequest,
    AlertEvaluationResult,
    AlertItem,
    AlertRule,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertStatus,
)
from app.providers.base import MarketDataProvider
from app.repositories.base import AlertRepository, AlertRuleRepository, WatchlistRepository
from app.repositories.sqlite import alert_from_candidate


class AlertService:
    def __init__(
        self,
        rule_repository: AlertRuleRepository,
        alert_repository: AlertRepository,
        watchlist_repository: WatchlistRepository,
        quote_provider: MarketDataProvider,
        event_provider: MarketDataProvider,
        engine: AlertEngine | None = None,
    ) -> None:
        self._rules = rule_repository
        self._alerts = alert_repository
        self._watchlist = watchlist_repository
        self._quotes = quote_provider
        self._events = event_provider
        self._engine = engine or AlertEngine()

    async def list_rules(self, enabled_only: bool = False, rule_type: str | None = None) -> list[AlertRule]:
        await self._rules.ensure_default_rules()
        return await self._rules.list_rules(enabled_only=enabled_only, rule_type=rule_type)

    async def create_rule(self, payload: AlertRuleCreate) -> AlertRule:
        now = datetime.now(UTC)
        rule = AlertRule(
            id=f"rule-{now.strftime('%Y%m%d%H%M%S%f')}",
            **payload.model_dump(),
            is_system_default=False,
            created_at=now,
            updated_at=now,
        )
        return await self._rules.create_rule(rule)

    async def update_rule(self, rule_id: str, patch: AlertRuleUpdate) -> AlertRule | None:
        await self._rules.ensure_default_rules()
        return await self._rules.update_rule(rule_id, patch)

    async def set_enabled(self, rule_id: str, enabled: bool) -> AlertRule | None:
        await self._rules.ensure_default_rules()
        return await self._rules.set_enabled(rule_id, enabled)

    async def evaluate(self, request: AlertEvaluationRequest) -> AlertEvaluationResult:
        await self._rules.ensure_default_rules()
        rules = await self._rules.list_rules(enabled_only=True)
        watchlist = [item.symbol for item in await self._watchlist.list_symbols()]
        effective_symbols = request.symbols or watchlist
        if request.symbols:
            watchlist_for_scope = request.symbols
        else:
            watchlist_for_scope = watchlist

        quotes = await self._quotes.get_quotes(effective_symbols or None) if request.include_quotes else []
        events = await self._events.get_events(symbols=effective_symbols or None) if request.include_events else []
        now = datetime.now(UTC)
        candidates = self._engine.evaluate(
            quotes=quotes,
            events=events,
            rules=rules,
            watchlist_symbols=watchlist_for_scope,
            now=now,
        )

        created: list[AlertItem] = []
        cooldown_suppressed = 0
        for candidate in candidates:
            rule = next((item for item in rules if item.id == candidate.rule_id), None)
            if rule is None or not candidate.symbol:
                continue
            since = candidate.triggered_at - timedelta(seconds=rule.cooldown_seconds)
            recent = await self._alerts.find_recent_for_cooldown(rule.id, candidate.symbol, since)
            if recent is not None:
                cooldown_suppressed += 1
                continue
            created.append(alert_from_candidate(candidate))

        save_result = await self._alerts.save_alerts(created)
        return AlertEvaluationResult(
            evaluated_rules=len(rules),
            evaluated_symbols=len(set(effective_symbols)),
            created_alerts=save_result.inserted,
            duplicate_alerts=save_result.duplicates,
            cooldown_suppressed=cooldown_suppressed,
            mock_data_used=any(getattr(item, "provider", "") == "mock" for item in quotes) or any(event.is_mock for event in events),
        )

    async def list_alerts(
        self,
        status: AlertStatus | None = None,
        severity: str | None = None,
        symbol: str | None = None,
        rule_type: str | None = None,
        limit: int = 50,
        before: datetime | None = None,
        after: datetime | None = None,
        include_snoozed: bool = False,
    ) -> list[AlertItem]:
        return await self._alerts.list_alerts(
            status=status,
            severity=severity,
            symbol=symbol,
            rule_type=rule_type,
            limit=limit,
            before=before,
            after=after,
            include_snoozed=include_snoozed,
        )

    async def get_alert(self, alert_id: str) -> AlertItem | None:
        return await self._alerts.get_alert(alert_id)

    async def acknowledge(self, alert_id: str) -> AlertItem | None:
        return await self._alerts.acknowledge(alert_id, datetime.now(UTC))

    async def snooze(self, alert_id: str, snoozed_until: datetime) -> AlertItem | None:
        return await self._alerts.snooze(alert_id, snoozed_until)

