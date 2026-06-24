import SwiftUI

struct SettingsView: View {
    @ObservedObject var store: MarketDataStore
    @AppStorage(AppEnvironment.backendModeKey) private var backendModeRawValue = BackendMode.simulatorLocal.rawValue
    @AppStorage(AppEnvironment.backendURLKey) private var backendURL = ""
    @State private var isTestingConnection = false
    @State private var connectionStatus: String?

    private var backendMode: Binding<BackendMode> {
        Binding(
            get: { BackendMode(rawValue: backendModeRawValue) ?? .simulatorLocal },
            set: { backendModeRawValue = $0.rawValue }
        )
    }

    var body: some View {
        NavigationStack {
            List {
                Section("Backend") {
                    Picker("Backend Mode", selection: backendMode) {
                        ForEach(BackendMode.allCases) { mode in
                            Text(mode.rawValue).tag(mode)
                        }
                    }

                    TextField("http://192.168.x.x:8000", text: $backendURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                        .disabled(backendMode.wrappedValue != .iPhoneLAN)

                    LabeledContent("Resolved URL", value: AppEnvironment.resolvedBaseURLString)

                    Button {
                        Task {
                            await testConnection()
                        }
                    } label: {
                        Label(isTestingConnection ? "Testing..." : "Test Connection", systemImage: "network")
                    }
                    .disabled(isTestingConnection)

                    if let connectionStatus {
                        Text(connectionStatus)
                            .font(.caption)
                            .foregroundStyle(connectionStatus == "Connected" ? .green : .red)
                    }
                }

                Section("Data Status") {
                    LabeledContent("Quote Provider", value: store.providerStatus?.quotes.active ?? "not loaded")
                    LabeledContent("Event Provider", value: store.providerStatus?.events.active ?? "not loaded")
                    LabeledContent("Trading", value: "disabled")
                    LabeledContent("System Notifications", value: "not implemented")
                }

                Section("Safety") {
                    Text("The iOS app calls only the configured local Market Radar backend. It does not connect to Moomoo OpenD directly.")
                    Text("No broker password, account, holdings, assets, orders, or trading actions are stored or requested.")
                    DisclaimerView()
                        .listRowInsets(EdgeInsets())
                        .listRowBackground(Color.clear)
                }
            }
            .navigationTitle("Settings")
        }
    }

    private func testConnection() async {
        isTestingConnection = true
        connectionStatus = nil
        defer {
            isTestingConnection = false
        }

        do {
            _ = try await APIClient().getProviderStatus()
            connectionStatus = "Connected"
            await store.load()
        } catch {
            connectionStatus = "Failed: \(String(describing: error))"
        }
    }
}

struct SettingsView_Previews: PreviewProvider {
    static var previews: some View {
        SettingsView(store: MarketDataStore())
    }
}
