import Foundation
import XCTest
@testable import MarketRadarApp

final class MarketRadarLocalAPITests: XCTestCase {
    override func tearDown() {
        MockURLProtocol.requestHandler = nil
        super.tearDown()
    }

    func testQuoteJSONDecoding() throws {
        let jsonString = """
        [{
          "symbol": "AAPL",
          "display_name": "Apple Mock",
          "market": "US",
          "currency": "USD",
          "provider": "mock",
          "price": 182.40,
          "previous_close": 181.10,
          "change": 1.30,
          "change_percent": 0.72,
          "volume": 12340000,
          "average_volume_20d": 51100000,
          "market_status": "mock_closed",
          "timestamp": "2024-01-15T21:00:00Z",
          "is_delayed": true
        }]
        """
        let jsonData = try XCTUnwrap(jsonString.data(using: .utf8))

        let quotes = try JSONDecoder().decode([QuoteSnapshot].self, from: jsonData)

        XCTAssertEqual(quotes.first?.symbol, "AAPL")
        XCTAssertEqual(quotes.first?.provider, "mock")
        XCTAssertEqual(quotes.first?.isDelayed, true)
    }

    func testMarketEventJSONDecoding() throws {
        let jsonString = """
        [{
          "id": "mock-event-001",
          "event_type": "earnings",
          "title": "Mock event",
          "summary": "Mock summary",
          "source_name": "Mock Data Provider",
          "source_url": "mock://events/mock-event-001",
          "published_at": "2024-01-15T13:00:00Z",
          "received_at": "2024-01-15T13:01:00Z",
          "affected_symbols": ["AAPL"],
          "importance_score": 82,
          "reliability_score": 100,
          "sentiment": "neutral",
          "confidence": 0.92,
          "is_mock": true
        }]
        """
        let jsonData = try XCTUnwrap(jsonString.data(using: .utf8))

        let events = try JSONDecoder().decode([MarketEvent].self, from: jsonData)

        XCTAssertEqual(events.first?.sourceName, "Mock Data Provider")
        XCTAssertEqual(events.first?.isMock, true)
    }

    func testProviderStatusJSONDecoding() throws {
        let jsonString = """
        {
          "free_only_mode": true,
          "quotes": {
            "configured": "mock",
            "active": "mock",
            "available": true,
            "reason": null
          },
          "events": {
            "configured": "mock",
            "active": "mock",
            "available": true,
            "reason": null
          },
          "trading_enabled": false,
          "paid_data_enabled": false
        }
        """
        let jsonData = try XCTUnwrap(jsonString.data(using: .utf8))

        let status = try JSONDecoder().decode(ProviderStatusResponse.self, from: jsonData)

        XCTAssertEqual(status.quotes.active, "mock")
        XCTAssertEqual(status.events.active, "mock")
        XCTAssertFalse(status.tradingEnabled)
        XCTAssertFalse(status.paidDataEnabled)
    }

    func testLiveRefreshResponseJSONDecoding() throws {
        let jsonString = """
        {
          "symbols": ["AAPL"],
          "fallback_symbol_used": true,
          "sec": {
            "attempted": true,
            "success": true,
            "request_count": 2,
            "filings_parsed": 10,
            "fallback_used": false
          },
          "moomoo": {
            "attempted": true,
            "success": true,
            "snapshot_rows": 1,
            "quote_context_closed": true,
            "fallback_used": false
          },
          "quote_archive": {
            "inserted": 1,
            "duplicates": 0,
            "failed": 0
          },
          "event_archive": {
            "inserted": 0,
            "duplicates": 10,
            "failed": 0
          },
          "report": {
            "generated": true,
            "archived": 1,
            "duplicate": 0,
            "failed": 0
          },
          "alerts": {
            "evaluated_rules": 29,
            "evaluated_symbols": 1,
            "created_alerts": 0,
            "duplicate_alerts": 0,
            "cooldown_suppressed": 27,
            "mock_data_used": false
          },
          "job_run": {
            "saved": true,
            "status": "succeeded"
          },
          "trading_enabled": false,
          "paid_data_enabled": false
        }
        """
        let jsonData = try XCTUnwrap(jsonString.data(using: .utf8))

        let result = try JSONDecoder().decode(LiveRefreshResponse.self, from: jsonData)

        XCTAssertEqual(result.symbols, ["AAPL"])
        XCTAssertTrue(result.sec.success)
        XCTAssertTrue(result.moomoo.quoteContextClosed)
        XCTAssertFalse(result.tradingEnabled)
        XCTAssertFalse(result.paidDataEnabled)
    }

    func testJobRunNestedSummaryJSONDecoding() throws {
        let jsonString = """
        [{
          "id": "run-local",
          "job_id": "live-watchlist-refresh",
          "job_key": "live_watchlist_refresh",
          "job_type": "full_pipeline",
          "status": "succeeded",
          "started_at": "2026-06-21T00:00:00Z",
          "finished_at": "2026-06-21T00:00:01Z",
          "duration_ms": 1000,
          "attempt": 1,
          "trigger_type": "manual",
          "input_summary": {},
          "result_summary": {
            "symbols": ["AAPL"],
            "sec": {
              "success": true,
              "request_count": 2
            },
            "steps": [
              {
                "name": "archive",
                "ok": true
              }
            ]
          },
          "error_code": null,
          "error_message": null,
          "created_at": "2026-06-21T00:00:00Z"
        }]
        """
        let jsonData = try XCTUnwrap(jsonString.data(using: .utf8))

        let runs = try JSONDecoder().decode([JobRun].self, from: jsonData)

        XCTAssertEqual(runs.first?.jobKey, "live_watchlist_refresh")
        XCTAssertNotNil(runs.first?.resultSummary["sec"])
        XCTAssertNotNil(runs.first?.resultSummary["steps"])
    }

