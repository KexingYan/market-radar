import SwiftUI

struct WatchlistView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            List {
                DisclaimerView()
                    .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                    .listRowBackground(Color.clear)

                Section {
                    if store.watchlist.isEmpty {
                        RadarEmptyState(title: "No Local Symbols", message: "Add AAPL to seed the local-only watchlist.", systemImage: "star")
                            .listRowBackground(Color.clear)
                    } else {
                        ForEach(store.watchlist) { quote in
                            QuoteRow(quote: quote)
                                .swipeActions {
                                    Button(role: .destructive) {
                                        Task {
                                            await store.removeLocalWatchlist(symbol: quote.symbol)
                                        }
                                    } label: {
                                        Label("删除", systemImage: "trash")
                                    }
                                }
                        }
                    }
                } header: {
                    Text("自选股")
                }

                Section {
                    Button {
                        Task {
                            await store.addLocalWatchlist(symbol: "AAPL", displayName: "Apple", market: "US")
                        }
                    } label: {
                        Label("添加 AAPL", systemImage: "plus.circle")
                    }
                    Text("仅修改本地自选股，不连接券商账户，不展示持仓、成本或买卖按钮。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } header: {
                    Text("本地管理")
                }
            }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
            .background(RadarTheme.pageBackground)
            .navigationTitle("Watchlist")
        }
    }
}

struct WatchlistView_Previews: PreviewProvider {
    static var previews: some View {
        WatchlistView(store: MarketDataStore())
    }
}
