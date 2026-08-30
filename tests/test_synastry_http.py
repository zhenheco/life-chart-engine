"""E5 — engine HTTP contract for POST /synastry.

Covers: the full error taxonomy (six machine-parsable tokens, two fixed body
shapes, fixed decision order), the 422 typed-exception mapping, time-unknown
handling at the HTTP edge, CLI/HTTP deep-equality, idempotency, the
deploy_regression marker, and the AGENTS.md / DEPLOY-HETZNER.md contract docs.

Run only via the project venv:  .venv/bin/python -m pytest -q tests/test_synastry_http.py
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import synastry  # noqa: E402  (contract constants; production-owned, not hand-copied)

SCRIPT = ROOT / "scripts" / "chart_engine.py"
PY = sys.executable
SAMPLE = ROOT / "examples" / "sample-output.json"
SAMPLE_INPUT = ROOT / "examples" / "sample-input.json"
SAMPLE_SYNASTRY_INPUT = ROOT / "examples" / "sample-synastry-input.json"

# A side: same person the E1–E4 CLI tests use (non-empty arrays guaranteed).
PERSON_A = {
    "date": "1990-06-15",
    "time": "08:30",
    "tz": 8,
    "lat": 25.033,
    "lon": 121.5654,
    "gender": "女",
}
PERSON_B = {
    "date": "1988-03-20",
    "time": "09:15",
    "tz": 8,
    "lat": 25.0,
    "lon": 121.5,
    "gender": "男",
}
DUAL_BODY = {"person_a": PERSON_A, "person_b": PERSON_B}

# Polar datum (Svalbard-ish): verified against astronomy-engine==2.1.19 to fail
# Placidus at 08:30, 09:15 AND 12:00 local (= tz 0) on both 1990-06-15 and
# 1988-03-20. Convergence flips with sidereal time, so this exact coordinate is
# load-bearing: picking one that converges at 12:00 would make the
# time-unknown 422 test pass for the wrong reason.
POLAR_B = {"date": "1988-03-20", "tz": 0, "lat": 78.0, "lon": 15.0, "gender": "男"}

# Spec-pinned literals (contract values, not implementation constants).
UNAVAILABLE_FIXED = ["house_overlay", "angle_contacts", "hd_lines"]
MSG_COMPUTATION_UNSUPPORTED = "chart cannot be computed for the given coordinates"
MSG_INTERNAL = "synastry computation failed"
MSG_NOT_CONFIGURED = "ENGINE_API_KEY not configured"
METHODOLOGY_NOTE = (
    "紫微斗數沒有本引擎採用的合盤方法；兩人盤各自獨立計算，不做關係層級推論。"
)

TOP_LEVEL_KEYS = {
    "ok",
    "schema_version",
    "western",
    "human_design",
    "ziwei",
    "synastry",
    "evidence_completeness",
}
WESTERN_ARRAY_KEYS = {
    "aspects",
    "a_planets_in_b_houses",
    "b_planets_in_a_houses",
    "angle_contacts_a_to_b",
    "angle_contacts_b_to_a",
}
HD_KEYS = {"channel_connections", "center_states", "participants"}


@pytest.fixture
def client(monkeypatch):
    """Real server (no engine stubs), intentional keyless mode by default."""
    monkeypatch.setenv("ENGINE_ALLOW_OPEN", "1")
    monkeypatch.delenv("ENGINE_API_KEY", raising=False)
    sys.modules.pop("server", None)
    import server
    from fastapi.testclient import TestClient

    yield TestClient(server.app), server
    sys.modules.pop("server", None)


def _post(client, body=None, *, content=None, headers=None):
    if content is not None:
        return client.post(
            "/synastry", content=content,
            headers={"content-type": "application/json", **(headers or {})},
        )
    return client.post("/synastry", json=body, headers=headers or {})


def _cli(*args):
    return subprocess.run(
        [PY, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _cli_dual_args(time_b=None):
    args = [
        "--gender", "女", "--date", "1990-06-15", "--time", "08:30",
        "--tz", "8", "--lat", "25.033", "--lon", "121.5654",
        "--date-b", "1988-03-20", "--tz-b", "8", "--lat-b", "25.0",
        "--lon-b", "121.5", "--gender-b", "男",
    ]
    if time_b is not None:
        args += ["--time-b", time_b]
    args.append("--json")
    return args


def _raw_asgi_post(app, body: bytes, headers: list[tuple[bytes, bytes]]):
    """Drive the ASGI app with raw header bytes (httpx rejects non-ASCII)."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/synastry",
        "raw_path": b"/synastry",
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
            *headers,
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    sent = {"body": False}

    async def receive():
        if not sent["body"]:
            sent["body"] = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    result = {"status": None, "chunks": []}

    async def send(message):
        if message["type"] == "http.response.start":
            result["status"] = message["status"]
        elif message["type"] == "http.response.body":
            result["chunks"].append(message.get("body", b""))

    asyncio.run(app(scope, receive, send))
    return result["status"], b"".join(result["chunks"])


