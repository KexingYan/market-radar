import Foundation

final class APIClient {
    enum APIError: Error, LocalizedError {
        case invalidResponse
        case httpStatus(Int)
        case invalidURL

        var errorDescription: String? {
            switch self {
            case .invalidResponse:
                return "The backend returned a non-HTTP response."
            case .httpStatus(let status):
                return "The backend returned HTTP \(status)."
            case .invalidURL:
                return "The configured backend URL is invalid."
            }
        }
    }

    struct RequestDiagnostics: Equatable {
        let backendMode: String
        let baseURL: String
        let endpoint: String
        let method: String
        let httpStatus: Int?
        let errorMessage: String?
    }

    private let fixedBaseURL: URL?
    private let session: URLSession
    private let decoder: JSONDecoder
    private let diagnosticsHandler: (@Sendable (RequestDiagnostics) -> Void)?
    private(set) var lastDiagnostics: RequestDiagnostics?

    init(
        baseURL: URL? = nil,
        session: URLSession = .shared,
        diagnosticsHandler: (@Sendable (RequestDiagnostics) -> Void)? = nil
    ) {
        self.fixedBaseURL = baseURL
        self.session = session
        self.decoder = JSONDecoder()
        self.diagnosticsHandler = diagnosticsHandler
    }

    func getQuotes() async throws -> [QuoteSnapshot] {
        try await get(path: "/api/v1/quotes")
    }

    func getEvents() async throws -> [MarketEvent] {
        try await get(path: "/api/v1/events")
    }

    func getProviderStatus() async throws -> ProviderStatusResponse {
        try await get(path: "/api/v1/providers/status")
    }

    func getReports() async throws -> [MarketReport] {
        async let premarket: MarketReport = get(path: "/api/v1/reports/premarket")
        async let intraday: MarketReport = get(path: "/api/v1/reports/intraday")
        async let close: MarketReport = get(path: "/api/v1/reports/close")
        return try await [premarket, intraday, close]
    }

    func getStorageStatus() async throws -> StorageStatus {
        try await get(path: "/api/v1/storage/status")
    }

    func getRetentionPreview() async throws -> RetentionPreview {
        try await get(path: "/api/v1/storage/retention-preview")
    }

    func getAlertRules() async throws -> [AlertRule] {
        try await get(path: "/api/v1/alert-rules")
    }

    func getAlerts() async throws -> [AlertItem] {
        try await get(path: "/api/v1/alerts")
    }

    func getAlertSummary() async throws -> AlertSummary {
        try await get(path: "/api/v1/alerts/summary")
    }

    func evaluateAlerts(symbols: [String]) async throws -> AlertEvaluationResult {
        try await send(
            path: "/api/v1/alerts/evaluate",
            method: "POST",
            body: AlertEvaluationRequest(symbols: symbols, includeQuotes: true, includeEvents: true)
        )
    }

    func acknowledgeAlert(id: String) async throws -> AlertItem {
        try await send(path: "/api/v1/alerts/\(id)/acknowledge", method: "POST", body: EmptyBody())
    }

    func snoozeAlert(id: String, durationMinutes: Int) async throws -> AlertItem {
        try await send(
            path: "/api/v1/alerts/\(id)/snooze",
            method: "POST",
            body: AlertSnoozeRequest(durationMinutes: durationMinutes)
        )
    }

    func getQuoteHistory(symbol: String) async throws -> [QuoteSnapshot] {
        try await get(path: "/api/v1/history/quotes/\(symbol)?limit=5")
    }

    func getEventHistory(symbol: String) async throws -> [MarketEvent] {
        try await get(path: "/api/v1/history/events?symbol=\(symbol)&limit=5")
    }

    func getReportHistory() async throws -> [MarketReport] {
        try await get(path: "/api/v1/history/reports?report_type=intraday&limit=5")
    }

    func getJobs() async throws -> [ScheduledJob] {
        try await get(path: "/api/v1/jobs")
    }

    func getJobRuns() async throws -> [JobRun] {
        try await get(path: "/api/v1/job-runs")
    }

    func getSchedulerStatus() async throws -> SchedulerStatus {
        try await get(path: "/api/v1/scheduler/status")
    }

