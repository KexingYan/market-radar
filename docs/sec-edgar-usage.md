# SEC EDGAR Usage

Phase 3A implements an SEC EDGAR event provider but defers live SEC validation until the user can safely configure `SEC_USER_AGENT`.

## Supported Forms

- `8-K`
- `10-K`
- `10-Q`
- `6-K`
- `20-F`
- `4`
- `13D`
- `13G`

## Event Conversion

SEC filings become `regulatory_filing` events with:

- `source_name = SEC EDGAR`
- `reliability_score = 100`
- `sentiment = neutral`
- `confidence = 1.0`
- `is_mock = false`

Summaries only describe filing metadata. They do not infer impact, sentiment, investment meaning, or advice.

## Offline Tests

Tests use `httpx.MockTransport`.

No live request is made to `data.sec.gov` or `www.sec.gov` in Phase 3A.

## Future Live Validation

Live use requires a compliant `SEC_USER_AGENT`, rate limiting, and explicit user approval. Do not infer or write a user email address into project files.

## Phase 5B Validation Status

SEC live validation was skipped because `SEC_USER_AGENT` was not configured in the current process.

Recorded result:

- SEC_USER_AGENT present: no.
- SEC request count: 0.
- Ticker mapping request: not executed.
- AAPL submissions request: not executed.
- MarketEvent conversion from live SEC data: not executed.
- Full User-Agent output: no.
- Real email saved: no.
- Full SEC response saved: no.

Default offline tests continue to use `httpx.MockTransport` and must not access SEC.

## Phase 6A Live E2E Status

SEC EDGAR was used for a one-shot AAPL-only live E2E validation.

Recorded result:

- SEC request count: 2.
- AAPL mapping found: yes.
- AAPL CIK valid: yes.
- Submissions JSON valid: yes.
- MarketEvent conversion: yes.
- Full SEC response saved: no.
- Full User-Agent output: no.
- Contact email saved to docs or source: no.

The live E2E endpoint returns counts and success flags only. It does not return full SEC responses or contact details.

## Phase 6B Watchlist Refresh Status

SEC EDGAR was used for a one-shot watchlist refresh validation.

Recorded result:

- Processed symbols source: local enabled watchlist with fixed fallback.
- SEC request count: 2.
- AAPL mapping found: yes.
- Submissions JSON valid: yes.
- MarketEvent conversion: yes.
- Full SEC response saved: no.
- Full User-Agent output: no.
- Contact email saved to docs or source: no.

The watchlist refresh endpoint returns counts and success flags only. It does not return full SEC responses or contact details.
