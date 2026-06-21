# Market Radar

Market Radar is a personal research project for monitoring stock market snapshots, watchlist movement, and major market events in a high-density iPhone interface.

Current stage: Phase 3A, free data source architecture with offline validation.

This project currently has no real market data, no brokerage account integration, no trading features, and no investment advice.

## Scope

- Product and architecture documentation.
- Static SwiftUI prototype for iPhone.
- Minimal FastAPI backend skeleton.
- Local Mock JSON data only.
- Test files for core API behavior.
- Security, configuration, and data source policies.

## Non-Goals

- No live quotes.
- No real news.
- No AI provider.
- No database or Redis connection.
- No user login.
- No broker login.
- No order placement or trading workflow.
- No push notification delivery.

## Repository Structure

```text
market-radar/
├── apps/ios/MarketRadar/
├── services/api/
├── packages/domain/
├── docs/
├── scripts/
└── infra/
```

## Mock Data

All current quote, watchlist, report, and event data is fictional or generic demonstration data. User-facing screens and API records mark Mock data clearly.

Required user-facing disclaimer:

> 当前为 Mock 演示数据，不代表真实市场价格。仅供信息展示，不构成投资建议。

## Security

Credentials must not enter this repository. The only environment file in Phase 1 is `.env.example`, and it contains placeholders only.

No real provider, brokerage, news, AI, or account API is connected in this stage.

## Phase 2 Local Development

Requirements:

- Python 3.12 or newer.
- Dependencies installed only into `PROJECT_ROOT/.venv`.
- No real market data, news, AI, account, or trading provider.
- Project-local uv in `.tools/uv`.
- uv-managed Python 3.12 in `.runtime/python`.
- uv cache in `.cache/uv`.
- No system PATH modification and no global installation.

Windows PowerShell:

```powershell
$env:UV_INSTALL_DIR = "$PWD\.tools\uv"
$env:UV_PYTHON_INSTALL_DIR = "$PWD\.runtime\python"
$env:UV_PYTHON_BIN_DIR = "$PWD\.runtime\bin"
$env:UV_CACHE_DIR = "$PWD\.cache\uv"
$env:UV_PROJECT_ENVIRONMENT = "$PWD\.venv"
$env:UV_NO_MODIFY_PATH = "1"

.\.tools\uv\uv.exe --no-config python install 3.12
.\.tools\uv\uv.exe --no-config venv .venv --python 3.12
.\.tools\uv\uv.exe --no-config pip install --python .\.venv -e ".\services\api[dev]"
.\.venv\Scripts\python -m pytest .\services\api
Set-Location .\services\api
..\..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

macOS/Linux:

```bash
export UV_INSTALL_DIR="$PWD/.tools/uv"
export UV_PYTHON_INSTALL_DIR="$PWD/.runtime/python"
export UV_PYTHON_BIN_DIR="$PWD/.runtime/bin"
export UV_CACHE_DIR="$PWD/.cache/uv"
export UV_PROJECT_ENVIRONMENT="$PWD/.venv"
export UV_NO_MODIFY_PATH=1

./.tools/uv/uv --no-config python install 3.12
./.tools/uv/uv --no-config venv .venv --python 3.12
./.tools/uv/uv --no-config pip install --python ./.venv -e "./services/api[dev]"
./.venv/bin/python -m pytest ./services/api
cd services/api
../../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Visit `http://127.0.0.1:8000/health` from the same machine.

Stop the service with `Ctrl+C` in the terminal running Uvicorn.

Do not bind the backend to `0.0.0.0`. Do not use LAN addresses, tunnels, public servers, or real provider URLs.

The iOS prototype is configured for `http://127.0.0.1:8000` in Simulator-oriented local development. If the local API is unavailable, it falls back to bundled Mock data and displays `Bundled Mock Fallback`.

A physical iPhone cannot use its own `127.0.0.1` to reach the computer backend. Phase 2 does not enable LAN access.

## Phase 3A Free Data Sources

Implemented in source:

- Provider registry and fallback.
- Provider status endpoint: `/api/v1/providers/status`.
- SEC EDGAR event provider, tested offline with `httpx.MockTransport`.
- Moomoo read-only quote provider and SDK adapter, tested offline with fake adapters.
- `/api/v1/filings` endpoint.

Default configuration remains:

```text
MARKET_DATA_PROVIDER=mock
EVENT_DATA_PROVIDER=mock
FREE_ONLY_MODE=true
```

Phase 3A does not install, start, configure, probe, or log in to OpenD. No connection attempt is made to `127.0.0.1:11111`.

SEC live validation is skipped by instruction. Moomoo live validation is deferred to a separate user-approved Phase 3B.

Current live validation status:

- SEC live validation: Deferred until the user can safely configure `SEC_USER_AGENT`.
- Moomoo live validation: Deferred until OpenD is manually started by the user.

## Phase 4A Offline Reports

Implemented in source:

- Premarket report endpoint: `/api/v1/reports/premarket`
- Intraday event digest endpoint: `/api/v1/reports/intraday`
- Close report endpoint: `/api/v1/reports/close`
- Deterministic event sorting, deduplication, importance grouping, and quote move rules.

Reports use existing Mock data and mocked provider test data only. They do not use AI and do not provide investment advice.

## Phase 4B Local Storage

Implemented in source:

