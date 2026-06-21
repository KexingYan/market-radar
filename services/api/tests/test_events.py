from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

SENSITIVE_FIELD_PARTS = [
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "account_id",
    "broker_password",
    "trading_password",
]


def test_events_list_returns_mock_events() -> None:
    response = client.get("/api/v1/events")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 8
    assert all(item["is_mock"] is True for item in payload)
    assert all(item["source_name"] == "Mock Data Provider" for item in payload)


def test_event_importance_scores_are_in_range() -> None:
    response = client.get("/api/v1/events")

    assert response.status_code == 200
    payload = response.json()
    assert all(0 <= item["importance_score"] <= 100 for item in payload)


def test_event_reliability_and_confidence_are_in_range() -> None:
    response = client.get("/api/v1/events")

    assert response.status_code == 200
    payload = response.json()
    assert all(0 <= item["reliability_score"] <= 100 for item in payload)
    assert all(0 <= item["confidence"] <= 1 for item in payload)


def test_missing_event_returns_404() -> None:
    response = client.get("/api/v1/events/not-found")

    assert response.status_code == 404


def test_event_response_has_no_sensitive_fields() -> None:
    response = client.get("/api/v1/events/mock-event-001")

    assert response.status_code == 200
    lowered_keys = {key.lower() for key in response.json().keys()}
    assert not any(part in key for part in SENSITIVE_FIELD_PARTS for key in lowered_keys)


def test_filings_endpoint_defaults_to_mock_without_live_sec() -> None:
    response = client.get("/api/v1/filings?symbols=AAPL&forms=8-K&limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert all(item["is_mock"] is True for item in payload)
    assert all(item["source_name"] == "Mock Data Provider" for item in payload)
