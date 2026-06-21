# Contributing

Market Radar is currently a personal research project. Contributions should preserve the Phase 1 safety model.

## Rules

- Keep changes scoped to this repository.
- Do not add real credentials.
- Do not connect real market, broker, news, AI, or account services in Phase 1.
- Do not add trading, order placement, or account access.
- Add or update tests for new API behavior.
- Keep Mock data clearly labeled.

## Development

Dependency declarations are included for future setup, but Phase 1 does not install dependencies automatically.

## Review Checklist

- No secrets or account information.
- No live API calls.
- No destructive scripts.
- No user tracking or telemetry.
- User-visible financial data includes timestamp and delay status.
- Screens include the disclaimer: `仅供信息展示，不构成投资建议。`
