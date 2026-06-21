from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_storage_status_and_retention_preview() -> None:
    status = client.get("/api/v1/storage/status")
    preview = client.get("/api/v1/storage/retention-preview")

    assert status.status_code == 200
    assert status.json()["database_location_type"] == "project_runtime"
    assert "path" not in status.json()
    assert preview.status_code == 200
    assert preview.json()["automatic_deletion_enabled"] is False


def test_report_archive_and_history_endpoints() -> None:
    report_response = client.get("/api/v1/reports/close?archive=true")

    assert report_response.status_code == 200
    report_id = report_response.json()["id"]
    history = client.get("/api/v1/history/reports?report_type=close&limit=10")
    detail = client.get(f"/api/v1/history/reports/{report_id}")

    assert history.status_code == 200
    assert detail.status_code == 200
    assert detail.json()["report_type"] == "close"


def test_quote_and_event_history_after_report_archive() -> None:
    client.get("/api/v1/reports/premarket?archive=true")

    quote_history = client.get("/api/v1/history/quotes/AAPL?limit=5")
    event_history = client.get("/api/v1/history/events?symbol=AAPL&minimum_importance=50&limit=5")

    assert quote_history.status_code == 200
    assert event_history.status_code == 200
    assert quote_history.json()
    assert event_history.json()


def test_watchlist_post_get_delete() -> None:
    payload = {"symbol": "AAPL", "display_name": "Apple", "market": "US"}
    add = client.post("/api/v1/watchlist", json=payload)
    listed = client.get("/api/v1/watchlist")
    removed = client.delete("/api/v1/watchlist/AAPL")

    assert add.status_code in {200, 409}
    assert listed.status_code == 200
    assert removed.status_code == 200
    assert "removed" in removed.json()


def test_invalid_symbol_and_limit_validation() -> None:
    bad_symbol = client.get("/api/v1/history/quotes/AAPL;DROP TABLE reports")
    high_limit = client.get("/api/v1/history/quotes/AAPL?limit=9999")
    bad_watchlist = client.post("/api/v1/watchlist", json={"symbol": "0700.HK", "display_name": "HK", "market": "HK"})

    assert bad_symbol.status_code == 422
    assert high_limit.status_code == 422
    assert bad_watchlist.status_code == 422


def test_api_responses_do_not_expose_sensitive_storage_fields() -> None:
    response = client.get("/api/v1/storage/status")
    text = response.text.lower()

    assert "password" not in text
    assert "token" not in text
    assert "api_key" not in text
    assert "market-radar.db" not in text
