import SwiftUI

struct DisclaimerView: View {
    var body: some View {
        RadarCard {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: "info.circle")
                    .foregroundStyle(RadarTheme.accent)
                    .accessibilityHidden(true)
                Text(MockMarketData.disclaimer)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .accessibilityLabel(MockMarketData.disclaimer)
    }
}
