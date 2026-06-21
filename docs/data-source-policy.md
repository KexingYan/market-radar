# Data Source Policy

## Phase 3A Current Phase

- Mock Provider remains the default.
- SEC EDGAR Provider is implemented and tested offline.
- Moomoo read-only Quote Provider is implemented and tested offline.
- Do not access Futu OpenD or Moomoo OpenD without a separate Phase 3B approval.
- Do not access iFinD.
- Do not access Bloomberg.
- Do not scrape news websites.
- Do not scrape broker apps.
- Do not reverse engineer client APIs.
- Do not bypass paywalls.
- Do not bypass market data authorization.
- Do not share, resell, or publicly distribute market data with restricted authorization.

Phase 3A does not perform live SEC requests and does not connect to `127.0.0.1:11111`.

## Future Real Data Source Requirements

Before adding any real provider:

- Review official API documentation and terms.
- Use legally authorized accounts.
- Confirm whether data may be stored.
- Confirm whether data may be displayed.
- Confirm whether data may be pushed as notifications.
- Confirm whether derivative analysis is allowed.
- Set rate limits.
- Set data retention periods.
- Store credentials on the server.
- Do not put credentials in the app.
- Do not commit credentials to Git.
