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
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(event.eventType.rawValue)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.blue)
                Spacer()
                MockBadge()
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
                Spacer()
                Text("重要性 \(event.importanceScore)")
                    .font(.caption.weight(.semibold))
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
        .padding(12)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: RadarTheme.cardRadius))
    }
}
