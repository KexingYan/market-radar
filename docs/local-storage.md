# Local Storage

Phase 4B adds local SQLite storage for personal development.

## Location

The development database lives under:

```text
PROJECT_ROOT/.runtime/data/market-radar.db
```

Tests may use in-memory SQLite or project-local test storage under:

```text
PROJECT_ROOT/.runtime/test-data/
```

Do not move the database outside the project. Do not upload it to third parties.

## Tables

- `quote_snapshots`
- `market_events`
- `event_symbols`
- `reports`
- `watchlist_symbols`
- `alert_rules`
- `alerts`

## Safety

- No cloud sync.
- No multi-user support.
- No account data.
- No holdings, costs, balances, orders, or trade history.
- No automatic deletion.
- No client-submitted database paths.
- No destructive cleanup endpoint.

## Retention

Default quote retention policy is 30 days, but Phase 4B only implements preview. It does not automatically delete data.

Future migrations may use Alembic or another reviewed migration process. Phase 4B initializes missing tables through SQLAlchemy metadata and does not drop or rebuild existing tables.

## Alert Storage

Phase 4C stores deterministic rule configuration in `alert_rules` and local in-app alert records in `alerts`.

Alert deduplication uses a unique deterministic key derived from rule id, symbol, source timestamp or event id, alert type, and a normalized trigger bucket.

Cooldown is persisted through alert history and checked by `rule_id + symbol`, so restarting the API does not bypass cooldown.

Phase 4C does not physically delete alerts, bulk clear the inbox, send system notifications, or run automatic expiration jobs.

## Job Storage

Phase 5A adds:

- `scheduled_jobs`
- `job_runs`
- `job_locks`

Default jobs are created idempotently and disabled by default. Job locks are SQLite rows with expiration timestamps. Job run records store aggregate summaries only.

The scheduler status file, when used, is stored under project runtime storage and is not an authority for locks. SQLite locks remain authoritative.
