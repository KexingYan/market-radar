import Foundation

struct AlertRule: Identifiable, Codable {
    let id: String
    let name: String
    let ruleType: String
    let severity: String
    let symbolScope: String
    let symbols: [String]
    let isEnabled: Bool
    let cooldownSeconds: Int
    let isSystemDefault: Bool
    let createdAt: String
    let updatedAt: String
    let parameters: [String: AlertParameterValue]

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case ruleType = "rule_type"
        case severity
        case symbolScope = "symbol_scope"
        case symbols
        case isEnabled = "is_enabled"
        case cooldownSeconds = "cooldown_seconds"
        case isSystemDefault = "is_system_default"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case parameters
    }
}

struct AlertItem: Identifiable, Codable {
    let id: String
    let ruleId: String
    let alertType: String
    let severity: String
    let title: String
    let message: String
    let symbol: String?
    let eventId: String?
    let sourceTimestamp: String?
    let triggeredAt: String
    let status: String
    let acknowledgedAt: String?
    let snoozedUntil: String?
    let isMock: Bool
    let metadata: [String: AlertParameterValue]

    enum CodingKeys: String, CodingKey {
        case id
        case ruleId = "rule_id"
        case alertType = "alert_type"
        case severity
        case title
        case message
        case symbol
        case eventId = "event_id"
        case sourceTimestamp = "source_timestamp"
        case triggeredAt = "triggered_at"
        case status
        case acknowledgedAt = "acknowledged_at"
        case snoozedUntil = "snoozed_until"
        case isMock = "is_mock"
        case metadata
    }
}

struct AlertSummary: Codable {
    let new: Int
    let acknowledged: Int
    let snoozed: Int
    let highOrCritical: Int
    let latestTriggeredAt: String?

    enum CodingKeys: String, CodingKey {
        case new
        case acknowledged
        case snoozed
        case highOrCritical = "high_or_critical"
        case latestTriggeredAt = "latest_triggered_at"
    }
}

struct AlertEvaluationRequest: Codable {
    let symbols: [String]
    let includeQuotes: Bool
    let includeEvents: Bool

    enum CodingKeys: String, CodingKey {
        case symbols
        case includeQuotes = "include_quotes"
        case includeEvents = "include_events"
    }
}

struct AlertEvaluationResult: Codable {
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

struct AlertSnoozeRequest: Codable {
    let durationMinutes: Int

    enum CodingKeys: String, CodingKey {
        case durationMinutes = "duration_minutes"
    }
}

enum AlertParameterValue: Codable, Hashable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case stringArray([String])
    case array([AlertParameterValue])
    case object([String: AlertParameterValue])

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode(Double.self) {
            self = .number(value)
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode([String].self) {
            self = .stringArray(value)
        } else if let value = try? container.decode([AlertParameterValue].self) {
            self = .array(value)
        } else if let value = try? container.decode([String: AlertParameterValue].self) {
            self = .object(value)
        } else {
            self = .string("")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value):
            try container.encode(value)
        case .number(let value):
            try container.encode(value)
        case .bool(let value):
            try container.encode(value)
        case .stringArray(let value):
            try container.encode(value)
        case .array(let value):
            try container.encode(value)
        case .object(let value):
            try container.encode(value)
        }
    }
}
