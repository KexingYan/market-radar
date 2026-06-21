# API Contract

Base path: `/api/v1`

All Phase 1 responses use local Mock JSON data only.

## GET /health

Returns service health and active provider.

Example:

```json
{
  "status": "ok",
  "service": "market-radar-api",
  "provider": "mock"
}
```

## GET /api/v1/quotes

Returns all available Mock quote snapshots.

Optional query:

- `symbols`: comma-separated symbols.

## GET /api/v1/quotes/{symbol}

Returns a single Mock quote snapshot. Unknown symbols return `404`.

## GET /api/v1/events

Returns Mock market events.

Optional queries:

- `symbols`: comma-separated symbols.
- `minimum_importance`: integer from 0 to 100.

## GET /api/v1/events/{event_id}

Returns a single Mock event. Unknown event IDs return `404`.

## GET /api/v1/watchlist

Returns Mock watchlist symbols and metadata.

## Phase 4B Storage APIs

## GET /api/v1/storage/status

Returns local storage readiness and aggregate counts. It does not return database paths or connection strings.

## GET /api/v1/storage/retention-preview

Returns quote retention policy preview. It does not delete data.

## GET /api/v1/history/quotes/{symbol}

Returns archived quote snapshots for a validated symbol.

## GET /api/v1/history/events

Returns archived events with optional symbol, event type, minimum importance, and limit filters.

## GET /api/v1/history/events/{event_id}

Returns one archived event.

## GET /api/v1/history/reports

Returns archived reports with optional report type and date filters.

## GET /api/v1/history/reports/{report_id}

Returns one archived report.

## POST /api/v1/watchlist

Adds one local watchlist symbol. It does not sync broker watchlists.

## DELETE /api/v1/watchlist/{symbol}

Disables one local watchlist symbol. It does not delete quote, event, or report history.

## Phase 4C Alert APIs

## GET /api/v1/alert-rules

Returns local alert rules. Optional filters:

- `enabled_only`
- `rule_type`

## POST /api/v1/alert-rules

Creates one local deterministic rule. Rule type, severity, symbol scope, symbols, cooldown, and parameters are strictly validated.

No arbitrary expressions, scripts, SQL, JavaScript, or Python code are accepted.

## PATCH /api/v1/alert-rules/{rule_id}

Updates local rule fields only. It does not change `id`, `created_at`, or `is_system_default`.

## POST /api/v1/alert-rules/{rule_id}/enable

Enables one local alert rule.

## POST /api/v1/alert-rules/{rule_id}/disable

Disables one local alert rule. Rules are not physically deleted in Phase 4C.

## POST /api/v1/alerts/evaluate

Manually evaluates local rules against current Mock/local data. This endpoint does not start background polling and does not request live SEC, OpenD, or real market data.

## GET /api/v1/alerts

Returns local in-app alert records with optional status, severity, symbol, rule type, date, and limit filters.

## GET /api/v1/alerts/{alert_id}

Returns one local alert record.

## POST /api/v1/alerts/{alert_id}/acknowledge

Idempotently marks one alert as acknowledged.

## POST /api/v1/alerts/{alert_id}/snooze

Snoozes one alert for a bounded duration. Phase 4C does not run a background expiration task.

## GET /api/v1/alerts/summary

Returns local alert inbox counts.

## Phase 5A Job APIs

## GET /api/v1/jobs

Returns local scheduled job definitions. Optional filters:

- `enabled_only`
- `job_type`

## GET /api/v1/jobs/{job_id}

Returns one local job definition.

## PATCH /api/v1/jobs/{job_id}

Updates `display_name`, `is_enabled`, `interval_seconds`, `timeout_seconds`, or `max_retries`.

It does not allow changing job id, job key, job type, or creation timestamp.

## POST /api/v1/jobs/{job_id}/run

Runs one fixed local job synchronously and records a `job_runs` entry. It does not start a background worker.

## POST /api/v1/jobs/pipeline/run

Runs the fixed full Mock pipeline:

```text
collect_quotes -> collect_events -> archive_market_data -> generate_intraday_report -> evaluate_alerts
```

## GET /api/v1/job-runs

Returns local job run history with optional job type, status, trigger type, date, and limit filters.

## GET /api/v1/job-runs/{run_id}

Returns one job run record without stack traces or sensitive data.

## GET /api/v1/scheduler/status

Returns foreground scheduler status. FastAPI does not run the scheduler, so `scheduler_process_running` is false for the API process unless a future reviewed status-sharing mechanism reports otherwise.

## Security Requirements

- Responses must not include passwords, tokens, API keys, account IDs, broker credentials, or authorization headers.
- All Phase 1 events must include `is_mock: true`.
- User-visible data must include timestamps and delay status.
