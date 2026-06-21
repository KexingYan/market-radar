import Foundation

enum AppEnvironment {
    static var apiBaseURL: URL {
        guard let url = URL(string: "http://127.0.0.1:8000") else {
            preconditionFailure("Invalid local Mock API URL")
        }
        return url
    }
}
