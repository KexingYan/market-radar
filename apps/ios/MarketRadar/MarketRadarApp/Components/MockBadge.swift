import SwiftUI

struct MockBadge: View {
    var body: some View {
        Label("Mock", systemImage: "testtube.2")
            .font(.caption.weight(.semibold))
            .foregroundStyle(.orange)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(.orange.opacity(0.12))
            .clipShape(Capsule())
    }
}
