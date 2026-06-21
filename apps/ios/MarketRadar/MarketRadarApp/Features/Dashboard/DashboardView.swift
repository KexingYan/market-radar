import SwiftUI

struct DashboardView: View {
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

                DashboardHero(store: store)

                RadarSectionHeader(
                    title: "Market Tape",
                    subtitle: "Mock-safe quote surface with source and freshness visible."
                )
                ScrollView(.horizontal, showsIndicators: false) {
                    LazyHStack(spacing: 10) {
                        ForEach(store.indices) { quote in
                            MarketIndexTile(quote: quote)
                        }
                    }
                    .padding(.vertical, 2)
                }
                .accessibilityLabel("Market index cards")

                RadarSectionHeader(title: "Watchlist", subtitle: "Local-only symbols, no holdings or account data.")
                if store.watchlist.isEmpty {
                    RadarEmptyState(title: "No Watchlist Rows", message: "Local watchlist data will appear here after the Mock API or bundled fallback loads.", systemImage: "star")
                } else {
                    RadarCard {
                        ForEach(watchlistPreview) { quote in
                            QuoteRow(quote: quote)
                            if quote.id != watchlistPreview.last?.id {
                                Divider()
                            }
                        }
                    }
                }

                RadarSectionHeader(title: "Event Timeline", subtitle: "Regulatory filings and mock events are labeled by source.")
                if store.events.isEmpty {
                    RadarEmptyState(title: "No Events", message: "Major filings and local mock events will appear here.", systemImage: "bolt")
                } else {
                    ForEach(store.events) { event in
                        EventCard(event: event)
                    }
                }
            }
            .navigationTitle("Market Radar")
        }
    }

    private var watchlistPreview: [QuoteSnapshot] {
        Array(store.watchlist.prefix(4))
    }
}

private struct DashboardHero: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        RadarCard {
            HStack(alignment: .top, spacing: 12) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Command Center")
                        .font(.title2.weight(.semibold))
                    Text("Live readiness, mock fallback, alerts, and data freshness in one place.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                Spacer()
                RadarStatusChip(
                    title: store.dataSourceState.rawValue,
                    systemImage: "waveform.path.ecg",
                    tint: RadarTheme.sourceTint(for: store.dataSourceState)
                )
            }

            HStack(spacing: 10) {
                RadarMetricTile(
                    title: "Watchlist",
                    value: "\(store.watchlist.count)",
                    detail: "local rows",
                    tint: RadarTheme.accent,
                    systemImage: "star.fill"
                )
                RadarMetricTile(
                    title: "Events",
                    value: "\(store.events.count)",
                    detail: "timeline",
                    tint: RadarTheme.purple,
                    systemImage: "bolt.fill"
                )
            }

            if let summary = store.alertSummary {
                HStack(spacing: 8) {
                    RadarStatusChip(title: "New \(summary.new)", systemImage: "tray.full", tint: RadarTheme.warning)
                    RadarStatusChip(title: "High/Critical \(summary.highOrCritical)", systemImage: "exclamationmark.triangle", tint: RadarTheme.negative)
                }
                .accessibilityElement(children: .combine)
            }
        }
    }
}

private struct MarketIndexTile: View {
    let quote: QuoteSnapshot

    var body: some View {
        RadarCard {
            Text(quote.displayName)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(quote.price.radarString)
                .font(.headline)
                .monospacedDigit()
            Text("\(quote.changePercent.radarString)% · 延迟")
                .font(.caption.weight(.semibold))
                .foregroundStyle(quote.change >= 0 ? RadarTheme.positive : RadarTheme.negative)
        }
        .frame(width: 150, alignment: .leading)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(quote.displayName), \(quote.price.radarString), change \(quote.changePercent.radarString) percent, delayed")
    }
}

struct DashboardView_Previews: PreviewProvider {
    static var previews: some View {
        DashboardView(store: MarketDataStore())
    }
}
