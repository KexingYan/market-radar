import Foundation

struct MockMarketService {
    func indices() -> [QuoteSnapshot] {
        MockMarketData.indices
    }

    func watchlist() -> [QuoteSnapshot] {
        MockMarketData.watchlist
    }

    func events() -> [MarketEvent] {
        MockMarketData.events
    }

    func reports() -> [DailyReport] {
        MockMarketData.reports
    }
}
