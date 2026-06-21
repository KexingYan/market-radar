import SwiftUI

struct JobListView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        List {
            ForEach(store.jobs) { job in
                NavigationLink {
                    JobDetailView(job: job, store: store)
                } label: {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(job.displayName)
                                .font(.headline)
                            Spacer()
                            Text(job.isEnabled ? "Enabled" : "Disabled")
                                .font(.caption)
                                .foregroundStyle(job.isEnabled ? .green : .secondary)
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
        }
        .navigationTitle("Jobs")
    }
}

