import SwiftUI

struct AutomationView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            List {
                Section {
                    SchedulerStatusView(status: store.schedulerStatus)
                    Text("The scheduler only runs while the local foreground scheduler process is open.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text("仅当前台调度器进程保持运行时，自动任务才会执行。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } header: {
                    Text("Foreground Scheduler")
                }

                Section {
                    Button {
                        Task {
                            await store.runPipeline()
                        }
                    } label: {
                        Label(store.isRunningJob ? "Running..." : "Run Full Pipeline", systemImage: "play.circle")
                    }
                    .disabled(store.isRunningJob)

                    if let run = store.lastManualRun {
                        Text("Last run: \(run.jobKey) - \(run.status)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                } footer: {
                    Text("Manual runs use the local Mock API only. They do not start background services, send notifications, or place trades.")
                }

                Section("Jobs") {
                    NavigationLink {
                        JobListView(store: store)
                    } label: {
                        Label("Jobs", systemImage: "list.bullet.rectangle")
                    }
                }

                Section("Recent Runs") {
                    NavigationLink {
                        JobRunListView(runs: store.jobRuns)
                    } label: {
                        Label("Job runs", systemImage: "clock.arrow.circlepath")
                    }
                }
            }
            .navigationTitle("Automation")
        }
    }
}

struct AutomationView_Previews: PreviewProvider {
    static var previews: some View {
        AutomationView(store: MarketDataStore())
    }
}