# ---------------------------------------------------------------------------
# Success shape
# ---------------------------------------------------------------------------

@pytest.mark.deploy_regression
def test_synastry_success_top_level_shape(client):
    http, _server = client

    response = _post(http, DUAL_BODY)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == TOP_LEVEL_KEYS
    assert body["ok"] is True
    assert body["schema_version"] == "1.2"
    assert set(body["synastry"]["western"]) == WESTERN_ARRAY_KEYS
    assert set(body["synastry"]["human_design"]) == HD_KEYS


def test_person_slots_are_empty_objects(client):
    http, _server = client

    body = _post(http, DUAL_BODY).json()

    for section in ("western", "human_design", "ziwei"):
        assert body[section]["person_a"] == {}, section
        assert body[section]["person_b"] == {}, section


def test_ziwei_not_computed_with_fixed_methodology_note(client):
    http, _server = client

    body = _post(http, DUAL_BODY).json()

    assert body["ziwei"]["status"] == "not_computed"
    assert body["ziwei"]["methodology_note"] == METHODOLOGY_NOTE
    assert body["ziwei"]["methodology_note"] == synastry.ZIWEI_METHODOLOGY_NOTE


def test_times_known_unavailable_empty_arrays_full(client):
    http, _server = client

    body = _post(http, DUAL_BODY).json()
    syn = body["synastry"]

    assert syn["unavailable"] == []
    # Non-empty guards: a mutation returning [] everywhere must not pass silently.
    for key in sorted(WESTERN_ARRAY_KEYS):
        assert syn["western"][key], f"synastry.western.{key} must be non-empty"
    assert syn["human_design"]["channel_connections"]
    assert len(syn["human_design"]["center_states"]) == 9
    assert set(syn["human_design"]["participants"]) == {"person_a", "person_b"}
    assert body["evidence_completeness"] == "full"


@pytest.mark.parametrize("variant", ["omitted", "null", "unknown"])
def test_time_unknown_variants(client, variant):
    http, _server = client
    person_b = dict(PERSON_B)
    if variant == "omitted":
        del person_b["time"]
    elif variant == "null":
        person_b["time"] = None
    else:
        person_b["time"] = "unknown"

    response = _post(http, {"person_a": PERSON_A, "person_b": person_b})

    assert response.status_code == 200
    body = response.json()
    syn = body["synastry"]
    assert syn["unavailable"] == UNAVAILABLE_FIXED
    assert syn["unavailable"] == list(synastry.UNAVAILABLE_TIME_UNKNOWN)
    # Keys stay present and empty while unavailable — parsers never branch on absence.
    for key in (
        "a_planets_in_b_houses",
        "b_planets_in_a_houses",
        "angle_contacts_a_to_b",
        "angle_contacts_b_to_a",
    ):
        assert syn["western"][key] == [], key
    assert syn["western"]["aspects"], "time-independent aspects must still be computed"
    assert body["evidence_completeness"] == "partial"


def test_malformed_time_is_400_not_time_unknown(client):
    http, _server = client
    body = {"person_a": {**PERSON_A, "time": "25:99"}, "person_b": PERSON_B}

    response = _post(http, body)

    # A silent downgrade to time-unknown would answer 200 with unavailable tokens.
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_input"
    assert payload["field"] == "person_a.time"
    assert "unavailable" not in payload


