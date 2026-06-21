import SwiftUI

enum RadarTheme {
    static let sectionSpacing: CGFloat = 16
    static let cardRadius: CGFloat = 8
}

extension Decimal {
    var radarString: String {
        NSDecimalNumber(decimal: self).stringValue
    }
}
