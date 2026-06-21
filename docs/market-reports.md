# Offline Market Reports

Phase 4A adds deterministic market reports built only from existing `QuoteSnapshot` and `MarketEvent` data.

## Implemented Reports

- Premarket report: `/api/v1/reports/premarket`
- Intraday major event digest: `/api/v1/reports/intraday`
- Close report: `/api/v1/reports/close`

## Rules

- Events are sorted by importance, publish time, and ID.
- Duplicate events are collapsed by event type, title, and affected symbols.
- Importance groups:
  - `critical`: 85-100
  - `high`: 70-84
  - `medium`: 50-69
  - `low`: 0-49
- Price move alert: absolute change percentage at least 3%.
- Volume move alert: current volume at least 1.5 times 20-day average volume.

## Boundaries

- No AI.
- No investment advice.
- No target prices.
- No trading signals.
- No real network requests.
- No database or cache service.
- No SEC live validation.
- No Moomoo OpenD connection.
