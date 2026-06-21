# Phase 5B API Integration

Phase 5B validates the free, read-only provider integration boundaries and the default local Mock pipeline.

## Status

- SEC live validation: skipped because `SEC_USER_AGENT` was not configured.
- Moomoo live validation: unavailable; no quote context was opened and no snapshot request was sent.
- Provider fallback: available and used for unavailable live validation.
- Default Mock pipeline: validated through the local FastAPI API.
- Offline regression tests: passed.

## SEC Result

- SEC_USER_AGENT present: no.
- Full User-Agent output: no.
- Real email saved: no.
- SEC request count: 0.
- Endpoint categories requested: none.
- AAPL parsing from live SEC: not executed.
- Live MarketEvent conversion: not executed.
- Full SEC response saved: no.

SEC remains available only through the gated provider path. Default tests use MockTransport and must not access public SEC endpoints.

## Moomoo Result

- Connection target allowed by design: `127.0.0.1:11111`.
- Quote context opened: no.
- Snapshot request sent: no.
- Real price output: no.
- Account read: no.
- Holdings or assets queried: no.
- Orders or trades queried: no.
- Context close: not applicable.
- Fallback Mock used: yes.

The SDK attempted user-level logging setup before a quote context could be opened. The sandbox blocked that operation, so the validation stopped before any OpenD connection or quote request.

Phase 5C adds project-local Moomoo SDK runtime isolation so SDK logging, cache, and temporary files are configured before lazy SDK import. Live quote validation still remains separate and is not performed by Phase 5C.

## Default Pipeline

Validated through local FastAPI on `127.0.0.1:8000`:

1. collect quotes
2. collect events
3. archive market data
4. generate intraday report
5. evaluate alerts
6. save job run

The default pipeline used Mock providers only. It did not connect to OpenD, request SEC, send system notifications, or perform trades.

## Data Handling

Phase 5B did not save:

- real SEC responses
- real quote prices
- real email addresses
- account identifiers
- holdings
- assets
- orders
- trade records

Default providers remain `mock` and `mock`, and `FREE_ONLY_MODE` remains true.
