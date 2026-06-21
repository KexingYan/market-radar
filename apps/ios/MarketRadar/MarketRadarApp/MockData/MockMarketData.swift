import Foundation

enum MockMarketData {
    static let disclaimer = "当前为 Mock 演示数据，不代表真实市场价格。仅供信息展示，不构成投资建议。"

    static let indices: [QuoteSnapshot] = [
        QuoteSnapshot(symbol: "MOCK-SPX", displayName: "Mock S&P 500", market: "US", currency: "USD", provider: "mock", price: 4321.10, previousClose: 4300.00, change: 21.10, changePercent: 0.49, volume: 0, averageVolume20d: 0, marketStatus: "mock_closed", timestamp: "2024-01-15 21:00 UTC", isDelayed: true),
        QuoteSnapshot(symbol: "MOCK-NDX", displayName: "Mock Nasdaq 100", market: "US", currency: "USD", provider: "mock", price: 15123.45, previousClose: 15200.00, change: -76.55, changePercent: -0.50, volume: 0, averageVolume20d: 0, marketStatus: "mock_closed", timestamp: "2024-01-15 21:00 UTC", isDelayed: true),
        QuoteSnapshot(symbol: "MOCK-HSI", displayName: "Mock Hang Seng", market: "HK", currency: "HKD", provider: "mock", price: 16888.00, previousClose: 16750.00, change: 138.00, changePercent: 0.82, volume: 0, averageVolume20d: 0, marketStatus: "mock_closed", timestamp: "2024-01-15 08:00 UTC", isDelayed: true),
        QuoteSnapshot(symbol: "MOCK-SSE", displayName: "Mock Shanghai", market: "CN", currency: "CNY", provider: "mock", price: 3012.34, previousClose: 3000.00, change: 12.34, changePercent: 0.41, volume: 0, averageVolume20d: 0, marketStatus: "mock_closed", timestamp: "2024-01-15 07:00 UTC", isDelayed: true)
    ]

    static let watchlist: [QuoteSnapshot] = [
        QuoteSnapshot(symbol: "AAPL", displayName: "Apple Mock", market: "US", currency: "USD", provider: "mock", price: 182.40, previousClose: 181.10, change: 1.30, changePercent: 0.72, volume: 12340000, averageVolume20d: 51100000, marketStatus: "mock_closed", timestamp: "2024-01-15 21:00 UTC", isDelayed: true),
        QuoteSnapshot(symbol: "NVDA", displayName: "NVIDIA Mock", market: "US", currency: "USD", provider: "mock", price: 510.25, previousClose: 520.00, change: -9.75, changePercent: -1.88, volume: 22100000, averageVolume20d: 45500000, marketStatus: "mock_closed", timestamp: "2024-01-15 21:00 UTC", isDelayed: true),
        QuoteSnapshot(symbol: "TSLA", displayName: "Tesla Mock", market: "US", currency: "USD", provider: "mock", price: 211.80, previousClose: 205.50, change: 6.30, changePercent: 3.07, volume: 50100000, averageVolume20d: 88000000, marketStatus: "mock_closed", timestamp: "2024-01-15 21:00 UTC", isDelayed: true),
        QuoteSnapshot(symbol: "MSFT", displayName: "Microsoft Mock", market: "US", currency: "USD", provider: "mock", price: 398.70, previousClose: 399.00, change: -0.30, changePercent: -0.08, volume: 9100000, averageVolume20d: 24000000, marketStatus: "mock_closed", timestamp: "2024-01-15 21:00 UTC", isDelayed: true),
        QuoteSnapshot(symbol: "0700.HK", displayName: "Tencent Mock", market: "HK", currency: "HKD", provider: "mock", price: 302.20, previousClose: 298.00, change: 4.20, changePercent: 1.41, volume: 18000000, averageVolume20d: 26000000, marketStatus: "mock_closed", timestamp: "2024-01-15 08:00 UTC", isDelayed: true),
        QuoteSnapshot(symbol: "000001.SZ", displayName: "Ping An Bank Mock", market: "CN", currency: "CNY", provider: "mock", price: 10.88, previousClose: 10.95, change: -0.07, changePercent: -0.64, volume: 65000000, averageVolume20d: 70000000, marketStatus: "mock_closed", timestamp: "2024-01-15 07:00 UTC", isDelayed: true)
    ]

    static let events: [MarketEvent] = [
        MarketEvent(id: "mock-event-001", eventType: .earnings, title: "演示事件：某科技公司发布虚构季度数据", summary: "用于界面演示的虚构财报事件，不代表真实公司当前业绩。", sourceName: "Mock Data Provider", sourceURL: "mock://events/mock-event-001", publishedAt: "2024-01-15 13:00 UTC", receivedAt: "2024-01-15 13:01 UTC", affectedSymbols: ["AAPL"], importanceScore: 82, reliabilityScore: 100, sentiment: .neutral, confidence: 0.92, isMock: true),
        MarketEvent(id: "mock-event-002", eventType: .guidance, title: "演示事件：虚构管理层调整全年展望", summary: "用于测试指引类事件展示，不构成真实预测或投资建议。", sourceName: "Mock Data Provider", sourceURL: "mock://events/mock-event-002", publishedAt: "2024-01-15 14:10 UTC", receivedAt: "2024-01-15 14:12 UTC", affectedSymbols: ["NVDA", "MSFT"], importanceScore: 76, reliabilityScore: 100, sentiment: .positive, confidence: 0.88, isMock: true),
        MarketEvent(id: "mock-event-003", eventType: .macroEvent, title: "演示事件：虚构宏观数据触发市场关注", summary: "通用宏观事件演示文本，不对应任何真实日期发布的数据。", sourceName: "Mock Data Provider", sourceURL: "mock://events/mock-event-003", publishedAt: "2024-01-15 15:00 UTC", receivedAt: "2024-01-15 15:01 UTC", affectedSymbols: ["MOCK-SPX", "MOCK-NDX"], importanceScore: 68, reliabilityScore: 100, sentiment: .negative, confidence: 0.81, isMock: true)
    ]

    static let reports: [DailyReport] = [
        DailyReport(id: "mock-premarket-2024-01-15", title: "Mock 盘前报告", reportType: "premarket", summary: "这是一份虚构盘前报告，用于验证 Reports 页面布局。", bulletPoints: ["关注 Mock 指数表现", "观察自选股演示波动", "所有内容均为静态演示"], publishedAt: "2024-01-15 12:00 UTC", isMock: true),
        DailyReport(id: "mock-close-2024-01-15", title: "Mock 收盘报告", reportType: "close", summary: "这是一份虚构收盘报告，不代表真实市场复盘。", bulletPoints: ["Mock 事件时间线已更新", "无真实新闻或行情接入", "不构成投资建议"], publishedAt: "2024-01-15 22:00 UTC", isMock: true)
    ]
}
