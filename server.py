import os
from json import JSONDecodeError
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from scripts.chart_engine import build_json
from scripts.validation import validate_input
from sentry_config import capture_exception, init_sentry


init_sentry()

app = FastAPI(title="life-chart-engine")


@app.get("/health")
def health():
    return {"ok": True}


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
            content={"ok": False, "error": str(exc), "schema_version": "1.1"},
        )


def _require_key(x_engine_key: str | None) -> None:
    key = os.environ.get("ENGINE_API_KEY")
    if not key:
        # Fail closed: the HTTP server sits behind a public reverse proxy, so a
        # missing key would expose an open compute endpoint. Set ENGINE_ALLOW_OPEN=1
        # to intentionally run keyless (local/dev only).
        if os.environ.get("ENGINE_ALLOW_OPEN") == "1":
            return
        raise HTTPException(status_code=503, detail="ENGINE_API_KEY not configured")
    if x_engine_key != key:
        raise HTTPException(status_code=401, detail="unauthorized")


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
