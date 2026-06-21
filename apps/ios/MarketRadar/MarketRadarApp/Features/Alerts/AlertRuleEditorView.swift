import SwiftUI

struct AlertRuleEditorView: View {
    let rule: AlertRule

    var body: some View {
        Form {
            Section("Rule") {
                LabeledContent("Name", value: rule.name)
                LabeledContent("Type", value: rule.ruleType)
                LabeledContent("Severity", value: rule.severity)
                LabeledContent("Scope", value: rule.symbolScope)
                LabeledContent("Cooldown", value: "\(rule.cooldownSeconds)s")
            }

            Section("Parameters") {
                ForEach(rule.parameters.keys.sorted(), id: \.self) { key in
                    LabeledContent(key, value: displayValue(rule.parameters[key]))
                }
            }

            Section("Phase 4C") {
                Text("Editing UI is source-only in this Windows environment. API support exists for local rule updates, but Xcode validation is pending macOS/Xcode.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("Rule")
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
        }
    }
}

