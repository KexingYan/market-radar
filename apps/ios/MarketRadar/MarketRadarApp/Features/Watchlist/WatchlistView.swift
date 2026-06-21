import SwiftUI

struct WatchlistView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            List {
                Section {
                    DisclaimerView()
                        .listRowInsets(EdgeInsets())
                        .listRowBackground(Color.clear)
                }

                Section("自选股") {
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

                Section("本地管理") {
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
                }
            }
            .navigationTitle("Watchlist")
        }
    }
}

struct WatchlistView_Previews: PreviewProvider {
    static var previews: some View {
        WatchlistView(store: MarketDataStore())
    }
}
