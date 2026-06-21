import SwiftUI

struct EventsView: View {
    @ObservedObject var store: MarketDataStore

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
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
                    ForEach(store.events) { event in
                        EventCard(event: event)
                    }
                }
                .padding()
            }
            .navigationTitle("Events")
        }
    }
}

#Preview {
    EventsView(store: MarketDataStore())
}
