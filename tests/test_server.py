import sys
import types

import pytest


BODY = {
    "date": "1990-06-15",
    "time": "08:30",
    "tz": 8,
    "lat": 25.0,
    "lon": 121.5,
    "gender": "女",
}


@pytest.fixture
def server_client(monkeypatch):
    calls = []
    fake_engine = types.ModuleType("scripts.chart_engine")
    fake_engine.INPUT = {"name": "範例", "target": "2025-01-01"}

    def build_json(inp):
        calls.append(inp)
        return {"ok": True, "schema_version": "1.0", "mock": True}

    fake_engine.build_json = build_json
    monkeypatch.setitem(sys.modules, "scripts.chart_engine", fake_engine)
    # These tests exercise input forwarding/validation, not auth: run in the
    # intentional keyless mode. Auth + fail-closed are covered by their own tests.
    monkeypatch.setenv("ENGINE_ALLOW_OPEN", "1")
    sys.modules.pop("server", None)

    import server
    from fastapi.testclient import TestClient

    yield TestClient(server.app), calls
    sys.modules.pop("server", None)


def test_health(server_client):
    client, _ = server_client

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_post_chart_forwards_engine_input(server_client):
    client, calls = server_client

    response = client.post("/chart", json=BODY)

    assert response.status_code == 200
    assert response.json() == {"ok": True, "schema_version": "1.0", "mock": True}
    assert calls == [
        {
            "name": "範例",
            "gender": "女",
            "date": (1990, 6, 15),
            "time": (8, 30),
            "tz_offset": 8.0,
            "lat": 25.0,
            "lon": 121.5,
            "target": "2025-01-01",
        }
    ]


def test_missing_required_field_returns_400(server_client):
    client, calls = server_client
    body = dict(BODY)
    del body["lon"]

    response = client.post("/chart", json=body)

    assert response.status_code == 400
    assert "lon" in response.json()["detail"]
    assert calls == []


def test_invalid_gender_returns_400(server_client):
    client, calls = server_client

    response = client.post("/chart", json={**BODY, "gender": "other"})

    assert response.status_code == 400
    assert "gender" in response.json()["detail"]
    assert calls == []


def test_invalid_target_returns_400(server_client):
    client, calls = server_client

    response = client.post("/chart", json={**BODY, "target": "not-a-date"})

    assert response.status_code == 400
    assert "target" in response.json()["detail"]
    assert calls == []


def test_invalid_time_returns_400(server_client):
    client, calls = server_client

    response = client.post("/chart", json={**BODY, "time": "aa:bb"})

    assert response.status_code == 400
    assert "time" in response.json()["detail"]
    assert calls == []


def test_api_key_rejects_missing_or_wrong_header(server_client, monkeypatch):
    client, calls = server_client
    monkeypatch.setenv("ENGINE_API_KEY", "secret")

    missing = client.post("/chart", json=BODY)
    wrong = client.post("/chart", json=BODY, headers={"X-Engine-Key": "bad"})

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert calls == []


def test_api_key_accepts_matching_header(server_client, monkeypatch):
    client, calls = server_client
    monkeypatch.setenv("ENGINE_API_KEY", "secret")

    response = client.post("/chart", json=BODY, headers={"X-Engine-Key": "secret"})

    assert response.status_code == 200
    assert len(calls) == 1


def test_fail_closed_when_no_key_configured(server_client, monkeypatch):
    # No ENGINE_API_KEY and no explicit ENGINE_ALLOW_OPEN => refuse, so a
    # misconfigured public deploy is not an open compute endpoint.
    client, calls = server_client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.delenv("ENGINE_API_KEY", raising=False)

    response = client.post("/chart", json=BODY)

    assert response.status_code == 503
    assert calls == []
