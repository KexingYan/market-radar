# Development Roadmap

## Phase 1: Safe Repository and Mock Prototype

Status: complete.

- Repository structure.
- Product and architecture documentation.
- FastAPI skeleton.
- SwiftUI static prototype.
- Mock data.
- Security and test standards.

## Phase 2: Locally Runnable UI and API

Status: backend complete; iOS implementation complete; iOS build validation pending macOS/Xcode.

- Backend health contract updated for local Mock-only operation.
- Backend tests expanded for Phase 2 safety requirements.
- iOS local API client source added.
- iOS bundled Mock fallback source added.
- Local development documentation added.
- Project-local uv, Python 3.12, and `.venv` workflow documented.
- Backend pytest and local API validation completed on Windows.
- iOS cannot be compiled in the current Windows environment.

## Phase 3A: Free Data Source Architecture and Offline Validation

Status: implemented in source and validated offline.

- SEC EDGAR event provider implemented.
- Moomoo read-only quote provider implemented.
- Provider fallback implemented.
- Provider status endpoint implemented.
- Offline tests implemented.
- SEC live validation deferred until the user can safely configure `SEC_USER_AGENT`.
- Moomoo live validation deferred until OpenD is manually started by the user.
- iOS source updated; iOS build validation remains pending macOS/Xcode.

## Phase 4A: Offline Market Reports and Event Organization

Status: implemented in source and validated offline.

- Premarket report model implemented.
- Intraday event digest model implemented.
- Close report model implemented.
- Deterministic report engine implemented.
- Event sorting, deduplication, and importance grouping implemented.
- Quote move rules implemented.
- Read-only report API endpoints implemented.
- iOS report source updated.
- No AI, investment advice, real network, database, or trading features added.

## Phase 4B: Local Historical Storage and Watchlist Persistence

Status: implemented in source and validated offline.

- Repository protocols implemented.
- Local SQLite repository implemented.
- Quote, event, and report archive implemented.
- Local watchlist persistence implemented.
- Storage status, retention preview, and history APIs implemented.
- No cloud sync, multi-user accounts, automatic deletion, or trading features added.

## Phase 4C: Local Alert Rules and In-App Inbox

Status: implemented in source and validated offline.

- Deterministic alert rule models implemented.
- Local in-app alert records implemented.
- SQLite alert persistence implemented.
- Rule-level deduplication and cooldown implemented.
- Manual alert evaluation endpoint implemented.
- Alert acknowledge and snooze implemented.
- iOS Alerts source added.
- No APNs, system notifications, background polling, AI, real data, account access, or trading features added.

## Phase 5A: Local Job Orchestration and Foreground Scheduler

Status: implemented in source and validated offline.

- Job model and job run history implemented.
- SQLite job locks implemented.
- Static job registry implemented.
- Manual Mock job execution implemented.
- Manual full pipeline implemented.
- Foreground scheduler module implemented.
- iOS Automation source added.
- No Windows service, scheduled task, startup item, background resident process, system notification, live data request, AI, or trading feature added.

## Phase 5B: Free Read-Only API Integration and E2E Validation

Status: implemented with gated live validation; default Mock pipeline validated locally.

- SEC live validation gating implemented.
- Moomoo live validation gating implemented.
- Default Mock full pipeline validated through local FastAPI.
- Offline regression tests expanded for live validation safety.
- SEC live request was skipped because `SEC_USER_AGENT` was not configured.
- Moomoo live quote validation did not open a quote context; SDK user-level logging setup was blocked by the sandbox before any snapshot request.
- No real response, real price, account data, credentials, holdings, assets, orders, or trading data was saved.
- Default providers remain `mock` and `mock`.
- `FREE_ONLY_MODE` remains true.

## Phase 5C: Moomoo SDK Runtime Isolation

Status: implemented and validated offline.

- Moomoo SDK runtime path configuration implemented before lazy SDK import.
- Project-local `logs`, `cache`, and `tmp` runtime directories declared under `.runtime/moomoo`.
- Runtime isolation failure and SDK logging failure map to safe provider reasons.
- Provider fallback to Mock data is preserved.
- No OpenD connection, Quote Context, real quote request, account read, holdings read, asset read, system directory write, or trading feature added.

