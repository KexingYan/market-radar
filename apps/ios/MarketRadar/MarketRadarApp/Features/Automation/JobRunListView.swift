import SwiftUI

struct JobRunListView: View {
    let runs: [JobRun]

    var body: some View {
        List {
            ForEach(runs) { run in
                NavigationLink {
                    JobRunDetailView(run: run)
                } label: {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(run.jobKey)
                                .font(.headline)
                            Spacer()
                            Text(run.status)
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(run.status == "succeeded" ? .green : .orange)
                        }
                        Text("\(run.triggerType) · attempt \(run.attempt)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Job Runs")
    }
}

