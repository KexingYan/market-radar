import SwiftUI

struct ReportsView: View {
    @ObservedObject var store: MarketDataStore
    private let service = MockMarketService()

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

                if let storage = store.storageStatus {
                    RadarCard {
                        HStack(spacing: 10) {
                            Image(systemName: "archivebox")
                                .foregroundStyle(RadarTheme.purple)
                                .accessibilityHidden(true)
                            VStack(alignment: .leading, spacing: 3) {
                                Text("Report Archive")
                                    .font(.subheadline.weight(.semibold))
                                Text("\(storage.reportsCount) reports · \(storage.databaseLocationType)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                        }
                        .accessibilityElement(children: .combine)
                    }
                }

                RadarSectionHeader(
                    title: "Daily Reports",
                    subtitle: store.reports.isEmpty ? "Mock fallback is active until archived reports are available." : "Generated market notes and rule-trigger context."
                )

                if store.reports.isEmpty {
                    ForEach(service.reports()) { report in
                        LegacyReportCard(report: report)
                    }
                } else {
                    ForEach(store.reports) { report in
                        MarketReportCard(report: report)
                    }
                }
            }
            .navigationTitle("Reports")
        }
    }
}

struct ReportsView_Previews: PreviewProvider {
    static var previews: some View {
        ReportsView(store: MarketDataStore())
    }
}

private struct MarketReportCard: View {
    let report: MarketReport

    var body: some View {
        RadarCard {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(report.title)
                        .font(.headline)
                    Text(report.generatedAt)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                if report.isMock {
                    MockBadge()
                }
            }

            Text(report.summary)
                .font(.subheadline)
                .foregroundStyle(.secondary)

            ForEach(report.keyPoints, id: \.self) { item in
                Label(item, systemImage: "checkmark.circle")
                    .font(.subheadline)
                    .foregroundStyle(.primary)
            }

            if !report.marketMoveAlerts.isEmpty {
                Text("Rule Movement")
                    .font(.subheadline.weight(.semibold))
                ForEach(report.marketMoveAlerts) { alert in
                    Text(alert.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .accessibilityElement(children: .combine)
    }
}

private struct LegacyReportCard: View {
    let report: DailyReport

    var body: some View {
        RadarCard {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(report.title)
                        .font(.headline)
                    Text(report.publishedAt)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                MockBadge()
            }
            Text(report.summary)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            ForEach(report.bulletPoints, id: \.self) { item in
                Label(item, systemImage: "checkmark.circle")
                    .font(.subheadline)
                    .foregroundStyle(.primary)
            }
        }
        .accessibilityElement(children: .combine)
    }
}
