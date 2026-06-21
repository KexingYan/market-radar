import SwiftUI

struct JobDetailView: View {
    let job: ScheduledJob
    @ObservedObject var store: MarketDataStore

    var body: some View {
        Form {
            Section("Job") {
                LabeledContent("Key", value: job.jobKey)
                LabeledContent("Type", value: job.jobType)
                LabeledContent("Interval", value: "\(job.intervalSeconds)s")
                LabeledContent("Timeout", value: "\(job.timeoutSeconds)s")
                LabeledContent("Retries", value: "\(job.maxRetries)")
            }

            Section("Manual Run") {
                Button {
                    Task {
                        await store.runJob(id: job.id)
                    }
                } label: {
                    Label(store.isRunningJob ? "Running..." : "Run job", systemImage: "play")
                }
                .disabled(store.isRunningJob)
            }

            Section("Boundaries") {
                Text("This runs in the local foreground API process. It does not execute shell commands, connect to real providers, send notifications, or trade.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle(job.displayName)
    }
}

