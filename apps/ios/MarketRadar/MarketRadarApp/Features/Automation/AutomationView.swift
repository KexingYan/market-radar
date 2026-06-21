import SwiftUI

struct AutomationView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            RadarPage {
                RadarSectionHeader(
                    title: "Foreground Scheduler",
                    subtitle: "Runs only while the local scheduler process is open."
                )
                RadarCard {
                    SchedulerStatusView(status: store.schedulerStatus)
                    Text("仅当前台调度器进程保持运行时，自动任务才会执行。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                RadarSectionHeader(
                    title: "Manual Run",
                    subtitle: "Local Mock API only. No background services, notifications, or trades."
                )
                RadarCard {
                    Button {
                        Task {
                            await store.runPipeline()
                        }
                    } label: {
                        Label(store.isRunningJob ? "Running..." : "Run Full Pipeline", systemImage: store.isRunningJob ? "hourglass" : "play.circle")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(RadarTheme.accent)
                    .disabled(store.isRunningJob)

                    if store.isRunningJob {
                        HStack(spacing: 10) {
                            ProgressView()
                            Text("Pipeline is running")
                                .font(.subheadline.weight(.semibold))
                        }
                        .accessibilityElement(children: .combine)
                    }

                    if let run = store.lastManualRun {
                        HStack(spacing: 8) {
                            RadarStatusChip(title: run.status, systemImage: run.status == "succeeded" ? "checkmark.circle" : "clock", tint: run.status == "succeeded" ? RadarTheme.positive : RadarTheme.warning)
                            Text("Last run: \(run.jobKey)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .accessibilityElement(children: .combine)
                    }
                }

                RadarSectionHeader(title: "Operations")
                NavigationLink {
                    JobListView(store: store)
                } label: {
                    NavigationCard(
                        title: "Jobs",
                        subtitle: "\(store.jobs.count) configured jobs",
                        systemImage: "list.bullet.rectangle",
                        tint: RadarTheme.purple
                    )
                }
                .buttonStyle(.plain)

                NavigationLink {
                    JobRunListView(runs: store.jobRuns)
                } label: {
                    NavigationCard(
                        title: "Job Runs",
                        subtitle: "\(store.jobRuns.count) recent runs",
                        systemImage: "clock.arrow.circlepath",
                        tint: RadarTheme.accent
                    )
                }
                .buttonStyle(.plain)
            }
            .navigationTitle("Automation")
        }
    }
}

private struct NavigationCard: View {
    let title: String
    let subtitle: String
    let systemImage: String
    let tint: Color

    var body: some View {
        RadarCard {
            HStack(spacing: 12) {
                Image(systemName: systemImage)
                    .font(.headline)
                    .foregroundStyle(tint)
                    .frame(width: 28)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 3) {
                    Text(title)
                        .font(.headline)
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.tertiary)
                    .accessibilityHidden(true)
            }
        }
        .accessibilityElement(children: .combine)
    }
}

struct AutomationView_Previews: PreviewProvider {
    static var previews: some View {
        AutomationView(store: MarketDataStore())
    }
}
