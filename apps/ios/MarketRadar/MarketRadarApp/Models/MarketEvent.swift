import Foundation

enum EventType: String, Codable {
    case breakingNews = "breaking_news"
    case companyAnnouncement = "company_announcement"
    case earnings
    case guidance
    case macroEvent = "macro_event"
    case priceSpike = "price_spike"
    case volumeSpike = "volume_spike"
    case regulatoryFiling = "regulatory_filing"
    case dividend
    case shareBuyback = "share_buyback"
    case managementChange = "management_change"
}

enum EventSentiment: String, Codable {
    case positive
    case neutral
    case negative
}

struct MarketEvent: Identifiable, Codable {
    let id: String
    let eventType: EventType
    let title: String
    let summary: String
    let sourceName: String
    let sourceURL: String
    let publishedAt: String
    let receivedAt: String
    let affectedSymbols: [String]
    let importanceScore: Int
    let reliabilityScore: Int
    let sentiment: EventSentiment
    let confidence: Double
    let isMock: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case eventType = "event_type"
        case title
        case summary
        case sourceName = "source_name"
        case sourceURL = "source_url"
        case publishedAt = "published_at"
        case receivedAt = "received_at"
        case affectedSymbols = "affected_symbols"
        case importanceScore = "importance_score"
        case reliabilityScore = "reliability_score"
        case sentiment
        case confidence
        case isMock = "is_mock"
    }
}
