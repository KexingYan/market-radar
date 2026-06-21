import SwiftUI

struct DashboardView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: RadarTheme.sectionSpacing) {
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

                    if let summary = store.alertSummary {
                        HStack {
                            Label("Alerts \(summary.new)", systemImage: "bell.badge")
                            Spacer()
                            Text("High/Critical \(summary.highOrCritical)")
                        }
                        .font(.subheadline.weight(.semibold))
                        .padding(12)
                        .background(Color(.secondarySystemBackground))
                        .clipShape(RoundedRectangle(cornerRadius: RadarTheme.cardRadius))
                    }

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) {
                            ForEach(store.indices) { quote in
                                MarketIndexTile(quote: quote)
                            }
                        }
                        .padding(.vertical, 2)
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("今日市场概览")
                                .font(.headline)
                            Spacer()
                            MockBadge()
                        }
                        Text("当前为 Mock 演示数据，不代表真实市场价格。指数和自选股仅用于验证布局、信息密度和风险提示。")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding(12)
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: RadarTheme.cardRadius))

                    SectionHeader(title: "自选股快速列表")
                    VStack(spacing: 0) {
                        ForEach(store.watchlist.prefix(4)) { quote in
                            QuoteRow(quote: quote)
                            Divider()
                        }
                    }

                    SectionHeader(title: "重大事件时间线")
                    ForEach(store.events) { event in
                        EventCard(event: event)
                    }
                }
                .padding()
            }
            .navigationTitle("Market Radar")
        }
    }
}

private struct MarketIndexTile: View {
    let quote: QuoteSnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(quote.displayName)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(quote.price.radarString)
                .font(.headline)
            Text("\(quote.changePercent.radarString)% · 延迟")
                .font(.caption.weight(.semibold))
                .foregroundStyle(quote.change >= 0 ? .green : .red)
        }
        .frame(width: 150, alignment: .leading)
        .padding(12)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: RadarTheme.cardRadius))
    }
}

private struct SectionHeader: View {
    let title: String

    var body: some View {
        Text(title)
            .font(.headline)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct DashboardView_Previews: PreviewProvider {
    static var previews: some View {
        DashboardView(store: MarketDataStore())
    }
}
