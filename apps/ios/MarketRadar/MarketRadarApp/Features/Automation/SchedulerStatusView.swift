import SwiftUI

struct SchedulerStatusView: View {
    let status: SchedulerStatus?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Label(status?.schedulerProcessRunning == true ? "Running" : "Stopped", systemImage: "timer")
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
    }
}

