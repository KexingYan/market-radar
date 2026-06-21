import SwiftUI

struct DataSourceStatusView: View {
    let state: DataSourceState
    let message: String?
    let refresh: () -> Void

    var body: some View {
        RadarCard {
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Data Source")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    RadarStatusChip(
                        title: state.rawValue,
                        systemImage: iconName,
                        tint: RadarTheme.sourceTint(for: state)
                    )
                    if let message {
                        Text(message)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }

                Spacer()

                Button(action: refresh) {
                    Image(systemName: "arrow.clockwise")
                        .font(.headline)
                        .frame(width: 36, height: 36)
                }
                .buttonStyle(.borderless)
                .background(RadarTheme.elevatedBackground, in: Circle())
                .accessibilityLabel("Refresh local market data")
            }
        }
    }

    private var iconName: String {
        switch state {
        case .loading:
            return "arrow.triangle.2.circlepath"
        case .loadedFromBundledMock:
            return "testtube.2"
        case .loadedFromFreeMoomooQuotes:
            return "antenna.radiowaves.left.and.right"
        case .loadedFromSecEdgar:
            return "doc.text.magnifyingglass"
        case .error:
            return "exclamationmark.triangle"
        case .idle, .loadedFromLocalAPI:
            return "server.rack"
        }
    }
}
