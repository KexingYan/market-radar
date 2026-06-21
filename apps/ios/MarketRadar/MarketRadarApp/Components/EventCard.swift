import SwiftUI

struct EventCard: View {
    let event: MarketEvent

    private var sentimentColor: Color {
        switch event.sentiment {
        case .positive:
            return .green
        case .neutral:
            return .secondary
        case .negative:
            return .red
        }
    }

    var body: some View {
        RadarCard {
            HStack {
                RadarStatusChip(title: event.eventType.rawValue, systemImage: "bolt.fill", tint: RadarTheme.accent)
                Spacer()
                if event.isMock {
                    MockBadge()
                }
            }

            Text(event.title)
                .font(.headline)
                .fixedSize(horizontal: false, vertical: true)

            Text(event.summary)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)

            HStack {
                Text(event.affectedSymbols.joined(separator: ", "))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                RadarStatusChip(title: "重要性 \(event.importanceScore)", systemImage: "gauge.with.dots.needle.67percent", tint: sentimentColor)
            }

            HStack {
                Text(event.publishedAt)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("Source: \(event.sourceName)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text(event.sentiment.rawValue)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(sentimentColor)
            }
        }
        .accessibilityElement(children: .combine)
    }
}
