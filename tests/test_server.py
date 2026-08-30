import sys
import types
from pathlib import Path

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
        return {"ok": True, "schema_version": "1.1", "mock": True}

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
    assert response.json() == {"ok": True, "schema_version": "1.2"}


def test_post_chart_forwards_engine_input(server_client):
    client, calls = server_client

    response = client.post("/chart", json=BODY)

    assert response.status_code == 200
    assert response.json() == {"ok": True, "schema_version": "1.1", "mock": True}
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


def test_post_chart_forwards_ziwei_day_divide(server_client):
    client, calls = server_client

    response = client.post("/chart", json={**BODY, "ziwei_day_divide": "current"})

    assert response.status_code == 200
    assert calls[0]["ziwei_day_divide"] == "current"


def test_invalid_ziwei_day_divide_returns_400(server_client):
    client, calls = server_client

    response = client.post("/chart", json={**BODY, "ziwei_day_divide": "tomorrow"})

    assert response.status_code == 400
    assert "ziwei_day_divide" in response.json()["detail"]
    assert calls == []


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


def test_sentry_initializes_when_dsn_configured(monkeypatch):
    fake_engine = types.ModuleType("scripts.chart_engine")
    fake_engine.INPUT = {"name": "範例", "target": "2025-01-01"}
    fake_engine.build_json = lambda inp: {"ok": True, "schema_version": "1.1"}
    fake_sentry = types.ModuleType("sentry_sdk")
    init_calls = []
    fake_sentry.init = lambda **kwargs: init_calls.append(kwargs)
    fake_sentry.capture_exception = lambda exc: None
    fake_sentry.flush = lambda timeout=None: None

    monkeypatch.setitem(sys.modules, "scripts.chart_engine", fake_engine)
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sentry)
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.invalid/1")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "ci")
    monkeypatch.setenv("SENTRY_RELEASE", "life-chart-engine@test")
    sys.modules.pop("server", None)

    import server  # noqa: F401

    assert len(init_calls) == 1
    options = init_calls[0]
    assert options["dsn"] == "https://public@example.invalid/1"
    assert options["environment"] == "ci"
    assert options["release"] == "life-chart-engine@test"
    assert options["send_default_pii"] is False
    assert options["include_local_variables"] is False
    assert options["traces_sample_rate"] == 0.0
    assert options["max_request_body_size"] == "never"
    assert callable(options["before_send"])
    assert options["before_send_transaction"] is options["before_send"]
    sys.modules.pop("server", None)


def test_sentry_captures_unhandled_chart_errors(monkeypatch):
    fake_engine = types.ModuleType("scripts.chart_engine")
    fake_engine.INPUT = {"name": "範例", "target": "2025-01-01"}

    def build_json(_inp):
        raise RuntimeError("ephemeris exploded")

    fake_engine.build_json = build_json
    fake_sentry = types.ModuleType("sentry_sdk")
    captured = []
    flushed = []
    fake_sentry.init = lambda **_kwargs: None
    fake_sentry.capture_exception = lambda exc: captured.append(exc)
    fake_sentry.flush = lambda timeout=None: flushed.append(timeout)

    monkeypatch.setitem(sys.modules, "scripts.chart_engine", fake_engine)
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sentry)
    monkeypatch.setenv("ENGINE_ALLOW_OPEN", "1")
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.invalid/1")
    sys.modules.pop("server", None)

    import server
    from fastapi.testclient import TestClient

    response = TestClient(server.app).post("/chart", json=BODY)

    assert response.status_code == 500
    assert response.json()["ok"] is False
    assert len(captured) == 1
    assert isinstance(captured[0], RuntimeError)
    assert flushed == []
    sys.modules.pop("server", None)


def test_sentry_scrubs_pii_and_secret_headers(monkeypatch):
    fake_engine = types.ModuleType("scripts.chart_engine")
    fake_engine.INPUT = {"name": "範例", "target": "2025-01-01"}
    fake_engine.build_json = lambda inp: {"ok": True, "schema_version": "1.1"}
    fake_sentry = types.ModuleType("sentry_sdk")
    init_calls = []
    fake_sentry.init = lambda **kwargs: init_calls.append(kwargs)
    fake_sentry.capture_exception = lambda exc: None
    fake_sentry.flush = lambda timeout=None: None

    monkeypatch.setitem(sys.modules, "scripts.chart_engine", fake_engine)
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sentry)
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.invalid/1")
    sys.modules.pop("server", None)

    import server  # noqa: F401

    before_send = init_calls[0]["before_send"]
    event = {
        "request": {
            "data": {"name": "Alice", "date": "1990-06-15"},
            "cookies": {"session": "secret"},
            "query_string": "chartHash=abc&token=secret",
            "headers": {
                "Authorization": "Bearer secret",
                "X-Engine-Key": "engine-secret",
                "Content-Type": "application/json",
            },
        },
        "exception": {
            "values": [
                {
                    "type": "RuntimeError",
                    "value": "failed for Alice born 1990-06-15",
                    "stacktrace": {
                        "frames": [
                            {"function": "chart", "vars": {"body": {"name": "Alice"}}}
                        ]
                    },
                }
            ]
        },
        "user": {"email": "person@example.com"},
    }

    scrubbed = before_send(event, {})

    assert "data" not in scrubbed["request"]
    assert "cookies" not in scrubbed["request"]
    assert "query_string" not in scrubbed["request"]
    assert "Authorization" not in scrubbed["request"]["headers"]
    assert "X-Engine-Key" not in scrubbed["request"]["headers"]
    assert scrubbed["request"]["headers"]["Content-Type"] == "application/json"
    assert scrubbed["exception"]["values"][0]["value"] == "[redacted]"
    assert "vars" not in scrubbed["exception"]["values"][0]["stacktrace"]["frames"][0]
    assert "user" not in scrubbed
    sys.modules.pop("server", None)


