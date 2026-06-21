import Foundation

struct DailyReport: Identifiable, Codable {
    let id: String
    let title: String
    let reportType: String
    let summary: String
    let bulletPoints: [String]
    let publishedAt: String
    let isMock: Bool
}