    func runJob(id: String) async throws -> ManualJobRunResponse {
        try await send(path: "/api/v1/jobs/\(id)/run", method: "POST", body: EmptyBody())
    }

    func runPipeline() async throws -> ManualJobRunResponse {
        try await send(path: "/api/v1/jobs/pipeline/run", method: "POST", body: EmptyBody())
    }

    func runLiveWatchlistRefresh() async throws -> LiveRefreshResponse {
        try await send(path: "/api/v1/live/watchlist-refresh", method: "POST", body: EmptyBody())
    }

    func addLocalWatchlistItem(_ request: LocalWatchlistRequest) async throws -> QuoteSnapshot? {
        let _: WatchlistItem = try await send(path: "/api/v1/watchlist", method: "POST", body: request)
        return nil
    }

    func removeLocalWatchlistItem(symbol: String) async throws {
        let _: DeleteResponse = try await send(path: "/api/v1/watchlist/\(symbol)", method: "DELETE", body: EmptyBody())
    }

    private func get<T: Decodable>(path: String) async throws -> T {
        let baseURL = resolvedBaseURL()
        let url = try makeURL(path: path, baseURL: baseURL)
        var request = URLRequest(url: url)
        request.timeoutInterval = 5
        request.cachePolicy = .reloadIgnoringLocalCacheData

        do {
            let (data, response) = try await session.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                recordDiagnostics(baseURL: baseURL, path: path, method: "GET", status: nil, error: APIError.invalidResponse)
                throw APIError.invalidResponse
            }
            recordDiagnostics(baseURL: baseURL, path: path, method: "GET", status: httpResponse.statusCode, error: nil)
            guard (200...299).contains(httpResponse.statusCode) else {
                throw APIError.httpStatus(httpResponse.statusCode)
            }
            return try decoder.decode(T.self, from: data)
        } catch {
            recordDiagnostics(baseURL: baseURL, path: path, method: "GET", status: nil, error: error)
            throw error
        }
    }

    private func send<T: Decodable, B: Encodable>(path: String, method: String, body: B) async throws -> T {
        let baseURL = resolvedBaseURL()
        let url = try makeURL(path: path, baseURL: baseURL)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 5
        if method != "DELETE" {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(body)
        }
        do {
            let (data, response) = try await session.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                recordDiagnostics(baseURL: baseURL, path: path, method: method, status: nil, error: APIError.invalidResponse)
                throw APIError.invalidResponse
            }
            recordDiagnostics(baseURL: baseURL, path: path, method: method, status: httpResponse.statusCode, error: nil)
            guard (200...299).contains(httpResponse.statusCode) else {
                throw APIError.httpStatus(httpResponse.statusCode)
            }
            return try decoder.decode(T.self, from: data)
        } catch {
            recordDiagnostics(baseURL: baseURL, path: path, method: method, status: nil, error: error)
            throw error
        }
    }

    private func resolvedBaseURL() -> URL {
        fixedBaseURL ?? AppEnvironment.apiBaseURL
    }

    private func makeURL(path: String, baseURL: URL) throws -> URL {
        guard let url = URL(string: path, relativeTo: baseURL)?.absoluteURL else {
            throw APIError.invalidURL
        }
        return url
    }

    private func recordDiagnostics(baseURL: URL, path: String, method: String, status: Int?, error: Error?) {
        let diagnostics = RequestDiagnostics(
            backendMode: AppEnvironment.backendMode.rawValue,
            baseURL: baseURL.absoluteString.trimmingCharacters(in: CharacterSet(charactersIn: "/")),
            endpoint: "\(method) \(path)",
            method: method,
            httpStatus: status,
            errorMessage: error.map { String(describing: $0) }
        )
        lastDiagnostics = diagnostics
        diagnosticsHandler?(diagnostics)
    }
}

private struct WatchlistItem: Codable {
    let symbol: String
    let displayName: String
    let market: String

    enum CodingKeys: String, CodingKey {
        case symbol
        case displayName = "display_name"
        case market
    }
}

private struct DeleteResponse: Codable {
    let removed: Bool
}

private struct EmptyBody: Codable {}
