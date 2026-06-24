import Foundation

enum BackendMode: String, CaseIterable, Identifiable {
    case simulatorLocal = "Simulator Local"
    case iPhoneLAN = "iPhone LAN"

    var id: String { rawValue }
}

enum AppEnvironment {
    static let backendModeKey = "marketRadar.backendMode"
    static let backendURLKey = "marketRadar.backendURL"

    static var backendMode: BackendMode {
        let rawValue = UserDefaults.standard.string(forKey: backendModeKey) ?? BackendMode.simulatorLocal.rawValue
        return BackendMode(rawValue: rawValue) ?? .simulatorLocal
    }

    static var customBackendURLString: String {
        UserDefaults.standard.string(forKey: backendURLKey) ?? ""
    }

    static var apiBaseURL: URL {
        if backendMode == .iPhoneLAN,
           let url = sanitizedURL(from: customBackendURLString) {
            return url
        }
        guard let url = URL(string: "http://127.0.0.1:8000") else {
            preconditionFailure("Invalid local API URL")
        }
        return url
    }

    static var resolvedBaseURLString: String {
        apiBaseURL.absoluteString.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    }

    static func sanitizedURL(from value: String) -> URL? {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
            .trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard !trimmed.isEmpty,
              let url = URL(string: trimmed),
              let scheme = url.scheme?.lowercased(),
              scheme == "http",
              url.host != nil else {
            return nil
        }
        return url
    }
}
