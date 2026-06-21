# Phase 5D Live Smoke Validation

Phase 5D performs tightly scoped live smoke validation for free, read-only providers.

## SEC User-Agent

- SEC_USER_AGENT configured from project-local runtime file: yes.
- Storage location type: project_runtime.
- Stored in Git-tracked file: no.
- Printed full email: no.
- Saved full email to docs: no.
- Saved full email to code: no.

## SEC EDGAR Smoke Result

- Symbols: AAPL only.
- SEC request count: 2.
- AAPL mapping found: yes.
- AAPL CIK valid: yes.
- Submissions JSON valid: yes.
- MarketEvent conversion: yes.
- Fallback used: no.
- Full SEC response saved: no.

## Moomoo Local OpenD Smoke Result

- Target: local OpenD only.
- Symbol: `US.AAPL` only.
- OpenD reachable: yes.
- Quote context opened: yes.
- Snapshot returned: yes.
- Quote context closed: yes.
- Fallback used: no.
- Real price output: no.
- Account read: no.
- Holdings or assets queried: no.
- Orders or trades queried: no.

## Defaults

Default project configuration remains:

```text
MARKET_DATA_PROVIDER=mock
EVENT_DATA_PROVIDER=mock
FREE_ONLY_MODE=true
```

Offline regression tests remain the default validation path and must not access SEC or OpenD.