@pytest.mark.parametrize("bad_literal", ["Unknown", " unknown ", ""])
def test_unknown_literal_is_exact_lowercase_only(client, bad_literal):
    http, _server = client
    body = {"person_a": {**PERSON_A, "time": bad_literal}, "person_b": PERSON_B}

    response = _post(http, body)

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_input"
    assert payload["field"] == "person_a.time"


# ---------------------------------------------------------------------------
# Error table — row by row
# ---------------------------------------------------------------------------

def test_non_json_body_is_invalid_json(client):
    http, _server = client

    response = _post(http, content=b"{not json")

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"] == "invalid_json"
    assert payload["field"] is None


@pytest.mark.parametrize(
    "raw_body",
    [
        pytest.param(b'{"person_a": "\xff"}', id="invalid-utf8"),
        pytest.param(b"\xff\xfe{\"person_a\":", id="utf16-bom"),
    ],
)
def test_invalid_utf8_body_is_invalid_json_not_500(client, raw_body):
    """Both bodies must hit the endpoint's ``except ValueError`` branch.

    The first body is genuinely invalid UTF-8: json.loads(bytes) decodes with
    the detected encoding and raises UnicodeDecodeError — a ValueError but NOT
    a JSONDecodeError, so an ``except JSONDecodeError`` mutation must turn
    this case red. The second body starts with a UTF-16 LE BOM, which
    json.detect_encoding honours: it decodes cleanly and raises JSONDecodeError
    instead. Keeping both proves the wider ``except ValueError`` is load-bearing.
    """
    http, _server = client

    response = _post(http, content=raw_body)

    assert response.status_code == 400, response.text
    payload = response.json()
    assert payload["error"] == "invalid_json"
    assert payload["field"] is None


def test_deeply_nested_body_is_invalid_json_not_bare_500(client):
    """A parser RecursionError must stay inside the six-token envelope.

    json.loads raises RecursionError (not a ValueError) once nesting exceeds
    the recursion limit (~20 KB of brackets is enough). Without catching it,
    the endpoint leaks a bare, non-JSON 500 — a retryable status for an
    input-deterministic failure (spec: parse-stage errors are 400
    invalid_json, not retryable).
    """
    http, _server = client
    body = b'{"person_a":' + b"[" * 10000 + b"]" * 10000 + b"}"

    response = _post(http, content=body)

    assert response.status_code == 400, response.text
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"] == "invalid_json"
    assert payload["field"] is None
    assert set(payload) == {"ok", "error", "field", "detail"}


def test_missing_person_b_is_invalid_input_field_person_b(client):
    http, _server = client

    response = _post(http, {"person_a": PERSON_A})

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_input"
    assert payload["field"] == "person_b"


def test_person_a_not_object_is_invalid_input_not_500(client):
    http, _server = client

    response = _post(http, {"person_a": ["not", "an", "object"], "person_b": PERSON_B})

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_input"
    assert payload["field"] == "person_a"


def test_body_not_object_is_invalid_input_field_person_a(client):
    http, _server = client

    response = _post(http, content=b"[1, 2, 3]")

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_input"
    assert payload["field"] == "person_a"


def test_missing_date_is_prefixed_person_a_date(client):
    http, _server = client
    person_a = dict(PERSON_A)
    del person_a["date"]

    response = _post(http, {"person_a": person_a, "person_b": PERSON_B})

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_input"
    assert payload["field"] == "person_a.date"


@pytest.mark.parametrize(
    ("body", "expected_field"),
    [
        pytest.param(
            # Both sides miss `date`: exactly one error, naming person_a.
            # Reversing the validation loop's tuple reports person_b.date.
            {
                "person_a": {k: v for k, v in PERSON_A.items() if k != "date"},
                "person_b": {k: v for k, v in PERSON_B.items() if k != "date"},
            },
            "person_a.date",
            id="both-missing-date",
        ),
        pytest.param(
            # Both person slots absent: the shape-check loop must also report
            # person_a first. Reversing that loop's tuple reports person_b.
            {},
            "person_a",
            id="both-slots-missing",
        ),
    ],
)
def test_first_error_is_person_a_when_both_sides_invalid(
    client, body, expected_field
):
    http, _server = client

    response = _post(http, body)

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_input"
    assert payload["field"] == expected_field