def test_sentry_deploy_contract_documents_runtime_env():
    root = Path(__file__).resolve().parents[1]

    assert "sentry-sdk" in (root / "requirements.txt").read_text()
    deploy_doc = (root / "DEPLOY-HETZNER.md").read_text()
    assert "SENTRY_DSN" in deploy_doc
    assert "SENTRY_ENVIRONMENT" in deploy_doc
    assert "SENTRY_RELEASE" in deploy_doc


@pytest.mark.parametrize(
    ("field", "value"),
    [("tz", 20), ("tz", -12.5), ("lat", 95), ("lat", -90.5), ("lon", 200), ("lon", -181)],
)
def test_out_of_range_numeric_values_return_400(server_client, field, value):
    client, calls = server_client

    response = client.post("/chart", json={**BODY, field: value})

    assert response.status_code == 400
    assert field in response.json()["detail"]
    assert calls == []


@pytest.mark.parametrize("payload_field", ["tz", "lat", "lon"])
def test_nonfinite_values_return_400(server_client, payload_field):
    client, calls = server_client

    string_inf = client.post("/chart", json={**BODY, payload_field: "1e999"})
    raw = {**BODY, payload_field: "__NAN__"}
    import json as _json

    nan_body = _json.dumps(raw, ensure_ascii=False).replace('"__NAN__"', "NaN")
    literal_nan = client.post(
        "/chart", content=nan_body, headers={"content-type": "application/json"}
    )

    assert string_inf.status_code == 400
    assert payload_field in string_inf.json()["detail"]
    assert literal_nan.status_code == 400
    assert payload_field in literal_nan.json()["detail"]
    assert calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("date", "1899-12-31"),
        ("date", "2101-01-01"),
        ("target", "1899-12-31"),
        ("target", "2101-01-01"),
    ],
)
def test_out_of_window_years_return_400(server_client, field, value):
    client, calls = server_client

    response = client.post("/chart", json={**BODY, field: value})

    assert response.status_code == 400
    assert field in response.json()["detail"]
    assert calls == []


def test_cli_and_http_reject_the_same_validation_decisions(server_client):
    import subprocess

    client, calls = server_client
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "chart_engine.py"
    rejected = [
        ("tz", "20"),
        ("lat", "95"),
        ("date", "1899-12-31"),
        ("target", "2101-01-01"),
        ("time", "25:99"),
    ]
    for field, value in rejected:
        http = client.post("/chart", json={**BODY, field: value})
        assert http.status_code == 400, (field, value)

        argv = [sys.executable, str(script), "--json"]
        cli_body = {**BODY, field: value}
        for k, v in cli_body.items():
            argv += [f"--{k}", str(v)]
        cli = subprocess.run(argv, cwd=root, capture_output=True, text=True, encoding="utf-8")
        assert cli.returncode == 2, (field, value, cli.stderr)
        assert cli.stdout == ""
        assert f"--{field}" in cli.stderr, (field, value, cli.stderr)
    assert calls == []


def test_non_string_ziwei_day_divide_returns_400_not_500(server_client):
    client, calls = server_client

    response = client.post("/chart", json={**BODY, "ziwei_day_divide": ["forward"]})

    assert response.status_code == 400
    assert "ziwei_day_divide" in response.json()["detail"]
    assert calls == []


def test_name_is_always_forwarded_as_string(server_client):
    client, calls = server_client

    null_name = client.post("/chart", json={**BODY, "name": None})
    dict_name = client.post("/chart", json={**BODY, "name": 42})

    assert null_name.status_code == 200
    assert dict_name.status_code == 200
    assert calls[0]["name"] == "範例"
    assert calls[1]["name"] == "42"


def test_non_string_gender_returns_400_not_500(server_client):
    client, calls = server_client

    response = client.post("/chart", json={**BODY, "gender": ["女"]})

    assert response.status_code == 400
    assert "gender" in response.json()["detail"]
    assert calls == []


def test_invalid_utf8_body_is_invalid_json(server_client):
    client, calls = server_client

    response = client.post(
        "/chart",
        content=b"\xff\xfe",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"] == "invalid_json"
    assert payload["field"] is None
    assert payload["detail"] == "body must be valid JSON"
    assert set(payload) == {"ok", "error", "field", "detail"}
    assert calls == []


def test_deeply_nested_body_is_invalid_json(server_client):
    client, calls = server_client
    body = b"[" * 10000 + b"]" * 10000

    response = client.post(
        "/chart",
        content=body,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_json"
    assert payload["field"] is None
    assert calls == []
