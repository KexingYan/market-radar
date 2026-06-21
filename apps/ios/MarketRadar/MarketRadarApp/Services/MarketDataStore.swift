import Combine
import Foundation

enum DataSourceState: String, Equatable {
    case idle
    case loading
    case loadedFromLocalAPI = "Local Mock API"
    case loadedFromBundledMock = "Bundled Mock Fallback"
    case loadedFromFreeMoomooQuotes = "Free Moomoo Quotes"
    case loadedFromSecEdgar = "SEC EDGAR"
    case error
}

@MainActor
final class MarketDataStore: ObservableObject {
    @Published private(set) var dataSourceState: DataSourceState = .idle
    @Published private(set) var quotes: [QuoteSnapshot] = MockMarketData.indices + MockMarketData.watchlist
    @Published private(set) var events: [MarketEvent] = MockMarketData.events
    @Published private(set) var reports: [MarketReport] = []
    @Published private(set) var storageStatus: StorageStatus?
    @Published private(set) var providerStatus: ProviderStatusResponse?
    @Published private(set) var alertRules: [AlertRule] = []
    @Published private(set) var alerts: [AlertItem] = []
    @Published private(set) var alertSummary: AlertSummary?
    @Published private(set) var lastAlertEvaluation: AlertEvaluationResult?
    @Published private(set) var jobs: [ScheduledJob] = []
    @Published private(set) var jobRuns: [JobRun] = []
    @Published private(set) var schedulerStatus: SchedulerStatus?
    @Published private(set) var lastManualRun: ManualJobRunResponse?
    @Published private(set) var liveRefreshResult: LiveRefreshResponse?
    @Published private(set) var liveHistorySnapshot: LiveHistorySnapshot?
    @Published private(set) var liveRefreshState: LiveRefreshViewState = .idle
    @Published private(set) var isRunningJob: Bool = false
    @Published private(set) var lastErrorMessage: String?

