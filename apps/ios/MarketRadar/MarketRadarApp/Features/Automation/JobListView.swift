import SwiftUI

struct JobListView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        RadarPage {
            RadarSectionHeader(
                title: "Configured Jobs",
                subtitle: "Foreground, local job definitions used by the app scheduler."
            )

            if store.jobs.isEmpty {
                RadarCard {
                    RadarEmptyState(
                        title: "No Jobs",
                        message: "The local API has not returned job definitions yet.",
                        systemImage: "list.bullet.rectangle"
                    )
                }
            } else {
                ForEach(store.jobs) { job in
                    NavigationLink {
                        JobDetailView(job: job, store: store)
                    } label: {
                        JobCard(job: job)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .navigationTitle("Jobs")
    }
}

private struct JobCard: View {
    let job: ScheduledJob

    var body: some View {
        RadarCard {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: "gearshape.2")
                    .foregroundStyle(job.isEnabled ? RadarTheme.positive : .secondary)
                    .frame(width: 24)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 5) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(job.displayName)
                            .font(.headline)
                        Spacer()
                        RadarStatusChip(
                            title: job.isEnabled ? "Enabled" : "Disabled",
                            systemImage: job.isEnabled ? "checkmark.circle" : "pause.circle",
                            tint: job.isEnabled ? RadarTheme.positive : .secondary
                        )
                    }
                    Text(job.jobType)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text("Timeout \(job.timeoutSeconds)s · retries \(job.maxRetries)")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .accessibilityElement(children: .combine)
    }
}
