import SwiftUI

struct JobRunListView: View {
    let runs: [JobRun]

    var body: some View {
        RadarPage {
            RadarSectionHeader(
                title: "Recent Runs",
                subtitle: "Local job execution history returned by the API."
            )

            if runs.isEmpty {
                RadarCard {
                    RadarEmptyState(
                        title: "No Runs Yet",
                        message: "Manual or scheduled jobs have not produced local run records yet.",
                        systemImage: "clock.arrow.circlepath"
                    )
                }
            } else {
                ForEach(runs) { run in
                    NavigationLink {
                        JobRunDetailView(run: run)
                    } label: {
                        JobRunCard(run: run)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .navigationTitle("Job Runs")
    }
}

private struct JobRunCard: View {
    let run: JobRun

    var body: some View {
        RadarCard {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: statusIcon)
                    .foregroundStyle(statusTint)
                    .frame(width: 24)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 5) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(run.jobKey)
                            .font(.headline)
                        Spacer()
                        RadarStatusChip(title: run.status, systemImage: statusIcon, tint: statusTint)
                    }
                    Text("\(run.triggerType) · attempt \(run.attempt)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let duration = run.durationMs {
                        Text("Duration \(duration)ms")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .accessibilityElement(children: .combine)
    }

    private var statusTint: Color {
        run.status == "succeeded" ? RadarTheme.positive : RadarTheme.warning
    }

    private var statusIcon: String {
        run.status == "succeeded" ? "checkmark.circle" : "clock"
    }
}

