import hmac
import os
from json import JSONDecodeError
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from scripts.chart_engine import build_json
from scripts.ephemeris import ComputationUnsupportedError
from scripts.synastry import (
    ERROR_COMPUTATION_UNSUPPORTED,
    ERROR_INTERNAL,
    MESSAGE_COMPUTATION_UNSUPPORTED,
    MESSAGE_INTERNAL,
    build_synastry_json,
)
from scripts.validation import validate_input
from sentry_config import capture_exception, init_sentry


init_sentry()

app = FastAPI(title="life-chart-engine")

MESSAGE_NOT_CONFIGURED = "ENGINE_API_KEY not configured"


@app.get("/health")
def health():
    return {"ok": True, "schema_version": "1.2"}


@app.post("/chart")
async def chart(request: Request, x_engine_key: str | None = Header(default=None)):
    _require_key(x_engine_key)
    try:
        body = await request.json()
    except JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON body") from exc
    try:
        return build_json(_engine_input(body))
    except HTTPException:
        raise  # 400s from _engine_input pass through unchanged
    except Exception as exc:  # build_json / ephemeris edge input
        capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(exc), "schema_version": "1.2"},
        )


@app.post("/synastry")
async def synastry_endpoint(
    request: Request, x_engine_key: str | None = Header(default=None)
):
    # Decision order is fixed (spec §完整度、錯誤與安全): not_configured →
    # unauthorized → invalid_json → invalid_input → computation_unsupported →
    # internal_error. The body is read only after key verification, so an
    # unauthenticated caller cannot use body size to amplify resource use.
    failure = _auth_failure(x_engine_key)
    if failure == "not_configured":
        return _message_error(503, "not_configured", MESSAGE_NOT_CONFIGURED)
    if failure == "unauthorized":
        return _input_error(401, "unauthorized", None, "missing or incorrect X-Engine-Key")

    try:
        body = await request.json()
    except (ValueError, RecursionError):
        # JSONDecodeError, UnicodeDecodeError (invalid UTF-8), and
        # RecursionError (JSON nested deeper than the parser's recursion
        # limit). Every parse-stage failure is input-deterministic, so it maps
        # to the non-retryable 400 invalid_json — never a bare 500.
        return _input_error(400, "invalid_json", None, "body must be valid JSON")

    if not isinstance(body, dict):
        return _input_error(
            400, "invalid_input", "person_a",
            "body must be a JSON object with person_a and person_b",
        )

    for person_key in ("person_a", "person_b"):
        if not isinstance(body.get(person_key), dict):
            detail = (
                f"{person_key}: must be a JSON object"
                if person_key in body
                else f"{person_key}: is required"
            )
            return _input_error(400, "invalid_input", person_key, detail)

    inputs: dict[str, dict[str, Any]] = {}
    try:
        for person_key in ("person_a", "person_b"):
            try:
                inputs[person_key] = validate_input(
                    body[person_key], allow_unknown_time=True
                )
            except ValueError as exc:
                field, separator, detail = str(exc).partition(":")
                if separator:
                    return _input_error(
                        400, "invalid_input", f"{person_key}.{field}", detail.strip()
                    )
                return _input_error(400, "invalid_input", person_key, str(exc))
    except Exception as exc:
        # A non-ValueError from validation (pathological input types) must not
        # escape the six-token contract as a generic FastAPI 500.
        capture_exception(exc)
        return _message_error(500, ERROR_INTERNAL, MESSAGE_INTERNAL)

    try:
        payload = build_synastry_json(inputs["person_a"], inputs["person_b"])
    except ComputationUnsupportedError:
        # Type mapping, never message matching: an input-deterministic failure
        # (e.g. Placidus undefined at polar latitudes) is 422, not retryable.
        # Time-unknown inputs reach this too — houses are still computed at
        # the estimated local 12:00, so no 200-partial downgrade.
        return _message_error(
            422, ERROR_COMPUTATION_UNSUPPORTED, MESSAGE_COMPUTATION_UNSUPPORTED
        )
    except Exception as exc:
        capture_exception(exc)
        return _message_error(500, ERROR_INTERNAL, MESSAGE_INTERNAL)
    return payload


def _auth_failure(x_engine_key: str | None) -> str | None:
    """Shared X-Engine-Key check. Returns None when authorized, else the token.

    Must compare bytes, and must check None first: ``hmac.compare_digest``
    raises TypeError on None and its str form only accepts ASCII, while
    Starlette decodes header bytes as latin-1 — a missing or undecodable key
    must stay a 401, never become a 500.

    The header is re-encoded as latin-1 to recover the exact wire bytes before
    comparing against the configured key's UTF-8 bytes. Re-encoding as UTF-8
    instead would mangle every non-ASCII byte, so a non-ASCII ENGINE_API_KEY
    would reject even the correct key — a 100% outage that merely looks like a
    broken deploy.

    The key side must use ``surrogateescape``: on POSIX, ``os.environ``
    surrogate-escapes environment values that are not valid UTF-8, so a
    non-UTF-8 ENGINE_API_KEY arrives here containing lone surrogates. Plain
    UTF-8 encoding would raise UnicodeEncodeError outside every handler try —
    a 500 on all requests — while ``surrogateescape`` round-trips the
    original bytes.
    """
    key = os.environ.get("ENGINE_API_KEY")
    if not key:
        # Fail closed: the HTTP server sits behind a public reverse proxy, so a
        # missing key would expose an open compute endpoint. Set ENGINE_ALLOW_OPEN=1
        # to intentionally run keyless (local/dev only).
        if os.environ.get("ENGINE_ALLOW_OPEN") == "1":
            return None
        return "not_configured"
    if x_engine_key is None or not hmac.compare_digest(
        x_engine_key.encode("latin-1", "replace"),
        key.encode("utf-8", "surrogateescape"),
    ):
        return "unauthorized"
    return None


def _require_key(x_engine_key: str | None) -> None:
    """/chart auth — keeps the historical ``{"detail": ...}`` bodies unchanged."""
    failure = _auth_failure(x_engine_key)
    if failure == "not_configured":
        raise HTTPException(status_code=503, detail=MESSAGE_NOT_CONFIGURED)
    if failure == "unauthorized":
        raise HTTPException(status_code=401, detail="unauthorized")


def _input_error(status: int, error: str, field: Any, detail: str) -> JSONResponse:
    # Input-error shape (invalid_json / invalid_input / unauthorized):
    # exactly {ok, error, field, detail}.
    return JSONResponse(
        status_code=status,
        content={"ok": False, "error": error, "field": field, "detail": detail},
    )


def _message_error(status: int, error: str, message: str) -> JSONResponse:
    # Fixed-message shape (computation_unsupported / not_configured /
    # internal_error): exactly {ok, error, message} — no field/detail.
    return JSONResponse(
        status_code=status, content={"ok": False, "error": error, "message": message}
    )


def _engine_input(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="body must be a JSON object")

    # Single validation source shared with the CLI (and MCP): scripts/validation.py.
    # Out-of-range / non-finite / out-of-window rejection is deliberate 400 hardening
    # over the historical float()-coercion behaviour — see AGENTS.md §3/§5.
    try:
        return validate_input(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