def test_lat_out_of_range_is_invalid_input(client):
    http, _server = client

    response = _post(
        http, {"person_a": {**PERSON_A, "lat": 95}, "person_b": PERSON_B}
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_input"
    assert payload["field"] == "person_a.lat"


def test_huge_integer_tz_is_invalid_input_not_500(client):
    """A 400-digit JSON int makes float() raise OverflowError — a pure input
    error must surface as 400 invalid_input, not as a server-error 500 that
    an authorized caller could weaponize into Sentry alerts."""
    http, _server = client

    response = _post(
        http,
        {"person_a": {**PERSON_A, "tz": int("1" * 400)}, "person_b": PERSON_B},
    )

    assert response.status_code == 400, response.text
    payload = response.json()
    assert payload["error"] == "invalid_input"
    assert payload["field"] == "person_a.tz"


def test_same_person_twice_is_computed_normally(client):
    http, _server = client

    response = _post(http, {"person_a": PERSON_A, "person_b": dict(PERSON_A)})

    assert response.status_code == 200
    body = response.json()
    aspects = body["synastry"]["western"]["aspects"]
    assert aspects, "identical persons still produce orb-0 conjunctions"
    assert any(ev["raw_fact"]["orb"] == 0.0 for ev in aspects)


# ---------------------------------------------------------------------------
# Decision order
# ---------------------------------------------------------------------------

def test_not_configured_wins_over_invalid_json(client, monkeypatch):
    http, _server = client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.delenv("ENGINE_API_KEY", raising=False)

    response = _post(http, content=b"{not json")

    assert response.status_code == 503, response.text
    assert response.status_code != 400
    payload = response.json()
    assert payload == {"ok": False, "error": "not_configured", "message": MSG_NOT_CONFIGURED}


def test_unauthorized_wins_over_invalid_json(client, monkeypatch):
    http, _server = client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.setenv("ENGINE_API_KEY", "secret")

    response = _post(http, content=b"{not json", headers={"X-Engine-Key": "wrong"})

    assert response.status_code == 401
    payload = response.json()
    assert payload["error"] == "unauthorized"


# ---------------------------------------------------------------------------
# 422 polar coordinates — typed mapping, fixed message, exact key sets
# ---------------------------------------------------------------------------

def test_polar_coordinates_return_422_computation_unsupported(client):
    http, _server = client
    body = {"person_a": PERSON_A, "person_b": {**POLAR_B, "time": "09:15"}}

    response = _post(http, body)

    assert response.status_code == 422, response.text
    assert response.status_code != 500
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"] == "computation_unsupported"
    assert payload["error"] == synastry.ERROR_COMPUTATION_UNSUPPORTED
    assert payload["message"] == MSG_COMPUTATION_UNSUPPORTED
    assert payload["message"] == synastry.MESSAGE_COMPUTATION_UNSUPPORTED
    assert "placidus undefined at high latitude" not in payload["message"]
    assert "placidus" not in payload["message"]


def test_422_body_key_set_is_exactly_ok_error_message(client):
    http, _server = client
    body = {"person_a": PERSON_A, "person_b": {**POLAR_B, "time": "09:15"}}

    payload = _post(http, body).json()

    assert set(payload) == {"ok", "error", "message"}


def test_400_body_key_set_is_exactly_ok_error_field_detail(client):
    http, _server = client
    person_a = dict(PERSON_A)
    del person_a["date"]

    payload = _post(http, {"person_a": person_a, "person_b": PERSON_B}).json()

    assert set(payload) == {"ok", "error", "field", "detail"}


def test_422_maps_exception_type_not_message(client, monkeypatch):
    http, server_mod = client
    # Import via the same package path the server uses, so the except clause
    # and the injected exception share one class object.
    from scripts.ephemeris import ComputationUnsupportedError

    def raise_unsupported(_a, _b):
        raise ComputationUnsupportedError("a totally different message 完全不同")

    monkeypatch.setattr(server_mod, "build_synastry_json", raise_unsupported)

    response = _post(http, DUAL_BODY)

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"] == "computation_unsupported"
    assert payload["message"] == MSG_COMPUTATION_UNSUPPORTED
    assert "totally different" not in payload["message"]


def test_plain_valueerror_maps_to_500_fixed_message(client, monkeypatch):
    http, server_mod = client

    def raise_generic(_a, _b):
        raise ValueError("boom secret internals")

    monkeypatch.setattr(server_mod, "build_synastry_json", raise_generic)

    response = _post(http, DUAL_BODY)

    assert response.status_code == 500
    payload = response.json()
    assert payload == {
        "ok": False,
        "error": "internal_error",
        "message": MSG_INTERNAL,
    }
    assert payload["message"] == synastry.MESSAGE_INTERNAL
    assert "boom" not in payload["message"]


def test_validate_input_non_valueerror_is_500_fixed_envelope(client, monkeypatch):
    """A non-ValueError escaping validate_input must not bypass the six-token
    envelope as a generic FastAPI 500 — the contract's internal_error shape
    still applies."""
    http, server_mod = client

    def raise_type_error(_body, allow_unknown_time=False):
        raise TypeError("pathological input type")

    monkeypatch.setattr(server_mod, "validate_input", raise_type_error)

    response = _post(http, DUAL_BODY)

    assert response.status_code == 500, response.text
    payload = response.json()
    assert payload == {
        "ok": False,
        "error": "internal_error",
        "message": MSG_INTERNAL,
    }
    assert payload["message"] == synastry.MESSAGE_INTERNAL
    assert "pathological" not in payload["message"]


def test_polar_with_b_time_unknown_still_422(client):
    """Houses are still computed at estimated 12:00 — no 200-partial downgrade.

    POLAR_B fails Placidus at 12:00 by construction; a mutation that skips
    house computation for time-unknown sides would return 200 here.
    """
    http, _server = client
    body = {"person_a": PERSON_A, "person_b": dict(POLAR_B)}  # time omitted

    response = _post(http, body)

    assert response.status_code == 422, response.text
    assert response.json()["error"] == "computation_unsupported"


def test_polar_with_a_time_unknown_still_422(client):
    http, _server = client
    person_a = dict(PERSON_A)
    del person_a["time"]

    response = _post(http, {"person_a": person_a, "person_b": {**POLAR_B, "time": "09:15"}})

    assert response.status_code == 422, response.text
    assert response.json()["error"] == "computation_unsupported"


# ---------------------------------------------------------------------------
# Auth: X-Engine-Key reuse, fail-closed, non-ASCII headers
# ---------------------------------------------------------------------------

def test_missing_engine_key_header_is_401_not_500(client, monkeypatch):
    http, _server = client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.setenv("ENGINE_API_KEY", "secret")

    response = _post(http, DUAL_BODY)  # no X-Engine-Key header at all

    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["error"] == "unauthorized"
    assert payload["field"] is None
    assert set(payload) == {"ok", "error", "field", "detail"}


def test_non_ascii_engine_key_header_is_401_not_500(client, monkeypatch):
    http, server_mod = client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.setenv("ENGINE_API_KEY", "secret")

    # Raw ASGI: Starlette decodes header bytes as latin-1, so 0xff arrives as a
    # non-ASCII str. compare_digest's str form would TypeError → 500 without
    # the bytes comparison.
    status, raw = _raw_asgi_post(
        server_mod.app,
        json.dumps(DUAL_BODY).encode("utf-8"),
        [(b"x-engine-key", b"key-\xff")],
    )

    assert status == 401, raw
    payload = json.loads(raw)
    assert payload["error"] == "unauthorized"


def test_non_ascii_configured_key_accepts_correct_utf8_header(client, monkeypatch):
    """A non-ASCII ENGINE_API_KEY must not be a 100% outage.

    Starlette hands the header over as a latin-1-decoded str, so the server
    must re-encode it as latin-1 to recover the exact wire bytes before
    comparing against the configured key's UTF-8 bytes. Re-encoding the
    header as UTF-8 instead mangles every non-ASCII byte and rejects even
    the correct key.
    """
    http, server_mod = client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.setenv("ENGINE_API_KEY", "密鑰secret")

    status, raw = _raw_asgi_post(
        server_mod.app,
        json.dumps(DUAL_BODY).encode("utf-8"),
        [(b"x-engine-key", "密鑰secret".encode("utf-8"))],
    )

    assert status == 200, raw
    assert json.loads(raw)["ok"] is True

    wrong_status, wrong_raw = _raw_asgi_post(
        server_mod.app,
        json.dumps(DUAL_BODY).encode("utf-8"),
        [(b"x-engine-key", "wrong-密鑰".encode("utf-8"))],
    )

    assert wrong_status == 401, wrong_raw
    assert json.loads(wrong_raw)["error"] == "unauthorized"


def test_surrogate_escaped_configured_key_is_401_not_500(client, monkeypatch):
    """A non-UTF-8 ENGINE_API_KEY must not be a 100% outage either.

    On POSIX, os.environ surrogate-escapes env values that are not valid
    UTF-8, so the configured key can contain lone surrogates. Re-encoding it
    as plain UTF-8 raises UnicodeEncodeError outside every handler try — a
    bare 500 on both endpoints — instead of the 401 the old code returned.
    With surrogateescape the original bytes round-trip, and any header value
    must stay a 401 envelope, never an exception.
    """
    http, server_mod = client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.setenv("ENGINE_API_KEY", b"k\xff".decode("utf-8", "surrogateescape"))

    response = _post(http, DUAL_BODY, headers={"X-Engine-Key": "whatever"})

    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["error"] == "unauthorized"
    assert payload["field"] is None
    assert set(payload) == {"ok", "error", "field", "detail"}

    # Non-ASCII header bytes against a surrogate-escaped key: same envelope.
    status, raw = _raw_asgi_post(
        server_mod.app,
        json.dumps(DUAL_BODY).encode("utf-8"),
        [(b"x-engine-key", b"key-\xff")],
    )

    assert status == 401, raw
    raw_payload = json.loads(raw)
    assert raw_payload["error"] == "unauthorized"
    assert set(raw_payload) == {"ok", "error", "field", "detail"}

    # /chart shares _auth_failure: it must return the 401 envelope, not raise.
    chart = http.post(
        "/chart",
        json={
            "date": "1990-06-15", "time": "08:30", "tz": 8,
            "lat": 25.0, "lon": 121.5, "gender": "女",
        },
        headers={"X-Engine-Key": "whatever"},
    )

    assert chart.status_code == 401, chart.text
    assert chart.json() == {
        "ok": False,
        "error": "unauthorized",
        "field": None,
        "detail": "missing or incorrect X-Engine-Key",
    }


def test_wrong_key_is_401_unauthorized(client, monkeypatch):
    http, _server = client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.setenv("ENGINE_API_KEY", "secret")

    response = _post(http, DUAL_BODY, headers={"X-Engine-Key": "wrong"})

    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized"


def test_correct_key_is_accepted(client, monkeypatch):
    http, _server = client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.setenv("ENGINE_API_KEY", "secret")

    response = _post(http, DUAL_BODY, headers={"X-Engine-Key": "secret"})

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_no_key_configured_is_503_not_configured(client, monkeypatch):
    http, _server = client
    monkeypatch.delenv("ENGINE_ALLOW_OPEN", raising=False)
    monkeypatch.delenv("ENGINE_API_KEY", raising=False)

    response = _post(http, DUAL_BODY)

    assert response.status_code == 503
    payload = response.json()
    assert payload["error"] == "not_configured"
    assert payload["message"] == MSG_NOT_CONFIGURED
    assert set(payload) == {"ok", "error", "message"}


def test_allow_open_bypasses_key(client):
    http, _server = client  # fixture: ENGINE_ALLOW_OPEN=1, no ENGINE_API_KEY

    response = _post(http, DUAL_BODY)

    assert response.status_code == 200
    assert response.json()["ok"] is True


# ---------------------------------------------------------------------------
# No per-request Node dependency
# ---------------------------------------------------------------------------

def test_synastry_succeeds_without_node_on_path(client, tmp_path, monkeypatch):
    http, _server = client
    bindir = tmp_path / "bin"
    bindir.mkdir()
    monkeypatch.setenv("PATH", str(bindir))

    response = _post(http, DUAL_BODY)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["synastry"]["western"]["aspects"]


# ---------------------------------------------------------------------------
# CLI dual-mode runtime failure contract
# ---------------------------------------------------------------------------

def test_cli_dual_polar_emits_computation_unsupported_envelope():
    result = _cli(
        "--gender", "女", "--date", "1990-06-15", "--time", "08:30",
        "--tz", "8", "--lat", "25.033", "--lon", "121.5654",
        "--date-b", POLAR_B["date"], "--time-b", "09:15", "--tz-b", "0",
        "--lat-b", "78.0", "--lon-b", "15.0", "--gender-b", "男",
        "--json",
    )

    assert result.returncode == 1, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert set(payload) == {"ok", "error", "message", "schema_version"}
    assert payload["ok"] is False
    assert payload["error"] == synastry.ERROR_COMPUTATION_UNSUPPORTED
    assert payload["message"] == synastry.MESSAGE_COMPUTATION_UNSUPPORTED
    assert payload["schema_version"] == "1.2"
    # str(exc) must not leak into the fixed message
    assert "placidus" not in payload["message"]
    assert "converge" not in payload["message"]


# ---------------------------------------------------------------------------
# Accepted-but-ignored person options, idempotency, CLI/HTTP parity
# ---------------------------------------------------------------------------

def test_name_target_ziwei_day_divide_accepted_without_effect(client):
    http, _server = client
    extras = {"name": "Alice", "target": "2024-02-02", "ziwei_day_divide": "current"}
    with_extras = {
        "person_a": {**PERSON_A, **extras, "name": "Alice"},
        "person_b": {**PERSON_B, **extras, "name": "Bob"},
    }

    plain = _post(http, DUAL_BODY)
    decorated = _post(http, with_extras)

    assert plain.status_code == 200
    assert decorated.status_code == 200, decorated.text
    assert decorated.content == plain.content


def test_idempotent_same_body_byte_identical(client):
    http, _server = client

    first = _post(http, DUAL_BODY)
    second = _post(http, DUAL_BODY)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.content == second.content


def test_cli_and_http_deep_equal_times_known(client):
    http, _server = client

    cli = _cli(*_cli_dual_args(time_b="09:15"))
    assert cli.returncode == 0, cli.stderr or cli.stdout
    response = _post(http, DUAL_BODY)
    assert response.status_code == 200

    assert json.loads(cli.stdout) == response.json()


def test_cli_and_http_deep_equal_time_unknown(client):
    http, _server = client
    person_b = dict(PERSON_B)
    del person_b["time"]

    cli = _cli(*_cli_dual_args(time_b=None))
    assert cli.returncode == 0, cli.stderr or cli.stdout
    response = _post(http, {"person_a": PERSON_A, "person_b": person_b})
    assert response.status_code == 200

    assert json.loads(cli.stdout) == response.json()


# ---------------------------------------------------------------------------
# /health and /chart regression (deploy_regression: platform-independent)
# ---------------------------------------------------------------------------

@pytest.mark.deploy_regression
def test_health_reports_ok_and_schema_version(client):
    http, _server = client

    response = http.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["schema_version"] == "1.2"
    assert set(body) == {"ok", "schema_version"}


@pytest.mark.deploy_regression
def test_chart_success_deep_equal_sample_excluding_schema_version(client):
    http, _server = client

    # Same fixture DEPLOY-HETZNER.md §6b POSTs to the live host: one pinned
    # request body, one pinned golden output. Reading it here keeps the
    # fixture ↔ examples/sample-output.json correspondence enforced.
    request_body = json.loads(SAMPLE_INPUT.read_text(encoding="utf-8"))
    response = http.post("/chart", json=request_body)

    assert response.status_code == 200, response.text
    got = response.json()
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    got.pop("schema_version", None)
    sample.pop("schema_version", None)
    assert got == sample


# ---------------------------------------------------------------------------
# Contract documentation and deploy-regression guard
# ---------------------------------------------------------------------------

def test_agents_md_documents_synastry_methods_tokens_and_retry_lists():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    for method in (
        "synastry_aspect",
        "house_overlay",
        "angle_contact",
        "hd_channel_connection",
        "hd_center_state",
    ):
        assert method in text, f"AGENTS.md missing method name {method}"
    for token in (
        "invalid_json",
        "invalid_input",
        "unauthorized",
        "not_configured",
        "computation_unsupported",
        "internal_error",
    ):
        assert token in text, f"AGENTS.md missing error token {token}"
    assert "POST /synastry" in text

    assert "**Not retryable**" in text
    assert "**Retryable**" in text
    not_retryable = text.split("**Not retryable**", 1)[1].split("**Retryable**", 1)[0]
    assert "computation_unsupported" in not_retryable
    retryable = text.split("**Retryable**", 1)[1]
    assert "internal_error" in retryable


def test_agents_md_documents_b_flags_and_unknown_time():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    for flag in (
        "--date-b",
        "--time-b",
        "--tz-b",
        "--lat-b",
        "--lon-b",
        "--gender-b",
        "--name-b",
    ):
        assert flag in text, f"AGENTS.md missing flag {flag}"
    assert '"unknown"' in text
    assert "`null`" in text
    # --example ↔ -b mutual exclusion must stay documented. Pin each
    # statement's unique phrase: plain "any `-b` flag" is also satisfied by
    # the mode-entry sentence and "`--example`" appears in unrelated rows,
    # so neither alone proves the exclusion is still there.
    assert "Mutually exclusive with all six birth flags and any `-b` flag" in text
    assert "`--example` is mutually exclusive with any `-b` flag" in text


def test_deploy_doc_contains_regression_command():
    text = (ROOT / "DEPLOY-HETZNER.md").read_text(encoding="utf-8")

    assert "pytest -m deploy_regression -r s" in text


def test_deploy_doc_contains_live_container_post_verification():
    """§6b must include a check that actually touches the deployed container.

    The in-checkout marker only proves the source contract; a live POST of the
    pinned sample input, deep-compared against the pinned golden output, is
    what catches an older build still being served. The schema_version check
    must live INSIDE the comparison as an assertion: the only diff between
    the pre-1.2 golden and the current one is that line, so popping it from
    both sides before comparing lets a stale build pass the deep-equal.
    """
    text = (ROOT / "DEPLOY-HETZNER.md").read_text(encoding="utf-8")

    # curl -f: without it a 401/502/503 error body is written to
    # /tmp/live-chart.json and misreported as deploy drift (§4 uses -fsS).
    assert "curl -fsS -X POST https://engine-life.aicycle.cc/chart" in text
    # Fresh-shell guard: the header variable only exists if §2/§4 ran in the
    # same shell (§2 pins the analogous test -n "$ENGINE_API_KEY").
    assert 'test -n "$ENGINE_AUTH_HEADER"' in text
    assert 'assert live_sv == "1.2"' in text
    assert "examples/sample-input.json" in text
    assert "examples/sample-output.json" in text
    # The marker test itself posts the same fixture, so it must exist.
    assert SAMPLE_INPUT.is_file()


def test_deploy_doc_contains_live_synastry_smoke():
    """§6b must smoke the live POST /synastry, not just /chart.

    A missing /synastry endpoint is exactly what hands existing paid synastry
    customers 502/503 once life-web goes live, so the doc must POST a pinned
    two-person body to the live host and assert the success envelope.
    """
    text = (ROOT / "DEPLOY-HETZNER.md").read_text(encoding="utf-8")

    assert "curl -fsS -X POST https://engine-life.aicycle.cc/synastry" in text
    assert "examples/sample-synastry-input.json" in text
    assert 'live["ok"] is True' in text
    assert '"evidence_completeness" in live' in text

    # The doc fixture must exist and stay the same two-person body the
    # deploy_regression synastry shape test posts.
    assert SAMPLE_SYNASTRY_INPUT.is_file()
    fixture = json.loads(SAMPLE_SYNASTRY_INPUT.read_text(encoding="utf-8"))
    assert fixture == DUAL_BODY


def test_golden_provenance_records_regeneration_date_and_schema_version():
    text = (ROOT / "tests" / "fixtures" / "GOLDEN_PROVENANCE.md").read_text(encoding="utf-8")

    assert "schema_version" in text
    assert "2026-08-06" in text  # the 1.1 → 1.2 regeneration date


def test_pyproject_registers_deploy_regression_marker():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "[tool.pytest.ini_options]" in text
    assert "deploy_regression" in text


def test_platform_gated_golden_tests_are_not_deploy_regression():
    """The byte-identity tests skip off the capture platform — a skip is no
    deploy evidence, so they must never carry the marker (spec §風險 4)."""
    for rel in (
        "tests/test_engine_astronomy_contract.py",
        "tests/test_synastry_cli.py",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "deploy_regression" not in text, rel
