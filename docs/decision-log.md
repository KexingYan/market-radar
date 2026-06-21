# Decision Log

## 2026-06-19: Phase 1 Uses Mock Data Only

Decision: Use local Mock JSON and static SwiftUI data only.

Reason: Establish product direction, safety boundaries, and UI/API shape without touching real accounts, licensed data, or network services.

## 2026-06-19: Provider Abstraction Before Real Providers

Decision: Define a provider protocol and implement only `MockMarketDataProvider`.

Reason: Future providers can be added behind a stable boundary after authorization and security review.

## 2026-06-19: No Trading Scope

Decision: Exclude trading, account reads, holdings, balances, order history, and investment recommendations.

Reason: This app is for information display only and must not handle brokerage authority in Phase 1.
