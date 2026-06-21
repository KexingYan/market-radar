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


def test_quotes_list_returns_mock_quotes() -> None:
    response = client.get("/api/v1/quotes")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 6
    assert all(item["provider"] == "mock" for item in payload)
    assert all("timestamp" in item for item in payload)
    assert all("is_delayed" in item for item in payload)


def test_existing_quote_returns_200() -> None:
    response = client.get("/api/v1/quotes/AAPL")

    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"


def test_missing_quote_returns_404() -> None:
    response = client.get("/api/v1/quotes/DOES-NOT-EXIST")

    assert response.status_code == 404


def test_quote_response_has_no_sensitive_fields() -> None:
    response = client.get("/api/v1/quotes/AAPL")

    assert response.status_code == 200
    lowered_keys = {key.lower() for key in response.json().keys()}
    assert not any(part in key for part in SENSITIVE_FIELD_PARTS for key in lowered_keys)
