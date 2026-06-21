# Phase 4B Storage

Phase 4B implements local historical storage, report archiving, and local watchlist management.

## Implemented

- Repository protocols.
- Memory repository factory for tests.
- SQLite repositories.
- Archive service.
- Storage status API.
- Retention preview API.
- Quote history API.
- Event history API.
- Report history API.
- Local watchlist add and remove.

## Not Implemented

- PostgreSQL.
- Redis.
- Cloud sync.
- Multi-user accounts.
- Broker watchlist sync.
- Automatic data deletion.
- Trading.
- SEC live validation.
- Moomoo OpenD validation.

## Idempotency

- Quotes deduplicate by symbol, provider, and source timestamp.
- Events deduplicate by a content hash over metadata and affected symbols.
- Reports deduplicate by report type, report date, and stable content hash.
- Watchlist symbols are unique and limited to 100 enabled items.
