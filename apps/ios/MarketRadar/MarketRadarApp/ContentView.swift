import SwiftUI

struct ContentView: View {
    @StateObject private var marketDataStore = MarketDataStore()

    var body: some View {
        TabView {
            DashboardView(store: marketDataStore)
                .tabItem {
                    Label("Dashboard", systemImage: "chart.line.uptrend.xyaxis")
                }

            WatchlistView(store: marketDataStore)
                .tabItem {
                    Label("Watchlist", systemImage: "star")
                }

            EventsView(store: marketDataStore)
                .tabItem {
                    Label("Events", systemImage: "bolt")
                }

            ReportsView(store: marketDataStore)
                .tabItem {
                    Label("Reports", systemImage: "doc.text")
                }

            AlertsView(store: marketDataStore)
                .tabItem {
                    Label("Alerts", systemImage: "bell")
                }

            AutomationView(store: marketDataStore)
                .tabItem {
                    Label("Automation", systemImage: "timer")
                }

            LiveRefreshView(store: marketDataStore)
                .tabItem {
                    Label("Live", systemImage: "dot.radiowaves.left.and.right")
                }

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
        .task {
            await marketDataStore.load()
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