- Local SQLite storage under project runtime storage.
- Repository abstraction for quotes, events, reports, and watchlist symbols.
- Idempotent quote, event, and report archive.
- Read-only history APIs.
- Local-only watchlist add and remove APIs.
- Retention preview without automatic deletion.

The database is for local personal development only. It is not uploaded, synced, or committed to Git.

## Phase 4C Local Alerts

Implemented in source:

- Deterministic local alert rules.
- Local in-app alert inbox records.
- Price move, volume ratio, event importance, event type, and price-and-volume rules.
- Rule-level cooldown and deduplication.
- Alert acknowledge and snooze APIs.
- Manual alert evaluation endpoint: `/api/v1/alerts/evaluate`.

Phase 4C does not send APNs, system notifications, email, SMS, webhooks, or chat messages. It does not run a background scheduler or polling loop. Alert evaluation is manual and uses current Mock/local data only.

Alerts do not provide investment advice and never place trades.

## Phase 5A Local Automation

Implemented in source:

- Local job models and job run history.
- SQLite job locks.
- Manual Mock quote/event collection tasks.
- Manual report and alert tasks.
- Manual full pipeline endpoint: `/api/v1/jobs/pipeline/run`.
- Foreground-only scheduler module: `python -m app.scheduler_runner`.

The scheduler is disabled by default with `SCHEDULER_ENABLED=false`. It does not register a Windows service, create a scheduled task, create a startup item, run hidden in the background, send system notifications, connect to OpenD, request SEC, or trade.

## Phase 5B Free Read-Only API Integration

Implemented and validated in the current repository:

- Live validation gating helpers for SEC EDGAR and Moomoo OpenD.
- Offline regression tests proving default pytest does not request SEC or connect to OpenD.
- Default Mock full pipeline validation through the local FastAPI API.
- Documentation for live validation status and fallback behavior.

Current Phase 5B validation result:

- SEC live validation: skipped because `SEC_USER_AGENT` was not configured in the current process.
- SEC request count: 0.
- Moomoo live validation: unavailable; the SDK attempted user-level logging setup before opening a quote context and was blocked by the sandbox.
- Moomoo quote context opened: no.
- Moomoo snapshot request count: 0.
- Real responses saved: no.
- Real prices saved or displayed: no.
- Real email saved or displayed: no.
- Account, holdings, assets, orders, and trading access: no.
- Default providers remain `mock` and `mock`.
- `FREE_ONLY_MODE` remains true.

## Phase 5C Moomoo Runtime Isolation

Implemented and validated offline:

- Moomoo SDK runtime paths are configured before lazy SDK import.
- SDK logs, cache, and temporary files are constrained to project runtime storage under `.runtime/moomoo/`.
- The configuration uses current-process runtime settings only and does not modify system PATH, shell profiles, registry, or user configuration.
- If runtime isolation or SDK logging setup fails, the provider returns a safe failure reason and falls back to Mock data.
- This phase did not open a Quote Context, connect to OpenD, request real quotes, read accounts, query holdings or assets, or output real prices.

## Phase 6A Minimal Live E2E

Implemented and validated once:

- Manual endpoint: `POST /api/v1/live/aapl-e2e`.
- Scope: AAPL only.
- SEC EDGAR live metadata: AAPL ticker mapping and submissions metadata only.
- Moomoo OpenD live quote check: one local read-only `US.AAPL` snapshot.
- Local SQLite archive: quote snapshot, SEC filing metadata events, intraday report, alerts, and job run summary.
- History API verification completed with row counts only.

The endpoint returns only a redacted summary. It does not return real prices, full SEC responses, full quote tables, full User-Agent values, contact emails, account data, holdings, assets, orders, or trading fields.

## Phase 6B Watchlist Live Refresh

Implemented and validated once:

- Manual endpoint: `POST /api/v1/live/watchlist-refresh`.
- Source symbols: enabled local watchlist only.
- Limit: at most 5 supported US symbols.
- Empty or unsupported watchlist fallback: AAPL.
- SEC EDGAR metadata and Moomoo local snapshot are archived into local SQLite.
- Intraday report, alert evaluation, and job run summary are generated.

The endpoint does not accept external symbols or URLs. It returns only redacted counts and status flags, not real prices, full SEC responses, full quote tables, full User-Agent values, contact emails, account data, holdings, assets, orders, or trading fields.

## Phase 7A iOS Live Refresh Source

Implemented in SwiftUI source:

- Local API client calls for `POST /api/v1/live/watchlist-refresh`.
- Local API client reads for quote history, event history, intraday report history, alerts summary, job runs, and provider status.
- A Live tab with a manual `Run Live Refresh` button.
- Loading, success, and error states.
- Redacted summary display for symbols, SEC status, Moomoo status, archive counts, report status, alerts, and job run status.
- Quote history is displayed only as returned rows, symbol, and timestamp; real prices are not shown in the Live page.

Windows cannot compile iOS SwiftUI. Build validation remains pending on macOS/Xcode.

## Phase 7B iOS Build Readiness

Completed in source:

- Swift source structure reviewed for Xcode target handoff.
- Live refresh decoding and API path tests added to the iOS test source.
- Nested job run summary decoding supported.
- Xcode handoff documentation expanded with target file lists, Simulator localhost behavior, physical-device limitations, and ATS guidance.

No Xcode project was generated in Windows. iOS build and test validation remain pending on macOS/Xcode.

## Disclaimer

This is a personal research project. It is not affiliated with any broker, data vendor, exchange, or news provider. It does not provide financial, investment, legal, tax, or trading advice.
