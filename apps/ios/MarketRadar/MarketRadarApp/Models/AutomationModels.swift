import Foundation

struct ScheduledJob: Identifiable, Codable {
    let id: String
    let jobKey: String
    let jobType: String
    let displayName: String
    let isEnabled: Bool
    let intervalSeconds: Int
    let timeoutSeconds: Int
    let maxRetries: Int
    let lastRunAt: String?
    let nextRunAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case jobKey = "job_key"
        case jobType = "job_type"
        case displayName = "display_name"
        case isEnabled = "is_enabled"
        case intervalSeconds = "interval_seconds"
        case timeoutSeconds = "timeout_seconds"
        case maxRetries = "max_retries"
        case lastRunAt = "last_run_at"
        case nextRunAt = "next_run_at"
    }
}

struct JobRun: Identifiable, Codable {
    let id: String
    let jobId: String
    let jobKey: String
    let jobType: String
    let status: String
    let startedAt: String?
    let finishedAt: String?
    let durationMs: Int?
    let attempt: Int
    let triggerType: String
    let resultSummary: [String: AlertParameterValue]
    let errorCode: String?
    let errorMessage: String?

    enum CodingKeys: String, CodingKey {
        case id
        case jobId = "job_id"
        case jobKey = "job_key"
        case jobType = "job_type"
        case status
        case startedAt = "started_at"
        case finishedAt = "finished_at"
        case durationMs = "duration_ms"
        case attempt
        case triggerType = "trigger_type"
        case resultSummary = "result_summary"
        case errorCode = "error_code"
        case errorMessage = "error_message"
    }
}

struct SchedulerStatus: Codable {
    let schedulerEnabled: Bool
    let schedulerProcessRunning: Bool
    let enabledJobs: Int
    let nextRunAt: String?
    let mode: String
    let backgroundServiceInstalled: Bool

    enum CodingKeys: String, CodingKey {
        case schedulerEnabled = "scheduler_enabled"
        case schedulerProcessRunning = "scheduler_process_running"
        case enabledJobs = "enabled_jobs"
        case nextRunAt = "next_run_at"
        case mode
        case backgroundServiceInstalled = "background_service_installed"
    }
}

struct ManualJobRunResponse: Codable {
    let runId: String
    let jobKey: String
    let jobType: String
    let status: String
    let attempts: Int
    let errorCode: String?
    let errorMessage: String?

    enum CodingKeys: String, CodingKey {
        case runId = "run_id"
        case jobKey = "job_key"
        case jobType = "job_type"
        case status
        case attempts
        case errorCode = "error_code"
        case errorMessage = "error_message"
    }
}

