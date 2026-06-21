# Alert Rules

Phase 4C alert rules are deterministic local rules. They are validated with Pydantic models, stored in local SQLite, and evaluated only when `/api/v1/alerts/evaluate` is called.

No AI, scripts, arbitrary expressions, or investment advice are used.

## Supported Rule Types

- `price_change_absolute`: triggers when absolute price change percentage crosses a threshold.
- `volume_ratio`: triggers when volume divided by 20-day average volume crosses a threshold.
- `event_importance`: triggers when a market event importance score crosses a threshold.
- `event_type`: triggers when a whitelisted event type and optional importance threshold match.
- `price_and_volume`: triggers when price movement and volume ratio both cross thresholds.

## Default Rules

- Watchlist price move: `abs(change_percent) >= 3.0`, severity `high`, cooldown `1800` seconds.
- Watchlist volume spike: `volume / average_volume_20d >= 2.0`, severity `medium`, cooldown `1800` seconds.
- High importance event: `importance_score >= 80`, severity `high`, cooldown `3600` seconds.
- Price and volume confirmation: `abs(change_percent) >= 3.0` and volume ratio `>= 2.0`, severity `critical`, cooldown `3600` seconds.

Default rule creation is idempotent. Existing user-edited rules are not automatically rewritten.

## Safety Boundaries

- Alerts are in-app local records only.
- No APNs, system notification, email, SMS, webhook, or chat delivery is implemented.
- No background scheduler, polling loop, worker, or resident process is active.
- Rules do not support `eval`, `exec`, scripts, SQL expressions, JavaScript, Python formulas, or dynamic module loading.
- Alerts never read brokerage accounts, positions, assets, orders, passwords, tokens, or keys.
- Alerts never place trades and do not generate buy/sell recommendations.

## Snooze

Alerts can be snoozed for bounded durations such as 15 minutes, 1 hour, 4 hours, or 24 hours. The maximum snooze window is 7 days. Phase 4C does not run a background expiration task.

## Phase 5A Evaluation

Phase 5A can call the existing alert evaluation service from a manual job or foreground scheduler job. This still creates only local in-app alert records. It does not send APNs, system notifications, email, SMS, webhooks, or trading orders.
