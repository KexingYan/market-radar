import SwiftUI

struct LiveRefreshView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            RadarPage {
                DisclaimerView()
                DataSourceStatusView(
                    state: store.dataSourceState,
                    message: store.lastErrorMessage,
                    refresh: {
                        Task {
                            await store.load()
                        }
                    }
                )

                RadarCard {
                    HStack(alignment: .top, spacing: 12) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Manual Live Refresh")
                                .font(.title3.weight(.semibold))
                            Text("One-shot local watchlist refresh. Results are redacted: prices, account data, holdings, assets, and orders are not displayed.")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                        Spacer()
                        RadarStatusChip(title: liveStateLabel, systemImage: liveStateIcon, tint: liveStateTint)
                    }

                    Button {
                        Task {
                            await store.runLiveWatchlistRefresh()
                        }
                    } label: {
                        Label(buttonTitle, systemImage: "arrow.clockwise.circle")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(store.liveRefreshState == .loading)
                    .accessibilityHint("Runs the local watchlist refresh endpoint once.")
                }

                if store.liveRefreshState == .loading {
                    RadarLoadingState(title: "Running local refresh...")
                }

                Section("Backend Diagnostics") {
                    StatusRow(title: "Backend mode", value: store.liveRefreshDiagnostics.backendMode)
                    StatusRow(title: "Base URL", value: store.liveRefreshDiagnostics.baseURL)
                    StatusRow(title: "Endpoint", value: store.liveRefreshDiagnostics.endpoint)
                    StatusRow(
                        title: "Status",
                        value: store.liveRefreshDiagnostics.httpStatus.map(String.init) ?? "not requested"
                    )
                    StatusRow(title: "Provider", value: providerSummary)
                    if let fallbackReason = store.liveRefreshDiagnostics.fallbackReason {
                        StatusRow(title: "Fallback reason", value: fallbackReason)
                    }
                    if let lastError = store.liveRefreshDiagnostics.lastError {
                        Text(lastError)
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }

                if let result = store.liveRefreshResult {
                    RadarSectionHeader(title: "Live Summary", subtitle: "Provider results and archive counts only.")
                    RadarCard {
                        StatusRow(title: "Processed symbols", value: result.symbols.joined(separator: ", "))
                        StatusRow(title: "Watchlist fallback AAPL", value: result.fallbackSymbolUsed ? "yes" : "no")
                        StatusRow(title: "SEC success", value: result.sec.success ? "yes" : "no")
                        StatusRow(title: "SEC requests", value: "\(result.sec.requestCount)")
                        StatusRow(title: "SEC filings parsed", value: "\(result.sec.filingsParsed)")
                        StatusRow(title: "Moomoo success", value: result.moomoo.success ? "yes" : "no")
                        StatusRow(title: "Snapshot rows", value: "\(result.moomoo.snapshotRows)")
                        StatusRow(title: "Quote context closed", value: result.moomoo.quoteContextClosed ? "yes" : "no")
                        StatusRow(title: "Quotes archived", value: "\(result.quoteArchive.inserted) new / \(result.quoteArchive.duplicates) duplicate")
                        StatusRow(title: "Events archived", value: "\(result.eventArchive.inserted) new / \(result.eventArchive.duplicates) duplicate")
                        StatusRow(title: "Report archived", value: result.report.generated ? "yes" : "no")
                        StatusRow(title: "Alerts created", value: "\(result.alerts.createdAlerts)")
                        StatusRow(title: "Job run", value: result.jobRun.status)
                    }
                }

                if let history = store.liveHistorySnapshot {
                    RadarSectionHeader(title: "History Verification", subtitle: "Quote prices are intentionally hidden on this page.")
                    RadarCard {
                        StatusRow(title: "Quote rows", value: "\(history.quoteRows)")
                        if let symbol = history.quoteSymbols.first {
                            StatusRow(title: "Latest quote symbol", value: symbol)
                        }
                        if let timestamp = history.quoteTimestamps.first {
                            StatusRow(title: "Latest quote timestamp", value: timestamp)
                        }
                        StatusRow(title: "Event rows", value: "\(history.eventRows)")
                        StatusRow(title: "Intraday report rows", value: "\(history.reportRows)")
                        StatusRow(title: "Job run rows", value: "\(history.jobRunRows)")
                        if let summary = history.alertSummary {
                            StatusRow(title: "New alerts", value: "\(summary.new)")
                            StatusRow(title: "High/Critical alerts", value: "\(summary.highOrCritical)")
                        }
                    }
                }

                if case .error(let message) = store.liveRefreshState {
                    RadarCard {
                        RadarStatusChip(title: "Refresh failed", systemImage: "exclamationmark.triangle", tint: RadarTheme.negative)
                        Text(message)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .accessibilityLabel("Refresh failed. \(message)")
                }
            }
            .navigationTitle("Live Refresh")
        }
    }

    private var buttonTitle: String {
        switch store.liveRefreshState {
        case .loading:
            return "Running..."
        case .loaded:
            return "Run Live Refresh Again"
        default:
            return "Run Live Refresh"
        }
    }

    private var liveStateLabel: String {
        switch store.liveRefreshState {
        case .idle:
            return "Ready"
        case .loading:
            return "Running"
        case .loaded:
            return "Complete"
        case .error:
            return "Error"
        }
    }

    private var liveStateIcon: String {
        switch store.liveRefreshState {
        case .idle:
            return "pause.circle"
        case .loading:
            return "arrow.triangle.2.circlepath"
        case .loaded:
            return "checkmark.circle"
        case .error:
            return "exclamationmark.triangle"
        }
    }

    private var liveStateTint: Color {
        switch store.liveRefreshState {
        case .idle:
            return RadarTheme.accent
        case .loading:
            return RadarTheme.purple
        case .loaded:
            return RadarTheme.positive
        case .error:
            return RadarTheme.negative
        }
    }

    private var providerSummary: String {
        guard let status = store.providerStatus else {
            return "not loaded"
        }
        return "quotes configured=\(status.quotes.configured), active=\(status.quotes.active)"
    }
}

private struct StatusRow: View {
    let title: String
    let value: String

    var body: some View {
        HStack {
            Text(title)
            Spacer()
            Text(value)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.trailing)
        }
        .font(.subheadline)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(title), \(value)")
    }
}

struct LiveRefreshView_Previews: PreviewProvider {
    static var previews: some View {
        LiveRefreshView(store: MarketDataStore())
    }
}
