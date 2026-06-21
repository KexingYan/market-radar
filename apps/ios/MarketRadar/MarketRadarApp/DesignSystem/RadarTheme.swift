import SwiftUI

enum RadarTheme {
    static let pagePadding: CGFloat = 16
    static let sectionSpacing: CGFloat = 18
    static let rowSpacing: CGFloat = 10
    static let cardRadius: CGFloat = 8
    static let chipRadius: CGFloat = 6
    static let hairlineOpacity: Double = 0.12

    static let accent = Color(red: 0.24, green: 0.52, blue: 0.96)
    static let positive = Color(red: 0.13, green: 0.68, blue: 0.39)
    static let negative = Color(red: 0.93, green: 0.25, blue: 0.28)
    static let warning = Color(red: 0.95, green: 0.61, blue: 0.20)
    static let purple = Color(red: 0.55, green: 0.41, blue: 0.95)

    static var pageBackground: Color {
        Color(.systemGroupedBackground)
    }

    static var cardBackground: Color {
        Color(.secondarySystemGroupedBackground)
    }

    static var elevatedBackground: Color {
        Color(.tertiarySystemGroupedBackground)
    }

    static var border: Color {
        Color.primary.opacity(hairlineOpacity)
    }

    static func sourceTint(for state: DataSourceState) -> Color {
        switch state {
        case .loadedFromFreeMoomooQuotes, .loadedFromSecEdgar:
            return positive
        case .loadedFromBundledMock:
            return warning
        case .error:
            return negative
        case .loading:
            return accent
        case .idle, .loadedFromLocalAPI:
            return purple
        }
    }
}

extension Decimal {
    var radarString: String {
        NSDecimalNumber(decimal: self).stringValue
    }
}

struct RadarPage<Content: View>: View {
    @ViewBuilder let content: Content

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: RadarTheme.sectionSpacing) {
                content
            }
            .padding(RadarTheme.pagePadding)
        }
        .background(RadarTheme.pageBackground)
        .scrollContentBackground(.hidden)
    }
}

struct RadarCard<Content: View>: View {
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: RadarTheme.rowSpacing) {
            content
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RadarTheme.cardBackground)
        .overlay {
            RoundedRectangle(cornerRadius: RadarTheme.cardRadius)
                .stroke(RadarTheme.border, lineWidth: 1)
        }
        .clipShape(RoundedRectangle(cornerRadius: RadarTheme.cardRadius))
    }
}

struct RadarSectionHeader: View {
    let title: String
    var subtitle: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title)
                .font(.headline)
            if let subtitle {
                Text(subtitle)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .combine)
    }
}

struct RadarStatusChip: View {
    let title: String
    let systemImage: String
    let tint: Color

    var body: some View {
        Label(title, systemImage: systemImage)
            .font(.caption.weight(.semibold))
            .lineLimit(1)
            .minimumScaleFactor(0.82)
            .foregroundStyle(tint)
            .padding(.horizontal, 8)
            .padding(.vertical, 5)
            .background(tint.opacity(0.14), in: RoundedRectangle(cornerRadius: RadarTheme.chipRadius))
            .accessibilityElement(children: .combine)
    }
}

struct RadarMetricTile: View {
    let title: String
    let value: String
    let detail: String
    let tint: Color
    let systemImage: String

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: systemImage)
                .font(.headline)
                .foregroundStyle(tint)
                .frame(width: 24)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(value)
                    .font(.title3.weight(.semibold))
                    .monospacedDigit()
                Text(detail)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RadarTheme.elevatedBackground, in: RoundedRectangle(cornerRadius: RadarTheme.cardRadius))
        .overlay {
            RoundedRectangle(cornerRadius: RadarTheme.cardRadius)
                .stroke(RadarTheme.border, lineWidth: 1)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(title), \(value), \(detail)")
    }
}

struct RadarEmptyState: View {
    let title: String
    let message: String
    let systemImage: String

    var body: some View {
        ContentUnavailableView(
            title,
            systemImage: systemImage,
            description: Text(message)
        )
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
    }
}

struct RadarLoadingState: View {
    let title: String

    var body: some View {
        RadarCard {
            HStack(spacing: 12) {
                ProgressView()
                Text(title)
                    .font(.subheadline.weight(.semibold))
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(title)
    }
}
