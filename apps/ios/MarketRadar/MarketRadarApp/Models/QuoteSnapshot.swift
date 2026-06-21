import Foundation

struct QuoteSnapshot: Identifiable, Codable {
    var id: String { symbol }
    let symbol: String
    let displayName: String
    let market: String
    let currency: String
    let provider: String
    let price: Decimal
    let previousClose: Decimal
    let change: Decimal
    let changePercent: Decimal
    let volume: Int
    let averageVolume20d: Int
    let marketStatus: String
    let timestamp: String
    let isDelayed: Bool

    enum CodingKeys: String, CodingKey {
        case symbol
        case displayName = "display_name"
        case market
        case currency
        case provider
        case price
        case previousClose = "previous_close"
        case change
        case changePercent = "change_percent"
        case volume
        case averageVolume20d = "average_volume_20d"
        case marketStatus = "market_status"
        case timestamp
        case isDelayed = "is_delayed"
    }
}
