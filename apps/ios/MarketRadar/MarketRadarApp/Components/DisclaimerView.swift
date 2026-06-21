import SwiftUI

struct DisclaimerView: View {
    var body: some View {
        Text(MockMarketData.disclaimer)
            .font(.footnote)
            .foregroundStyle(.secondary)
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.thinMaterial)
            .clipShape(RoundedRectangle(cornerRadius: RadarTheme.cardRadius))
    }
}
