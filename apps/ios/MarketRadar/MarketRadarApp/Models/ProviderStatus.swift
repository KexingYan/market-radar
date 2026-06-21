import Foundation

struct ProviderStatusResponse: Codable {
    let freeOnlyMode: Bool
    let quotes: ProviderStatus
    let events: ProviderStatus
    let tradingEnabled: Bool
    let paidDataEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case freeOnlyMode = "free_only_mode"
        case quotes
        case events
        case tradingEnabled = "trading_enabled"
        case paidDataEnabled = "paid_data_enabled"
    }
}

struct ProviderStatus: Codable {
    let configured: String
    let active: String
    let available: Bool
    let reason: String?
}
