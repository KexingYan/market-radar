import Foundation

struct LiveRefreshResponse: Codable {
    let symbols: [String]
    let fallbackSymbolUsed: Bool
    let sec: LiveSECSummary
    let moomoo: LiveMoomooSummary
    let quoteArchive: LiveArchiveSummary
    let eventArchive: LiveArchiveSummary
    let report: LiveReportSummary
    let alerts: LiveAlertSummary
    let jobRun: LiveJobRunSummary
    let tradingEnabled: Bool
    let paidDataEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case symbols
        case fallbackSymbolUsed = "fallback_symbol_used"
        case sec
        case moomoo
        case quoteArchive = "quote_archive"
        case eventArchive = "event_archive"
        case report
        case alerts
        case jobRun = "job_run"
        case tradingEnabled = "trading_enabled"
        case paidDataEnabled = "paid_data_enabled"
    }
}

struct LiveSECSummary: Codable {
    let attempted: Bool
    let success: Bool
    let requestCount: Int
    let filingsParsed: Int
    let fallbackUsed: Bool

    enum CodingKeys: String, CodingKey {
        case attempted
        case success
        case requestCount = "request_count"
        case filingsParsed = "filings_parsed"
        case fallbackUsed = "fallback_used"
    }
}

struct LiveMoomooSummary: Codable {
    let attempted: Bool
    let success: Bool
    let snapshotRows: Int
    let quoteContextClosed: Bool
    let fallbackUsed: Bool

    enum CodingKeys: String, CodingKey {
        case attempted
        case success
        case snapshotRows = "snapshot_rows"
        case quoteContextClosed = "quote_context_closed"
        case fallbackUsed = "fallback_used"
    }
}

struct LiveArchiveSummary: Codable {
    let inserted: Int
    let duplicates: Int
    let failed: Int
}

struct LiveReportSummary: Codable {
    let generated: Bool
    let archived: Int
    let duplicate: Int
    let failed: Int
}

struct LiveAlertSummary: Codable {
    let evaluatedRules: Int
    let evaluatedSymbols: Int
    let createdAlerts: Int
    let duplicateAlerts: Int
    let cooldownSuppressed: Int
    let mockDataUsed: Bool

    enum CodingKeys: String, CodingKey {
        case evaluatedRules = "evaluated_rules"
        case evaluatedSymbols = "evaluated_symbols"
        case createdAlerts = "created_alerts"
        case duplicateAlerts = "duplicate_alerts"
        case cooldownSuppressed = "cooldown_suppressed"
        case mockDataUsed = "mock_data_used"
    }
}

struct LiveJobRunSummary: Codable {
    let saved: Bool
    let status: String
}

struct LiveHistorySnapshot {
    let quoteRows: Int
    let quoteSymbols: [String]
    let quoteTimestamps: [String]
    let eventRows: Int
    let reportRows: Int
    let alertSummary: AlertSummary?
    let jobRunRows: Int
}

enum LiveRefreshViewState: Equatable {
    case idle
    case loading
    case loaded
    case error(String)
}
