# Phase 6A Minimal Live E2E

Phase 6A validates a single-symbol, one-shot live local loop.

## Scope

- Symbol: AAPL only.
- SEC: AAPL ticker-to-CIK mapping and submissions metadata.
- Moomoo: local OpenD read-only `US.AAPL` snapshot.
- Storage: local SQLite only.
- API: local FastAPI only.

## Endpoint

```text
POST /api/v1/live/aapl-e2e
```

The endpoint accepts no symbol, URL, account, trading, or provider override parameters. It always runs the fixed AAPL flow.

## Flow

1. Fetch one Moomoo `US.AAPL` snapshot.
2. Fetch SEC AAPL ticker mapping.
3. Fetch SEC AAPL submissions metadata.
4. Convert SEC filings to regulatory filing events.
5. Archive the quote snapshot and filing metadata events.
6. Generate and archive an intraday report.
7. Evaluate local alert rules.
8. Save a job run summary.
9. Verify history APIs by row counts.

## Live Validation Result

- SEC attempted: yes.
- SEC success: yes.
- SEC request count: 2.
- SEC filings parsed: 50.
- Moomoo attempted: yes.
- Moomoo success: yes.
- Moomoo snapshot rows: 1.
- Quote Context closed: yes.
- Quote archived: yes.
- Events archived: yes.
- Report generated and archived: yes.
- Alerts evaluated: yes.
- Job run saved: yes.
- Fallback used: no.

## Redaction Rules

The endpoint does not return:

- real prices
- full SEC responses
- full quote tables
- full User-Agent values
- contact email addresses
- account identifiers
- holdings
- assets
- orders
- trade records

## Safety

Phase 6A does not start a scheduler, does not enable background polling, does not bind to `0.0.0.0`, does not expose LAN or public services, does not connect to paid data sources, and does not trade.
