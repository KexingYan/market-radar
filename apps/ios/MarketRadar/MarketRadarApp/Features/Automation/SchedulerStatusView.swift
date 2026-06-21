import SwiftUI

struct SchedulerStatusView: View {
    let status: SchedulerStatus?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline) {
                RadarStatusChip(
                    title: status?.schedulerProcessRunning == true ? "Running" : "Stopped",
                    systemImage: "timer",
                    tint: status?.schedulerProcessRunning == true ? RadarTheme.positive : RadarTheme.warning
                )
                Spacer()
                Text(status?.mode ?? "foreground_only")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            LabeledContent("Enabled jobs", value: "\(status?.enabledJobs ?? 0)")
            LabeledContent("Background service", value: status?.backgroundServiceInstalled == true ? "Installed" : "Not installed")
            if let nextRunAt = status?.nextRunAt {
                LabeledContent("Next run", value: nextRunAt)
            }
        }
        .font(.subheadline)
        .accessibilityElement(children: .combine)
    }
}
