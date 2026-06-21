# Product Spec

## User Profile

Single user, personal use. The user wants a compact iPhone view for market snapshots, watchlist movement, and important market events.

## Core Scenarios

- Open the app and quickly scan major market conditions.
- Check watchlist price movement and whether displayed data is delayed.
- Review important company, macro, filing, earnings, guidance, dividend, buyback, management, price spike, and volume spike events.
- Read daily pre-market and close reports.
- In future phases, receive major event notifications.

## Dashboard

The Dashboard shows market indices, a market overview, quick watchlist rows, a major event timeline, Mock data warnings, timestamps, delay status, and the disclaimer `仅供信息展示，不构成投资建议。`

## Watchlist

The Watchlist focuses on symbols selected by the user. Phase 1 uses static Mock symbols only.

## Event Timeline

Events are displayed as cards with title, summary, affected symbols, importance score, event type, publish time, sentiment, and Mock data label.

## Daily Reports

Phase 1 includes one Mock pre-market report and one Mock close report for static display.

## Notifications

Future design only. Notifications may later alert on major events after provider authorization, scoring rules, and APNs safety review.

## Non-Functional Requirements

- Clear security boundaries.
- No real credentials in the repository.
- High information density without copying third-party app designs.
- Mock data must be clearly labeled.
- User-visible market data must show timestamp and delay status.

## Phase 1 Non-Goals

- Real market data.
- Real news.
- Trading.
- Broker account login.
- User authentication.
- Database persistence.
- Push notification delivery.
- AI summaries.
