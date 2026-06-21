from fastapi.testclient import TestClient
import httpx
import socket
import urllib.request

from app.main import app
from app.providers.registry import event_provider, quote_provider


client = TestClient(app)


def test_health_declares_network_and_trading_disabled() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock"
    assert payload["external_network_enabled"] is False
    assert payload["trading_enabled"] is False


def test_routes_use_mock_provider_instances() -> None:
    assert quote_provider.configured == "mock"
    assert quote_provider.primary is None
    assert event_provider.configured == "mock"
    assert event_provider.primary is None


def test_api_responses_do_not_expose_remote_provider() -> None:
    quotes_response = client.get("/api/v1/quotes")
    events_response = client.get("/api/v1/events")

    assert quotes_response.status_code == 200
    assert events_response.status_code == 200
    assert {item["provider"] for item in quotes_response.json()} == {"mock"}
    assert {item["source_name"] for item in events_response.json()} == {"Mock Data Provider"}


def test_provider_status_defaults_to_mock() -> None:
    response = client.get("/api/v1/providers/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["free_only_mode"] is True
    assert payload["quotes"]["configured"] == "mock"
    assert payload["quotes"]["active"] == "mock"
    assert payload["events"]["configured"] == "mock"
    assert payload["events"]["active"] == "mock"
    assert payload["trading_enabled"] is False
    assert payload["paid_data_enabled"] is False


def test_default_api_does_not_attempt_real_network(monkeypatch) -> None:
    original_connect = socket.socket.connect

    def fail_network(*args, **kwargs):
        raise AssertionError("real network access is not allowed in default tests")

    def guarded_connect(sock, address):
        host, port = address
        if host in {"127.0.0.1", "::1", "localhost"} and port != 11111:
            return original_connect(sock, address)
        raise AssertionError(f"blocked network access to {host}:{port}")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_network)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", fail_network)

    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/providers/status").status_code == 200
    assert client.get("/api/v1/quotes").status_code == 200
    assert client.get("/api/v1/events").status_code == 200
