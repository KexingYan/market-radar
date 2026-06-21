# Free Data Sources

Phase 3A implements provider architecture for free or locally authorized data sources while keeping defaults on Mock data.

## Current Implementations

- Mock quote and event provider.
- SEC EDGAR regulatory filing event provider.
- Moomoo read-only quote provider with injectable SDK adapter.
- Provider fallback.
- Provider status endpoint.

## Defaults

```text
MARKET_DATA_PROVIDER=mock
EVENT_DATA_PROVIDER=mock
FREE_ONLY_MODE=true
```

## Validation Status

- SEC EDGAR: implemented and tested offline with `httpx.MockTransport`.
- Moomoo quotes: implemented and tested offline with fake adapters.
- Moomoo OpenD: not installed, not started, not probed, not logged in.
- Phase 5B SEC live validation: skipped because `SEC_USER_AGENT` was not configured.
- Phase 5B Moomoo live validation: unavailable; no quote context was opened and no snapshot was requested.
- Phase 5C Moomoo runtime isolation: implemented and tested offline.
- Phase 5D SEC live smoke: completed with AAPL only and without saving full SEC responses.
- Phase 5D Moomoo live smoke: completed with one local read-only `US.AAPL` snapshot check and without outputting real prices.
- Phase 6A live E2E: completed once for AAPL only, with redacted API output and local archive verification.
- Phase 6B watchlist live refresh: completed once, using enabled local watchlist symbols with fallback to AAPL.
- Default pipeline validation: completed with Mock providers.

## Boundaries

- No trading.
- No account reads.
- No holdings or asset queries.
- No paid providers.
- No news scraping.
- No SEC live requests in Phase 3A.
- No connection to `127.0.0.1:11111` in Phase 3A.
- No SEC response bodies, real prices, emails, account data, or Moomoo user data are stored by Phase 5B validation.
- Moomoo SDK runtime files must stay under project runtime storage and fall back to Mock if SDK logging is blocked.
- Phase 5D does not change default providers; normal tests and pipeline validation remain Mock-first and offline.
- Phase 6A live E2E is manual, single-symbol, and one-shot. It does not start a scheduler, expose real prices in the response, or read any account data.
- Phase 6B watchlist refresh is manual and one-shot. It accepts no external symbol list and processes at most 5 supported local watchlist symbols.
