import SwiftUI

struct AlertsView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            RadarPage {
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

                RadarSectionHeader(
                    title: "Alert Inbox",
                    subtitle: "Local app records only. No APNs, emails, webhooks, orders, or background services."
                )
                RadarCard {
                    AlertSummaryRow(summary: store.alertSummary)
                    Button {
                        Task {
                            await store.evaluateAlerts()
                        }
                    } label: {
                        Label("Evaluate local mock alerts", systemImage: "bell.badge")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(RadarTheme.accent)
                    .accessibilityHint("Runs local alert evaluation against mock-compatible app data.")
                }

                if let evaluation = store.lastAlertEvaluation {
                    RadarSectionHeader(title: "Last Evaluation")
                    RadarCard {
                        EvaluationGrid(evaluation: evaluation)
                    }
                }

                RadarSectionHeader(title: "New Alerts")
                if store.alerts.isEmpty {
                    RadarCard {
                        RadarEmptyState(
                            title: "No Local Alerts",
                            message: "Alert rules have not created any in-app records yet.",
                            systemImage: "bell.slash"
                        )
                    }
                } else {
                    ForEach(store.alerts) { alert in
                        NavigationLink {
                            AlertDetailView(alert: alert, store: store)
                        } label: {
                            AlertRowView(alert: alert)
                        }
                        .buttonStyle(.plain)
                    }
                }

                RadarSectionHeader(title: "Rules")
                NavigationLink {
                    AlertRuleListView(rules: store.alertRules)
                } label: {
                    RadarCard {
                        HStack(spacing: 12) {
                            Image(systemName: "slider.horizontal.3")
                                .font(.headline)
                                .foregroundStyle(RadarTheme.purple)
                                .accessibilityHidden(true)
                            VStack(alignment: .leading, spacing: 3) {
                                Text("Alert Rules")
                                    .font(.headline)
                                Text("\(store.alertRules.count) local rules configured")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.tertiary)
                                .accessibilityHidden(true)
                        }
                    }
                }
                .buttonStyle(.plain)
            }
            .navigationTitle("Alerts")
        }
    }
}

private struct AlertSummaryRow: View {
    let summary: AlertSummary?

    var body: some View {
        HStack(spacing: 10) {
            RadarMetricTile(
                title: "New",
                value: "\(summary?.new ?? 0)",
                detail: "unread local alerts",
                tint: RadarTheme.accent,
                systemImage: "tray.full"
            )
            RadarMetricTile(
                title: "High",
                value: "\(summary?.highOrCritical ?? 0)",
                detail: "high or critical",
                tint: RadarTheme.warning,
                systemImage: "exclamationmark.triangle"
            )
        }
    }
}

private struct EvaluationGrid: View {
    let evaluation: AlertEvaluationResult

    var body: some View {
        VStack(spacing: 8) {
            LabeledContent("Rules", value: "\(evaluation.evaluatedRules)")
            LabeledContent("Created", value: "\(evaluation.createdAlerts)")
            LabeledContent("Duplicates", value: "\(evaluation.duplicateAlerts)")
            LabeledContent("Cooldown suppressed", value: "\(evaluation.cooldownSuppressed)")
        }
        .font(.subheadline)
        .accessibilityElement(children: .combine)
    }
}

private struct AlertRowView: View {
    let alert: AlertItem

    var body: some View {
        RadarCard {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: severityIcon)
                    .font(.headline)
                    .foregroundStyle(severityTint)
                    .frame(width: 24)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 6) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(alert.symbol ?? "Market")
                            .font(.headline)
                        Spacer()
                        RadarStatusChip(title: alert.severity.uppercased(), systemImage: severityIcon, tint: severityTint)
                    }
                    Text(alert.title)
                        .font(.subheadline.weight(.semibold))
                    Text(alert.message)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(3)
                    HStack(spacing: 8) {
                        RadarStatusChip(title: alert.alertType, systemImage: "tag", tint: RadarTheme.purple)
                        RadarStatusChip(title: alert.triggeredAt, systemImage: "clock", tint: RadarTheme.accent)
                        if alert.isMock {
                            MockBadge()
                        }
                    }
                }
            }
        }
        .accessibilityElement(children: .combine)
    }

    private var severityTint: Color {
        alert.severity == "critical" ? RadarTheme.negative : RadarTheme.warning
    }

    private var severityIcon: String {
        alert.severity == "critical" ? "exclamationmark.octagon" : "exclamationmark.triangle"
    }
}

struct AlertsView_Previews: PreviewProvider {
    static var previews: some View {
        AlertsView(store: MarketDataStore())
    }
}
