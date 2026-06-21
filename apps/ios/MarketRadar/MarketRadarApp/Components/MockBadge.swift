import SwiftUI

struct MockBadge: View {
    var body: some View {
        RadarStatusChip(title: "Mock", systemImage: "testtube.2", tint: RadarTheme.warning)
    }
}
