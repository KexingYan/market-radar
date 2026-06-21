from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["environment"] == "local"
    assert payload["provider"] == "mock"
    assert payload["external_network_enabled"] is False
    assert payload["trading_enabled"] is False
