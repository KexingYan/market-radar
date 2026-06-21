from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query

from app.alerts.models import (
    AlertEvaluationRequest,
    AlertEvaluationResult,
    AlertItem,
    AlertRule,
    AlertRuleCreate,
    AlertRuleType,
    AlertRuleUpdate,
    AlertSeverity,
    AlertSnoozeRequest,
    AlertStatus,
    AlertSummary,
)
from app.alerts.service import AlertService
from app.providers.registry import event_provider, quote_provider
from app.repositories import alert_repository, alert_rule_repository, watchlist_repository

router = APIRouter(prefix="/api/v1", tags=["alerts"])

service = AlertService(
    rule_repository=alert_rule_repository,
    alert_repository=alert_repository,
    watchlist_repository=watchlist_repository,
    quote_provider=quote_provider,
    event_provider=event_provider,
)


@router.get("/alert-rules")
async def list_alert_rules(
    enabled_only: bool = Query(default=False),
    rule_type: AlertRuleType | None = Query(default=None),
) -> list[AlertRule]:
    return await service.list_rules(enabled_only=enabled_only, rule_type=rule_type.value if rule_type else None)


@router.post("/alert-rules", status_code=201)
async def create_alert_rule(payload: AlertRuleCreate) -> AlertRule:
    try:
        return await service.create_rule(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/alert-rules/{rule_id}")
async def update_alert_rule(rule_id: str, payload: AlertRuleUpdate) -> AlertRule:
    rule = await service.update_rule(rule_id, payload)
    if rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.post("/alert-rules/{rule_id}/enable")
async def enable_alert_rule(rule_id: str) -> AlertRule:
    rule = await service.set_enabled(rule_id, True)
    if rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.post("/alert-rules/{rule_id}/disable")
async def disable_alert_rule(rule_id: str) -> AlertRule:
    rule = await service.set_enabled(rule_id, False)
    if rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.post("/alerts/evaluate")
async def evaluate_alerts(payload: AlertEvaluationRequest) -> AlertEvaluationResult:
    return await service.evaluate(payload)


@router.get("/alerts")
async def list_alerts(
    status: AlertStatus | None = Query(default=None),
    severity: AlertSeverity | None = Query(default=None),
    symbol: str | None = Query(default=None),
    rule_type: AlertRuleType | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    before: datetime | None = Query(default=None),
    after: datetime | None = Query(default=None),
    include_snoozed: bool = Query(default=False),
) -> list[AlertItem]:
    try:
        return await service.list_alerts(
            status=status,
            severity=severity.value if severity else None,
            symbol=symbol,
            rule_type=rule_type.value if rule_type else None,
            limit=limit,
            before=before,
            after=after,
            include_snoozed=include_snoozed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/alerts/summary")
async def alerts_summary() -> AlertSummary:
    return await alert_repository.summary(datetime.now(UTC))


@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str) -> AlertItem:
    alert = await service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> AlertItem:
    alert = await service.acknowledge(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/snooze")
async def snooze_alert(alert_id: str, payload: AlertSnoozeRequest) -> AlertItem:
    alert = await service.snooze(alert_id, payload.target_time(datetime.now(UTC)))
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
