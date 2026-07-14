from datetime import date as calendar_date
import math
import re


DEFAULT_NAME = "範例"
DEFAULT_TARGET = "2025-01-01"
MIN_YEAR = 1900
MAX_YEAR = 2100


def _date_value(field, value):
    try:
        if not re.fullmatch(r"\d{1,4}-\d{1,2}-\d{1,2}", str(value)):
            raise ValueError
        parts = tuple(int(part) for part in str(value).split("-"))
        parsed = calendar_date(*parts)
    except (TypeError, ValueError):
        raise ValueError(f"{field}: must be a real calendar date in YYYY-M-D form") from None
    if not MIN_YEAR <= parsed.year <= MAX_YEAR:
        raise ValueError(f"{field}: year must be between {MIN_YEAR} and {MAX_YEAR}")
    return parsed


def _time_value(value):
    try:
        if not re.fullmatch(r"\d{1,2}:\d{1,2}", str(value)):
            raise ValueError
        hour, minute = (int(part) for part in str(value).split(":"))
    except (TypeError, ValueError):
        raise ValueError("time: must be in H:M form") from None
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("time: hour must be 0-23 and minute must be 0-59")
    return hour, minute


def _finite_float(field, value, minimum, maximum):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field}: must be a number") from None
    if not math.isfinite(parsed):
        raise ValueError(f"{field}: must be finite")
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{field}: must be between {minimum:g} and {maximum:g}")
    return parsed


def validate_input(raw):
    """Validate raw interface values and return the engine's normalized input."""
    for field in ("date", "time", "tz", "lat", "lon", "gender"):
        if raw.get(field) is None:
            raise ValueError(f"{field}: is required")

    gender = raw["gender"]
    if not isinstance(gender, str) or gender not in {"男", "女"}:
        raise ValueError("gender: must be 男 or 女")

    birth_date = _date_value("date", raw["date"])
    target = _date_value("target", raw.get("target", DEFAULT_TARGET))
    normalized = {
        "name": DEFAULT_NAME if raw.get("name") is None else str(raw["name"]),
        "gender": gender,
        "date": (birth_date.year, birth_date.month, birth_date.day),
        "time": _time_value(raw["time"]),
        "tz_offset": _finite_float("tz", raw["tz"], -12, 14),
        "lat": _finite_float("lat", raw["lat"], -90, 90),
        "lon": _finite_float("lon", raw["lon"], -180, 180),
        "target": target.isoformat(),
    }
    if "ziwei_day_divide" in raw:
        day_divide = raw["ziwei_day_divide"]
        if not isinstance(day_divide, str) or day_divide not in {"forward", "current"}:
            raise ValueError("ziwei_day_divide: must be forward or current")
        normalized["ziwei_day_divide"] = day_divide
    return normalized
