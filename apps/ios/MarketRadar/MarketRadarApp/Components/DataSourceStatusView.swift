import SwiftUI

struct DataSourceStatusView: View {
    let state: DataSourceState
    let message: String?
    let refresh: () -> Void

    var body: some View {
        HStack(spacing: 10) {
            VStack(alignment: .leading, spacing: 3) {
                Text(state.rawValue)
                    .font(.caption.weight(.semibold))
                if let message {
                    Text(message)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()

            Button(action: refresh) {
                Image(systemName: "arrow.clockwise")
            }
            .buttonStyle(.borderless)
            .accessibilityLabel("Refresh local Mock API")
        }
        .padding(12)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: RadarTheme.cardRadius))
    }
}