    private let apiClient: APIClient

    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
    }

    var indices: [QuoteSnapshot] {
        quotes.filter { $0.symbol.hasPrefix("MOCK-") }
    }

    var watchlist: [QuoteSnapshot] {
        quotes.filter { !$0.symbol.hasPrefix("MOCK-") }
    }

    func load() async {
        dataSourceState = .loading
        do {
            async let apiQuotes = apiClient.getQuotes()
            async let apiEvents = apiClient.getEvents()
            async let apiProviderStatus = apiClient.getProviderStatus()
            async let apiReports = apiClient.getReports()
            async let apiStorageStatus = apiClient.getStorageStatus()
            async let apiAlertRules = apiClient.getAlertRules()
            async let apiAlerts = apiClient.getAlerts()
            async let apiAlertSummary = apiClient.getAlertSummary()
            async let apiJobs = apiClient.getJobs()
            async let apiJobRuns = apiClient.getJobRuns()
            async let apiSchedulerStatus = apiClient.getSchedulerStatus()
            quotes = try await apiQuotes
            events = try await apiEvents
            providerStatus = try await apiProviderStatus
            reports = try await apiReports
            storageStatus = try await apiStorageStatus
            alertRules = try await apiAlertRules
            alerts = try await apiAlerts
            alertSummary = try await apiAlertSummary
            jobs = try await apiJobs
            jobRuns = try await apiJobRuns
            schedulerStatus = try await apiSchedulerStatus
            lastErrorMessage = nil
            dataSourceState = resolvedState(from: providerStatus)
        } catch {
            quotes = MockMarketData.indices + MockMarketData.watchlist
            events = MockMarketData.events
            reports = []
            storageStatus = nil
            providerStatus = nil
            alertRules = []
            alerts = []
            alertSummary = nil
            lastAlertEvaluation = nil
            jobs = []
            jobRuns = []
            schedulerStatus = nil
            lastManualRun = nil
            liveRefreshResult = nil
            liveHistorySnapshot = nil
            liveRefreshState = .idle
            isRunningJob = false
            lastErrorMessage = "当前使用本地内置 Mock 数据"
            dataSourceState = .loadedFromBundledMock
        }
    }

    func runJob(id: String) async {
        guard !isRunningJob else {
            return
        }
        isRunningJob = true
        defer {
            isRunningJob = false
        }
        do {
            lastManualRun = try await apiClient.runJob(id: id)
            jobRuns = try await apiClient.getJobRuns()
            schedulerStatus = try await apiClient.getSchedulerStatus()
        } catch {
            lastErrorMessage = "Manual local job run failed."
        }
    }

    func runPipeline() async {
        guard !isRunningJob else {
            return
        }
        isRunningJob = true
        defer {
            isRunningJob = false
        }
        do {
            lastManualRun = try await apiClient.runPipeline()
            jobRuns = try await apiClient.getJobRuns()
            storageStatus = try await apiClient.getStorageStatus()
            alertSummary = try await apiClient.getAlertSummary()
        } catch {
            lastErrorMessage = "Manual local pipeline failed."
        }
    }

    func runLiveWatchlistRefresh() async {
        guard liveRefreshState != .loading else {
            return
        }
        liveRefreshState = .loading
        do {
            let result = try await apiClient.runLiveWatchlistRefresh()
            liveRefreshResult = result
            let primarySymbol = result.symbols.first ?? "AAPL"
            async let quoteHistory = apiClient.getQuoteHistory(symbol: primarySymbol)
            async let eventHistory = apiClient.getEventHistory(symbol: primarySymbol)
            async let reportHistory = apiClient.getReportHistory()
            async let alertSummary = apiClient.getAlertSummary()
            async let jobRuns = apiClient.getJobRuns()

            let quotes = try await quoteHistory
            let events = try await eventHistory
            let reports = try await reportHistory
            let summary = try await alertSummary
            let runs = try await jobRuns
            liveHistorySnapshot = LiveHistorySnapshot(
                quoteRows: quotes.count,
                quoteSymbols: quotes.map(\.symbol),
                quoteTimestamps: quotes.map(\.timestamp),
                eventRows: events.count,
                reportRows: reports.count,
                alertSummary: summary,
                jobRunRows: runs.count
            )
            providerStatus = try await apiClient.getProviderStatus()
            self.alertSummary = summary
            self.jobRuns = runs
            lastErrorMessage = nil
            liveRefreshState = .loaded
            dataSourceState = resolvedState(from: providerStatus)
        } catch {
            liveRefreshState = .error("Local API unavailable; live refresh was not run.")
            lastErrorMessage = "Local API unavailable; live refresh was not run."
        }
    }

    func evaluateAlerts() async {
        do {
            lastAlertEvaluation = try await apiClient.evaluateAlerts(symbols: watchlist.map(\.symbol))
            alerts = try await apiClient.getAlerts()
            alertSummary = try await apiClient.getAlertSummary()
        } catch {
            lastErrorMessage = "Local API unavailable; alerts were not evaluated."
        }
    }

    func acknowledgeAlert(id: String) async {
        do {
            _ = try await apiClient.acknowledgeAlert(id: id)
            alerts = try await apiClient.getAlerts()
            alertSummary = try await apiClient.getAlertSummary()
        } catch {
            lastErrorMessage = "Alert acknowledge failed."
        }
    }

    func snoozeAlert(id: String, durationMinutes: Int) async {
        do {
            _ = try await apiClient.snoozeAlert(id: id, durationMinutes: durationMinutes)
            alerts = try await apiClient.getAlerts()
            alertSummary = try await apiClient.getAlertSummary()
        } catch {
            lastErrorMessage = "Alert snooze failed."
        }
    }

    func addLocalWatchlist(symbol: String, displayName: String, market: String) async {
        do {
            try await apiClient.addLocalWatchlistItem(
                LocalWatchlistRequest(symbol: symbol, displayName: displayName, market: market)
            )
            await load()
        } catch {
            lastErrorMessage = "本地自选股添加失败"
        }
    }

    func removeLocalWatchlist(symbol: String) async {
        do {
            try await apiClient.removeLocalWatchlistItem(symbol: symbol)
            await load()
        } catch {
            lastErrorMessage = "本地自选股删除失败"
        }
    }

    private func resolvedState(from status: ProviderStatusResponse?) -> DataSourceState {
        guard let status else {
            return .loadedFromLocalAPI
        }
        if status.quotes.active == "moomoo" {
            return .loadedFromFreeMoomooQuotes
        }
        if status.events.active == "sec" {
            return .loadedFromSecEdgar
        }
        return .loadedFromLocalAPI
    }
}
