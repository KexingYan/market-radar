# Phase 4C: Local Alert Rules and In-App Inbox

Phase 4C adds a local deterministic alert engine and an in-app alert inbox.

## Completed Scope

- Alert rule data model.
- Alert record data model.
- SQLite tables for `alert_rules` and `alerts`.
- Repository protocols and SQLite implementations.
- Default alert rule initialization.
- Deduplication keys.
- Rule-level cooldown based on persisted alert history.
- Manual evaluation endpoint.
- Alert list, detail, summary, acknowledge, and snooze endpoints.
- iOS Alerts source files.
- Offline tests.

## Manual Evaluation Only

Alert evaluation is triggered by:

- tests, or
- `POST /api/v1/alerts/evaluate`.

No background scheduler is active in Phase 4C. There is no polling loop, worker, APNs integration, system notification delivery, or remote push service.

## Non-Goals

- Real SEC requests.
- OpenD or Moomoo connection.
- Live market data.
- AI summaries.
- Investment advice.
- Buy/sell signals.
- Trading or order placement.
- Account, position, asset, order, or transaction access.
- Public or LAN service exposure.

## Local Data Only

Default configuration remains:

```text
MARKET_DATA_PROVIDER=mock
EVENT_DATA_PROVIDER=mock
FREE_ONLY_MODE=true
TRADING_ENABLED=false
PAID_DATA_ENABLED=false
```

Mock-triggered alerts remain clearly marked as Mock data and do not represent real market conditions.

