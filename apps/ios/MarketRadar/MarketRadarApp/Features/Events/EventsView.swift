import SwiftUI

struct EventsView: View {
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
                RadarSectionHeader(title: "Major Event Tape", subtitle: "Source, sentiment, and importance are shown without account data.")
                if store.events.isEmpty {
                    RadarEmptyState(title: "No Events", message: "Events from the local API or bundled fallback will appear here.", systemImage: "bolt")
                } else {
                    ForEach(store.events) { event in
                        EventCard(event: event)
                    }
                }
            }
            .navigationTitle("Events")
        }
    }
}

struct EventsView_Previews: PreviewProvider {
    static var previews: some View {
        EventsView(store: MarketDataStore())
    }
}
