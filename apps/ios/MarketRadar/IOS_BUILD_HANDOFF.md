# iOS Build Handoff

Current environment: Windows. This environment cannot run Xcode or compile an iOS SwiftUI application.

## Current Status

- SwiftUI implementation exists under `MarketRadarApp/`.
- Local Mock API client exists in `MarketRadarApp/Services/APIClient.swift`.
- Bundled Mock fallback exists in `MarketRadarApp/Services/MarketDataStore.swift`.
- Provider status model exists in `MarketRadarApp/Models/ProviderStatus.swift`.
- Data source states include `Local Mock API`, `Bundled Mock Fallback`, `Free Moomoo Quotes`, and `SEC EDGAR`.
- No `.xcodeproj`, `.xcworkspace`, or `Package.swift` exists in this repository.
- Build validation is pending on macOS with Xcode.

## App Target Files

Add these files to the app target:

- `MarketRadarApp/MarketRadarApp.swift`
- `MarketRadarApp/ContentView.swift`
- `MarketRadarApp/Models/*.swift`
- `MarketRadarApp/MockData/*.swift`
- `MarketRadarApp/Services/*.swift`
- `MarketRadarApp/Features/**/*.swift`
- `MarketRadarApp/Components/*.swift`
- `MarketRadarApp/DesignSystem/*.swift`

Current source structure:

- `MarketRadarApp/Models/` contains quote, event, report, storage, alert, automation, provider status, and live refresh models.
- `MarketRadarApp/Services/` contains `APIClient`, `AppEnvironment`, `MarketDataStore`, and bundled Mock services.
- `MarketRadarApp/Features/` contains Dashboard, Watchlist, Events, Reports, Alerts, Automation, Live Refresh, and Settings views.
- `MarketRadarApp/Components/` contains shared badges, rows, event cards, disclaimers, and data source status UI.
- `MarketRadarApp/DesignSystem/` contains app styling constants.

## Unit Test Target Files

Add these files to the unit test target:

- `Tests/MarketRadarLocalAPITests.swift`

## Suggested Target Settings

- Platform: iOS
- Minimum iOS version: iOS 17 or newer
- Interface: SwiftUI
- Language: Swift
- Signing: disabled for simulator-only local validation

## Local API

The app uses:

```text
http://127.0.0.1:8000
```

This is for iOS Simulator on the same Mac as the FastAPI backend.

Do not replace this with a LAN address in the current phase. A physical iPhone cannot use its own `127.0.0.1` to reach the Mac backend. A future true-device test would require the Mac LAN IP and a deliberate backend LAN binding decision, but this repository currently does not enable LAN service.

## Phase 3A API Additions

Decode and test:

- `/api/v1/providers/status`
- `/api/v1/reports/premarket`
- `/api/v1/reports/intraday`
- `/api/v1/reports/close`
- SEC EDGAR events with `source_name = SEC EDGAR`
- Moomoo quote snapshots with `provider = moomoo`
- fallback to bundled Mock data when the API is unavailable

The UI must distinguish Mock demonstration data, current quote source labels, delayed quotes, and SEC regulatory filings.

## Phase 4A Report UI

The Reports tab source now supports backend `MarketReport` objects with:

- report type
- generated time
- key points
- importance groups
- rule-based market move alerts
- Mock flag and disclaimer

Build validation remains pending on macOS/Xcode.

## Phase 4B Storage UI

The iOS source now includes:

- `StorageStatus`
- `RetentionPreview`
- `StoredReportSummary`
- `LocalWatchlistRequest`
- API calls for storage status, quote history, report history, and local watchlist add/remove

Watchlist source must remain local-only. Do not add holdings, cost basis, buy/sell buttons, broker sync, or account login.

## Phase 4C Alerts UI

The iOS source now includes:

- `Models/AlertModels.swift`
- `Features/Alerts/AlertsView.swift`
- `Features/Alerts/AlertDetailView.swift`
- `Features/Alerts/AlertRuleListView.swift`
- `Features/Alerts/AlertRuleEditorView.swift`
- API calls for `/api/v1/alert-rules`, `/api/v1/alerts`, `/api/v1/alerts/summary`, `/api/v1/alerts/evaluate`, acknowledge, and snooze.
- A Dashboard in-app alert badge sourced from `/api/v1/alerts/summary`.

Phase 4C alert UI is an in-app inbox only. It does not request notification permission, does not implement APNs, does not implement system notifications, does not use device tokens, and does not add a Notification Service Extension.

Build validation remains pending on macOS/Xcode. Notification permission testing is not applicable in Phase 4C because no system notification feature is implemented.

## Phase 5A Automation UI

The iOS source now includes:

- `Models/AutomationModels.swift`
- `Features/Automation/AutomationView.swift`
- `Features/Automation/JobListView.swift`
- `Features/Automation/JobDetailView.swift`
- `Features/Automation/JobRunListView.swift`
- `Features/Automation/JobRunDetailView.swift`
- `Features/Automation/SchedulerStatusView.swift`
- API calls for `/api/v1/jobs`, `/api/v1/job-runs`, `/api/v1/scheduler/status`, manual job run, and manual pipeline run.

Automation UI must display that the scheduler only runs while the local foreground scheduler process is open. It must not imply a background service, scheduled task, startup item, APNs notification, system notification, account access, or trading feature.

Build validation remains pending on macOS/Xcode.

## Phase 5B API Integration Status

The backend Phase 5B validation added no new iOS compile result in the current Windows environment.

For macOS/Xcode follow-up, verify that the existing local API client can display:

- provider status with default `mock` quote and event providers
- Mock full pipeline run status
- job run summaries
- alerts summary after pipeline evaluation
- fallback messaging when the local API is unavailable

Phase 5B does not add real price display requirements, account views, broker login, holdings, assets, orders, system notifications, or trading controls.

Build validation remains pending on macOS/Xcode.

## Phase 7A Live Refresh UI

The iOS source now includes:

- `Models/LiveRefreshModels.swift`
- `Features/Dashboard/LiveRefreshView.swift`
- APIClient calls for:
  - `POST /api/v1/live/watchlist-refresh`
  - `GET /api/v1/history/quotes/AAPL?limit=5`
  - `GET /api/v1/history/events?symbol=AAPL&limit=5`
  - `GET /api/v1/history/reports?report_type=intraday&limit=5`
  - `GET /api/v1/alerts/summary`
  - `GET /api/v1/job-runs?limit=5`
  - `GET /api/v1/providers/status`
- A Live tab with a manual `Run Live Refresh` button.
- Loading, success, and error states.
- Redacted result display for processed symbols, SEC status, Moomoo status, snapshot row count, archive counts, report status, alert status, and job run status.

The Live tab does not display real quote prices. Quote history is shown only as row count, symbol, and timestamp. The UI does not add APNs, system notifications, background refresh, account views, holdings, assets, orders, or trading controls.

Build validation remains pending on macOS/Xcode. On a Mac, add the new files above to the app target and run simulator build plus decoding tests for `LiveRefreshResponse` and `JobRun.resultSummary`.

## Phase 7B Build Readiness

Static source review completed on Windows:

- `MarketRadarApp.swift` is the app entry point.
- `ContentView.swift` owns the root `TabView`.
- `MarketDataStore` remains the single observable app data store.
- `APIClient` uses the local base URL and async/await.
- `LiveRefreshResponse` matches the redacted backend response shape.
- `JobRun.resultSummary` can decode nested dictionaries and arrays.
- The Live Refresh UI does not display real quote prices.
- Mock fallback remains in `MarketDataStore.load()`.

No duplicate public Swift type names were found in the source tree. No Xcode project, workspace, or Swift Package manifest exists in this repository, so build validation remains pending.

Recommended Mac validation:

1. Create a new iOS App project in Xcode named `MarketRadar`.
2. Use SwiftUI lifecycle and Swift language.
3. Set minimum deployment target to iOS 17 or newer.
4. Add every file under `MarketRadarApp/` to the app target.
5. Add `Tests/MarketRadarLocalAPITests.swift` to the unit test target.
6. Keep signing disabled for simulator-only validation.
7. Add localhost-only networking support if needed with `NSAllowsLocalNetworking`.
8. Do not add `NSAllowsArbitraryLoads`.
9. Start FastAPI on `127.0.0.1:8000`.
10. Run the app in iOS Simulator.
11. Run unit tests for quote/event/provider/live refresh/job run decoding and bundled Mock fallback.

Expected manual checks:

- App launches into the tab layout.
- Bundled Mock fallback works with the backend stopped.
- Provider status loads with backend running.
- Live tab can run `POST /api/v1/live/watchlist-refresh`.
- Live tab shows symbols, SEC/Moomoo success flags, snapshot rows, archive counts, alert counts, job run status, history row counts, symbols, and timestamps.
- Live tab does not display real quote prices.
- No APNs, system notification permission, background task, account view, holdings view, assets view, order view, or trading control appears.

## ATS

If Xcode requires an ATS exception, use the smallest localhost-only setting available, such as `NSAllowsLocalNetworking`.

Do not add:

```text
NSAllowsArbitraryLoads = true
```

## Manual Validation Steps on macOS

1. Create a local SwiftUI iOS app project in Xcode.
2. Add the app target files listed above.
3. Add a unit test target and include `MarketRadarLocalAPITests.swift`.
4. Keep signing disabled for simulator-only validation.
5. Start the FastAPI backend on `127.0.0.1:8000`.
6. Run the app in iOS Simulator.
7. Stop the API and confirm the UI shows `Bundled Mock Fallback`.
8. Run unit tests in the simulator.

Do not connect Apple Developer accounts, create certificates, configure provisioning profiles, use real APIs, or upload the app.
