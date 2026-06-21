import SwiftUI

struct JobRunDetailView: View {
    let run: JobRun

    var body: some View {
        List {
            Section("Run") {
                LabeledContent("Job", value: run.jobKey)
                LabeledContent("Type", value: run.jobType)
                LabeledContent("Status", value: run.status)
                LabeledContent("Trigger", value: run.triggerType)
                LabeledContent("Attempt", value: "\(run.attempt)")
                if let duration = run.durationMs {
                    LabeledContent("Duration", value: "\(duration)ms")
                }
                if let error = run.errorCode {
                    LabeledContent("Error", value: error)
                }
            }

            Section("Summary") {
                ForEach(run.resultSummary.keys.sorted(), id: \.self) { key in
                    LabeledContent(key, value: displayValue(run.resultSummary[key]))
                }
            }
        }
        .navigationTitle("Job Run")
    }

    private func displayValue(_ value: AlertParameterValue?) -> String {
        guard let value else {
            return ""
        }
        switch value {
        case .string(let item):
            return item
        case .number(let item):
            return item.formatted()
        case .bool(let item):
            return item ? "true" : "false"
        case .stringArray(let items):
            return items.joined(separator: ", ")
        case .array(let items):
            return "\(items.count) items"
        case .object(let items):
            return "\(items.count) fields"
        }
    }
}
