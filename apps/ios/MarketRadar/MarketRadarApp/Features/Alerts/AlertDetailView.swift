import SwiftUI

struct AlertDetailView: View {
    let alert: AlertItem
    @ObservedObject var store: MarketDataStore

    var body: some View {
        List {
            Section("Alert") {
                Text(alert.title)
                    .font(.headline)
                Text(alert.message)
                LabeledContent("Severity", value: alert.severity)
                LabeledContent("Status", value: alert.status)
                LabeledContent("Triggered", value: alert.triggeredAt)
                if let symbol = alert.symbol {
                    LabeledContent("Symbol", value: symbol)
                }
                if alert.isMock {
                    HStack {
                        Text("Data")
                        Spacer()
                        MockBadge()
                    }
                }
            }

            Section("Actions") {
                Button {
                    Task {
                        await store.acknowledgeAlert(id: alert.id)
                    }
                } label: {
                    Label("Acknowledge", systemImage: "checkmark.circle")
                }

                Button {
                    Task {
                        await store.snoozeAlert(id: alert.id, durationMinutes: 60)
                    }
                } label: {
                    Label("Snooze 1 hour", systemImage: "clock")
                }
            }

            Section("Boundaries") {
                Text("This alert is a deterministic local record. It is not investment advice and does not send system notifications or trading orders.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("Alert Detail")
    }
}

