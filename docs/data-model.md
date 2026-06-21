# Data Model

## QuoteSnapshot

Fields:

- `symbol`: ticker or market symbol.
- `display_name`: user-facing name.
- `market`: market or region.
- `currency`: display currency.
- `provider`: provider identifier. Phase 1 uses `mock`.
- `price`: demonstration price.
- `previous_close`: demonstration previous close.
- `change`: demonstration absolute change.
- `change_percent`: demonstration percentage change.
- `volume`: demonstration volume.
- `average_volume_20d`: demonstration 20-day average volume.
- `market_status`: example status such as `closed` or `mock_session`.
- `timestamp`: Mock timestamp.
- `is_delayed`: whether the displayed data is delayed.

## MarketEvent

Fields:

- `id`: event identifier.
- `event_type`: event category.
- `title`: event title.
- `summary`: event summary.
- `source_name`: source display name. Phase 1 uses `Mock Data Provider`.
- `source_url`: empty string or `mock://` URL.
- `published_at`: Mock publish timestamp.
- `received_at`: Mock receive timestamp.
- `affected_symbols`: impacted symbols.
- `importance_score`: integer from 0 to 100.
- `reliability_score`: integer from 0 to 100.
- `sentiment`: `positive`, `neutral`, or `negative`.
- `confidence`: number from 0 to 1.
- `is_mock`: must be `true` for all Phase 1 events.

## Event Types

- `breaking_news`
- `company_announcement`
- `earnings`
- `guidance`
- `macro_event`
- `price_spike`
- `volume_spike`
- `regulatory_filing`
- `dividend`
- `share_buyback`
- `management_change`

## Reports

Phase 1 includes one static pre-market report and one static close report in the iOS prototype. They are Mock-only and must not imply real market conditions.

## Phase 4B Storage Tables

`quote_snapshots` stores typed quote snapshots with source timestamp, recorded timestamp, Mock flag, delay flag, and a unique deduplication key based on symbol, provider, and source timestamp.

`market_events` stores event metadata with content hash based deduplication. `event_symbols` stores affected symbol associations.

`reports` stores validated `MarketReport` payloads as JSON with report type, report date, generated time, schema version, Mock flag, and content hash.

`watchlist_symbols` stores local-only watchlist symbols. It does not store holdings, cost basis, balances, broker account identifiers, or trading data.

## Phase 4C Alert Tables

`alert_rules` stores deterministic local rule configuration:

- `rule_id`
- `name`
- `rule_type`
- `severity`
- `parameters_json`
- `symbol_scope`
- `symbols_json`
- `is_enabled`
- `cooldown_seconds`
- `is_system_default`
- `created_at`
- `updated_at`

Allowed rule types are `price_change_absolute`, `volume_ratio`, `event_importance`, `event_type`, and `price_and_volume`.

Allowed severities are `info`, `low`, `medium`, `high`, and `critical`.

`parameters_json` must be validated by the rule-specific Pydantic model before storage. It must not contain arbitrary expressions, scripts, account data, credentials, holdings, assets, or trading instructions.

`alerts` stores local in-app alert records:

- `alert_id`
- `rule_id`
- `alert_type`
- `severity`
- `title`
- `message`
- `symbol`
- `event_id`
- `source_timestamp`
- `triggered_at`
- `status`
- `acknowledged_at`
- `snoozed_until`
- `is_mock`
- `deduplication_key`
- `metadata_json`
- `created_at`
- `updated_at`

Allowed statuses are `new`, `acknowledged`, `snoozed`, and `expired`. Phase 4C does not physically delete alerts and does not run automatic expiration jobs.

## Phase 5A Job Tables

`scheduled_jobs` stores local foreground scheduler configuration:

- `job_id`
- `job_key`
- `job_type`
- `display_name`
- `is_enabled`
- `interval_seconds`
- `timeout_seconds`
- `max_retries`
- `last_run_at`
- `next_run_at`
- `created_at`
- `updated_at`

`job_runs` stores execution history:

- `run_id`
- `job_id`
- `job_key`
- `job_type`
- `status`
- `started_at`
- `finished_at`
- `duration_ms`
- `attempt`
- `trigger_type`
- `input_summary_json`
- `result_summary_json`
- `error_code`
- `error_message`
- `created_at`

`job_locks` stores SQLite-backed job locks:

- `job_key`
- `lock_owner`
- `acquired_at`
- `expires_at`

Job run summaries are aggregate-only and must not contain credentials, accounts, holdings, assets, full payloads, tracebacks, user paths, or trading data.
