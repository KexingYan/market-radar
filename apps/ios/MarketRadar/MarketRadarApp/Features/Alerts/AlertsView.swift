import SwiftUI

struct AlertsView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            List {
                Section {
                    DisclaimerView()
                    DataSourceStatusView(
                        state: store.dataSourceState,
                        message: store.lastErrorMessage,
                        refresh: {
                            Task {
                                await store.load()
                            }
                        }
                    )
                }

                Section {
                    AlertSummaryRow(summary: store.alertSummary)
                    Button {
                        Task {
                            await store.evaluateAlerts()
                        }
                    } label: {
                        Label("Evaluate local mock alerts", systemImage: "bell.badge")
                    }
                } header: {
                    Text("In-App Alert Inbox")
                } footer: {
                    Text("Alerts are local app records. Phase 4C does not send APNs, system notifications, emails, webhooks, or trading orders.")
                }

                if let evaluation = store.lastAlertEvaluation {
                    Section("Last Evaluation") {
                        Text("Rules: \(evaluation.evaluatedRules)")
                        Text("Created: \(evaluation.createdAlerts)")
                        Text("Duplicates: \(evaluation.duplicateAlerts)")
                        Text("Cooldown suppressed: \(evaluation.cooldownSuppressed)")
                    }
                }

                Section("New Alerts") {
                    if store.alerts.isEmpty {
                        Text("No local alerts.")
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(store.alerts) { alert in
                            NavigationLink {
                                AlertDetailView(alert: alert, store: store)
                            } label: {
                                AlertRowView(alert: alert)
                            }
                        }
                    }
                }

                Section("Rules") {
                    NavigationLink {
                        AlertRuleListView(rules: store.alertRules)
                    } label: {
                        Label("Alert rules", systemImage: "slider.horizontal.3")
                    }
                }
            }
            .navigationTitle("Alerts")
        }
    }
}

private struct AlertSummaryRow: View {
    let summary: AlertSummary?

    var body: some View {
        HStack {
            Label("New \(summary?.new ?? 0)", systemImage: "tray.full")
            Spacer()
            Label("High \(summary?.highOrCritical ?? 0)", systemImage: "exclamationmark.triangle")
        }
        .font(.subheadline.weight(.semibold))
    }
}

private struct AlertRowView: View {
    let alert: AlertItem

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(alert.symbol ?? "Market")
                    .font(.headline)
                Spacer()
                Text(alert.severity.uppercased())
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(alert.severity == "critical" ? .red : .orange)
            }
            Text(alert.title)
                .font(.subheadline)
            Text(alert.message)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
            HStack {
                Text(alert.alertType)
                Text(alert.triggeredAt)
                if alert.isMock {
                    MockBadge()
                }
            }
            .font(.caption2)
            .foregroundStyle(.secondary)
        }
    }
}

struct AlertsView_Previews: PreviewProvider {
    static var previews: some View {
        AlertsView(store: MarketDataStore())
    }
}
