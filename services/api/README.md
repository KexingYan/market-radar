# Market Radar API

Phase 1 FastAPI skeleton.

## Current Behavior

- Uses `MockMarketDataProvider` only.
- Reads local Mock JSON files from `app/mock_data/`.
- Does not access databases, Redis, network services, brokers, news providers, or AI APIs.
- Does not implement login, accounts, holdings, orders, or trading.

## Declared Dependencies

Dependencies are declared in `pyproject.toml` for future use. Do not install them automatically in Phase 1.

## Disclaimer

All returned data is Mock demonstration data and does not represent real market prices. It is for information display only and does not constitute investment advice.
