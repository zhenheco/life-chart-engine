import os
from datetime import date as valid_date
from datetime import time as valid_time
from json import JSONDecodeError
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from scripts.chart_engine import INPUT, build_json


app = FastAPI(title="life-chart-engine")

REQUIRED_FIELDS = ("date", "time", "tz", "lat", "lon", "gender")


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
    except Exception as exc:  # build_json / Swiss Ephemeris edge input
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

    missing = [field for field in REQUIRED_FIELDS if field not in body]
    if missing:
        raise HTTPException(status_code=400, detail=f"missing required fields: {', '.join(missing)}")

    gender = body["gender"]
    if gender not in {"男", "女"}:
        raise HTTPException(status_code=400, detail="gender must be 男 or 女")

    try:
        target = str(body.get("target", INPUT["target"]))
        _parse_date(target, "target")
        return {
            "name": str(body.get("name", INPUT["name"])),
            "gender": gender,
            "date": _parse_date(body["date"], "date"),
            "time": _parse_time(body["time"]),
            "tz_offset": float(body["tz"]),
            "lat": float(body["lat"]),
            "lon": float(body["lon"]),
            "target": target,
        }
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _parse_date(value: Any, field: str) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be YYYY-MM-DD")
    parts = value.split("-")
    if len(parts) != 3:
        raise ValueError(f"{field} must be YYYY-MM-DD")
    try:
        y, m, d = map(int, parts)
    except ValueError as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD") from exc
    valid_date(y, m, d)
    return y, m, d


def _parse_time(value: Any) -> tuple[int, int]:
    if not isinstance(value, str):
        raise ValueError("time must be HH:MM")
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("time must be HH:MM")
    try:
        h, m = map(int, parts)
    except ValueError as exc:
        raise ValueError("time must be HH:MM") from exc
    valid_time(h, m)
    return h, m
