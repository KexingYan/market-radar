# Job Orchestration

Phase 5A adds local job orchestration for existing Mock-only workflows.

## Job Types

- `collect_quotes`
- `collect_events`
- `archive_market_data`
- `generate_premarket_report`
- `generate_intraday_report`
- `generate_close_report`
- `evaluate_alerts`
- `full_pipeline`

Handlers are registered through a static whitelist. The API does not accept arbitrary module names, function names, shell commands, script paths, SQL expressions, or uploaded code.

## Default Jobs

The database creates these disabled jobs idempotently:

- `collect_quotes`
- `collect_events`
- `generate_intraday_report`
- `evaluate_alerts`
- `full_pipeline`

All default jobs are disabled. Starting FastAPI does not enable or run them.

## Run Records

Each run is stored in `job_runs` with status, trigger type, attempt, timing, safe result summary, and safe error code.

Result summaries store aggregate counts only. They must not store full quote payloads, event bodies, report text, credentials, tokens, emails, account identifiers, file paths, holdings, assets, orders, or tracebacks.

## Locking

Job locking uses SQLite rows with unique `job_key` and an expiration timestamp. It does not use Redis, file locks outside the project, system mutexes, or operating system services.

## Phase 5B Pipeline Validation

The default local pipeline was validated through FastAPI with:

- `MARKET_DATA_PROVIDER=mock`
- `EVENT_DATA_PROVIDER=mock`
- `FREE_ONLY_MODE=true`

The validated pipeline path was:

1. collect quotes
2. collect events
3. archive market data
4. generate intraday report
5. evaluate alerts
6. save job run

The validation did not request SEC, did not connect to OpenD, did not send system notifications, and did not trade.
