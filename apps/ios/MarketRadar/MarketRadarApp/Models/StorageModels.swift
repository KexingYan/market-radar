import Foundation

struct StorageStatus: Codable {
    let backend: String
    let databaseReady: Bool
    let databaseLocationType: String
    let quotesCount: Int
    let eventsCount: Int
    let reportsCount: Int
    let watchlistCount: Int
    let alertRulesCount: Int?
    let enabledAlertRulesCount: Int?
    let alertsCount: Int?
    let newAlertsCount: Int?
    let scheduledJobsCount: Int?
    let enabledJobsCount: Int?
    let jobRunsCount: Int?
    let runningJobsCount: Int?
    let failedJobRunsCount: Int?
    let automaticDeletionEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case backend
        case databaseReady = "database_ready"
        case databaseLocationType = "database_location_type"
        case quotesCount = "quotes_count"
        case eventsCount = "events_count"
        case reportsCount = "reports_count"
        case watchlistCount = "watchlist_count"
        case alertRulesCount = "alert_rules_count"
        case enabledAlertRulesCount = "enabled_alert_rules_count"
        case alertsCount = "alerts_count"
        case newAlertsCount = "new_alerts_count"
        case scheduledJobsCount = "scheduled_jobs_count"
        case enabledJobsCount = "enabled_jobs_count"
        case jobRunsCount = "job_runs_count"
        case runningJobsCount = "running_jobs_count"
        case failedJobRunsCount = "failed_job_runs_count"
        case automaticDeletionEnabled = "automatic_deletion_enabled"
    }
}

struct RetentionPreview: Codable {
    let quoteRetentionDays: Int
    let eligibleQuoteRows: Int
    let automaticDeletionEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case quoteRetentionDays = "quote_retention_days"
        case eligibleQuoteRows = "eligible_quote_rows"
        case automaticDeletionEnabled = "automatic_deletion_enabled"
    }
}

struct StoredReportSummary: Identifiable, Codable {
    let id: String
    let reportType: String
    let generatedAt: String
    let isMock: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case reportType = "report_type"
        case generatedAt = "generated_at"
        case isMock = "is_mock"
    }
}

struct LocalWatchlistRequest: Codable {
    let symbol: String
    let displayName: String
    let market: String

    enum CodingKeys: String, CodingKey {
        case symbol
        case displayName = "display_name"
        case market
    }
}
