import SwiftUI

struct LiveRefreshView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            List {
                Section {
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
                }

                Section {
                    Button {
                        Task {
                            await store.runLiveWatchlistRefresh()
                        }
                    } label: {
                        Label(buttonTitle, systemImage: "arrow.clockwise.circle")
                    }
                    .disabled(store.liveRefreshState == .loading)

                    Text("Runs one local watchlist refresh through the local API. No system notifications, account reads, or trades are performed.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } header: {
                    Text("Manual Live Refresh")
                }

                if let result = store.liveRefreshResult {
                    Section {
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
                    } header: {
                        Text("Live Summary")
                    }
                }

                if let history = store.liveHistorySnapshot {
                    Section {
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
                    } header: {
                        Text("History Verification")
                    } footer: {
                        Text("Quote history is shown only as row count, symbol, and timestamp. Prices are intentionally not displayed here.")
                    }
                }

                if case .error(let message) = store.liveRefreshState {
                    Section {
                        Text(message)
                            .foregroundStyle(.red)
                    }
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
    }
}

struct LiveRefreshView_Previews: PreviewProvider {
    static var previews: some View {
        LiveRefreshView(store: MarketDataStore())
    }
}
