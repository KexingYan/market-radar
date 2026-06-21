import SwiftUI

struct QuoteRow: View {
    let quote: QuoteSnapshot

    private var changeColor: Color {
        quote.change >= 0 ? .green : .red
    }

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    Text(quote.symbol)
                        .font(.headline)
                    RadarStatusChip(
                        title: quote.isDelayed ? "Delayed" : "Live",
                        systemImage: quote.isDelayed ? "clock" : "dot.radiowaves.left.and.right",
                        tint: quote.isDelayed ? RadarTheme.warning : RadarTheme.positive
                    )
                }
                Text(quote.displayName)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                Text("\(quote.timestamp) · \(quote.isDelayed ? "延迟" : "实时")")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text(quote.provider == "moomoo" ? "当前行情来源：Free Moomoo Quotes" : "Mock演示数据")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 3) {
                Text("\(quote.currency) \(quote.price.radarString)")
                    .font(.headline)
                    .monospacedDigit()
                Text("\(quote.change.radarString) / \(quote.changePercent.radarString)%")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(changeColor)
            }
        }
        .padding(.vertical, 8)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(quote.symbol), \(quote.displayName), \(quote.isDelayed ? "delayed" : "live"), provider \(quote.provider)")
        .accessibilityValue("\(quote.currency) \(quote.price.radarString), change \(quote.changePercent.radarString) percent")
    }
}