## Phase 5D: Gated Live Smoke Validation

Status: completed for SEC EDGAR and local read-only Moomoo quote smoke.

- SEC User-Agent was loaded from a project-local runtime file.
- The full SEC contact email was not written to Git-tracked files or docs.
- SEC live smoke used AAPL only and made two requests.
- SEC ticker mapping, CIK validation, submissions metadata parsing, and MarketEvent conversion succeeded.
- Moomoo live smoke used local OpenD only and requested one `US.AAPL` snapshot.
- Moomoo Quote Context opened and closed successfully.
- No real price, account, holdings, assets, orders, or trade data was printed or saved.
- Default providers remain `mock` and `mock`; default tests remain offline.

## Phase 6A: Minimal Live End-to-End Loop

Status: completed once for AAPL only.

- Manual endpoint `/api/v1/live/aapl-e2e` implemented.
- SEC AAPL ticker mapping and submissions metadata were fetched with two requests.
- Local Moomoo OpenD returned one `US.AAPL` snapshot.
- Quote snapshot, SEC filing metadata events, intraday report, alert evaluation, and job run summary were archived locally.
- History APIs returned rows for AAPL quote history, AAPL event history, intraday report history, alerts summary, and job runs.
- No real price, full SEC response, full quote table, full User-Agent, contact email, account data, holdings, assets, orders, or trading action is returned by the live E2E endpoint.
- No scheduler or continuous polling was started.

## Phase 6B: Watchlist Controlled Live Refresh

Status: completed once with local watchlist fallback to AAPL.

- Manual endpoint `/api/v1/live/watchlist-refresh` implemented.
- Symbols are read only from enabled local watchlist entries.
- At most 5 supported US symbols are processed.
- If the enabled watchlist is empty or contains no supported symbols, AAPL is used as the fixed fallback.
- SEC request count is bounded by one ticker mapping request plus one submissions request per processed symbol.
- Moomoo uses local OpenD read-only snapshots only.
- Quotes, SEC filing metadata events, intraday report, alert evaluation, and job run summary were archived locally.
- No real price, full SEC response, full quote table, full User-Agent, contact email, account data, holdings, assets, orders, or trading action is returned.
- No scheduler or continuous polling was started.

## Phase 7A: iOS Live Refresh Source Integration

Status: implemented in source; build validation pending macOS/Xcode.

- iOS API client extended for live watchlist refresh and related readback endpoints.
- Live Refresh SwiftUI tab added.
- UI displays redacted status summaries, row counts, symbols, timestamps, alert summary, and job run counts.
- Live page intentionally does not display real quote prices.
- Mock fallback remains in place when the local API is unavailable.
- No APNs, system notifications, background refresh, account reads, holdings reads, assets reads, orders, or trading controls added.

## Phase 7B: iOS Xcode Build Readiness

Status: source-readiness review completed on Windows; build validation pending macOS/Xcode.

- Swift source structure reviewed.
- Xcode handoff instructions expanded.
- Live refresh decoding tests added to the iOS test source.
- Job run nested summary decoding support added.
- Simulator localhost and physical-device LAN limitations documented.
- No Xcode project was generated, no signing was configured, and no Apple account access was attempted.

## Phase 3B: User-Approved Live Provider Validation

Status: not started.

Future only. May validate OpenD or live SEC access after explicit user approval and manual setup. Phase 3B must not include trading.

## Phase 4: Filings and Licensed News Sources

Future only. Add official filings and authorized news after terms review.

## Phase 5: Event Scoring and AI Summaries

Future only. Add scoring and AI summaries while keeping source facts separate from generated analysis.

## Phase 6: Notifications and Deployment

Future only. Add APNs, backend deployment, and operational monitoring after security review.

## Phase 7: Security Audit

Future only. Review secrets handling, provider permissions, data retention, logs, and mobile storage.
