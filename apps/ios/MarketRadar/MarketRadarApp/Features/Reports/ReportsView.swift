import SwiftUI

struct ReportsView: View {
    @ObservedObject var store: MarketDataStore
    private let service = MockMarketService()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
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
                        Text("归档：\(storage.reportsCount) 份报告 · \(storage.databaseLocationType)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

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
                .padding()
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
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                VStack(alignment: .leading) {
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
            }

            if !report.marketMoveAlerts.isEmpty {
                Text("规则异动")
                    .font(.subheadline.weight(.semibold))
                ForEach(report.marketMoveAlerts) { alert in
                    Text(alert.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(12)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: RadarTheme.cardRadius))
    }
}

private struct LegacyReportCard: View {
    let report: DailyReport

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                VStack(alignment: .leading) {
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
            }
        }
        .padding(12)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: RadarTheme.cardRadius))
    }
}
