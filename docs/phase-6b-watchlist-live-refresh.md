# Phase 6B Watchlist Live Refresh

Phase 6B validates a controlled, one-shot live refresh using the local enabled watchlist.

## Endpoint

```text
POST /api/v1/live/watchlist-refresh
```

The endpoint accepts no symbol list, URL, account, trading, or provider override parameters.

## Symbol Selection

1. Read enabled local watchlist entries.
2. Keep supported US symbols only.
3. Deduplicate in watchlist order.
4. Process at most 5 symbols.
5. If no supported symbol is available, use AAPL as the fixed fallback.

## Live Validation Result

- Processed symbols: AAPL.
- Fallback symbol used: yes.
- SEC attempted: yes.
- SEC success: yes.
- SEC request count: 2.
- SEC filings parsed: 10.
- Moomoo attempted: yes.
- Moomoo success: yes.
- Moomoo snapshot rows: 1.
- Quote Context closed: yes.
- Quote archived: yes.
- Events archived: duplicate-only in this run.
- Report generated and archived: yes.
- Alerts evaluated: yes.
- Job run saved: yes.
- Fallback used by providers: no.

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

Phase 6B does not start a scheduler, does not enable background polling, does not bind to `0.0.0.0`, does not expose LAN or public services, does not connect to paid data sources, and does not trade.