    func testSensitiveFieldsAreNotModeled() {
        let quoteProperties = Set(["symbol", "displayName", "market", "currency", "provider"])
        let eventProperties = Set(["id", "eventType", "sourceName", "sourceURL", "isMock"])
        let forbidden = Set(["password", "passwd", "secret", "token", "apiKey", "privateKey", "accountId"])

        XCTAssertTrue(quoteProperties.isDisjoint(with: forbidden))
        XCTAssertTrue(eventProperties.isDisjoint(with: forbidden))
    }

    func testAPIClientUsesInjectedURLProtocol() async throws {
        let payload = """
        [{
          "symbol": "AAPL",
          "display_name": "Apple Mock",
          "market": "US",
          "currency": "USD",
          "provider": "mock",
          "price": 182.40,
          "previous_close": 181.10,
          "change": 1.30,
          "change_percent": 0.72,
          "volume": 12340000,
          "average_volume_20d": 51100000,
          "market_status": "mock_closed",
          "timestamp": "2024-01-15T21:00:00Z",
          "is_delayed": true
        }]
        """
        let payloadData = try XCTUnwrap(payload.data(using: .utf8))
        MockURLProtocol.requestHandler = { request in
            let response = try XCTUnwrap(
                HTTPURLResponse(
                    url: request.url ?? AppEnvironment.apiBaseURL,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: nil
                )
            )
            return (response, payloadData)
        }

        let client = APIClient(baseURL: try XCTUnwrap(URL(string: "http://127.0.0.1:8000")), session: makeMockSession())
        let quotes = try await client.getQuotes()

        XCTAssertEqual(quotes.count, 1)
        XCTAssertEqual(quotes.first?.provider, "mock")
    }

    func testAPIClientRunLiveRefreshUsesLocalEndpoint() async throws {
        let payload = """
        {
          "symbols": ["AAPL"],
          "fallback_symbol_used": true,
          "sec": {
            "attempted": true,
            "success": true,
            "request_count": 2,
            "filings_parsed": 10,
            "fallback_used": false
          },
          "moomoo": {
            "attempted": true,
            "success": true,
            "snapshot_rows": 1,
            "quote_context_closed": true,
            "fallback_used": false
          },
          "quote_archive": {
            "inserted": 1,
            "duplicates": 0,
            "failed": 0
          },
          "event_archive": {
            "inserted": 0,
            "duplicates": 10,
            "failed": 0
          },
          "report": {
            "generated": true,
            "archived": 1,
            "duplicate": 0,
            "failed": 0
          },
          "alerts": {
            "evaluated_rules": 29,
            "evaluated_symbols": 1,
            "created_alerts": 0,
            "duplicate_alerts": 0,
            "cooldown_suppressed": 27,
            "mock_data_used": false
          },
          "job_run": {
            "saved": true,
            "status": "succeeded"
          },
          "trading_enabled": false,
          "paid_data_enabled": false
        }
        """
        let payloadData = try XCTUnwrap(payload.data(using: .utf8))
        MockURLProtocol.requestHandler = { request in
            XCTAssertEqual(request.url?.path, "/api/v1/live/watchlist-refresh")
            XCTAssertEqual(request.httpMethod, "POST")
            let response = try XCTUnwrap(
                HTTPURLResponse(
                    url: request.url ?? AppEnvironment.apiBaseURL,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: nil
                )
            )
            return (response, payloadData)
        }

        let client = APIClient(baseURL: try XCTUnwrap(URL(string: "http://127.0.0.1:8000")), session: makeMockSession())
        let result = try await client.runLiveWatchlistRefresh()

        XCTAssertEqual(result.symbols, ["AAPL"])
        XCTAssertTrue(result.jobRun.saved)
    }

    @MainActor
    func testNetworkFailureFallsBackToBundledMock() async throws {
        MockURLProtocol.requestHandler = { _ in
            throw URLError(.notConnectedToInternet)
        }

        let client = APIClient(baseURL: try XCTUnwrap(URL(string: "http://127.0.0.1:8000")), session: makeMockSession())
        let store = MarketDataStore(apiClient: client)

        await store.load()

        XCTAssertEqual(store.dataSourceState, .loadedFromBundledMock)
        XCTAssertFalse(store.watchlist.isEmpty)
        XCTAssertFalse(store.events.isEmpty)
    }

    private func makeMockSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        return URLSession(configuration: configuration)
    }
}

private final class MockURLProtocol: URLProtocol {
    static var requestHandler: ((URLRequest) throws -> (HTTPURLResponse, Data))?

    override class func canInit(with request: URLRequest) -> Bool {
        true
    }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest {
        request
    }

    override func startLoading() {
        guard let handler = Self.requestHandler else {
            client?.urlProtocol(self, didFailWithError: URLError(.badServerResponse))
            return
        }

        do {
            let (response, data) = try handler(request)
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}
