import SwiftUI

struct AlertRuleListView: View {
    let rules: [AlertRule]

    var body: some View {
        List {
            Section {
                ForEach(rules) { rule in
                    NavigationLink {
                        AlertRuleEditorView(rule: rule)
                    } label: {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text(rule.name)
                                    .font(.headline)
                                Spacer()
                                Text(rule.isEnabled ? "Enabled" : "Disabled")
                                    .font(.caption)
                                    .foregroundStyle(rule.isEnabled ? .green : .secondary)
                            }
                            Text("\(rule.ruleType) - \(rule.severity)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text("Cooldown \(rule.cooldownSeconds)s")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            } footer: {
                Text("Rules are deterministic and local. They do not contain scripts, expressions, AI prompts, or trading actions.")
            }
        }
        .navigationTitle("Alert Rules")
    }
}

