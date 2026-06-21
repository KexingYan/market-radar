import Foundation

struct MarketReport: Identifiable, Codable {
    let id: String
    let reportType: String
    let title: String
    let generatedAt: String
    let dataSource: String
    let summary: String
    let keyPoints: [String]
    let eventGroups: [String: [EventDigestItem]]
    let marketMoveAlerts: [MarketMoveAlert]
    let disclaimer: String
    let isMock: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case reportType = "report_type"
        case title
        case generatedAt = "generated_at"
        case dataSource = "data_source"
        case summary
        case keyPoints = "key_points"
        case eventGroups = "event_groups"
        case marketMoveAlerts = "market_move_alerts"
        case disclaimer
        case isMock = "is_mock"
    }
}

struct EventDigestItem: Identifiable, Codable {
    let id: String
    let title: String
    let eventType: String
    let sourceName: String
    let affectedSymbols: [String]
    let importanceScore: Int
    let group: String
    let publishedAt: String
    let isMock: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case eventType = "event_type"
        case sourceName = "source_name"
        case affectedSymbols = "affected_symbols"
        case importanceScore = "importance_score"
        case group
        case publishedAt = "published_at"
        case isMock = "is_mock"
    }
}

struct MarketMoveAlert: Identifiable, Codable {
    var id: String { "\(symbol)-\(alertType)" }
    let symbol: String
    let displayName: String
    let alertType: String
    let description: String
    let changePercent: Double
    let volumeRatio: Double?

    enum CodingKeys: String, CodingKey {
        case symbol
        case displayName = "display_name"
        case alertType = "alert_type"
        case description
        case changePercent = "change_percent"
        case volumeRatio = "volume_ratio"
    }
}
