import math
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validation import validate_input  # noqa: E402


RAW = {
    "date": "1990-06-15",
    "time": "08:30",
    "tz": 8,
    "lat": 25.0,
    "lon": 121.5,
    "gender": "女",
}


def test_normalizes_unpadded_values_and_applies_defaults():
    out = validate_input({**RAW, "date": "1990-6-15", "time": "8:5"})

    assert out["date"] == (1990, 6, 15)
    assert out["time"] == (8, 5)
    assert out["tz_offset"] == 8.0
    assert out["name"] == "範例"
    assert out["target"] == "2025-01-01"


def test_omits_ziwei_day_divide_unless_provided():
    assert "ziwei_day_divide" not in validate_input(dict(RAW))
    assert validate_input({**RAW, "ziwei_day_divide": "current"})["ziwei_day_divide"] == "current"


@pytest.mark.parametrize(
    ("field", "value"),
    [("tz", -12), ("tz", 14), ("lat", -90), ("lat", 90), ("lon", -180), ("lon", 180)],
)
def test_accepts_numeric_boundaries(field, value):
    out = validate_input({**RAW, field: value})
    key = "tz_offset" if field == "tz" else field
    assert out[key] == float(value)


@pytest.mark.parametrize("date_value", ["1900-01-01", "2100-12-31", "1900-1-1"])
def test_accepts_year_window_endpoints_for_birth_and_target(date_value):
    assert validate_input({**RAW, "date": date_value})["date"][0] in (1900, 2100)
    normalized_target = validate_input({**RAW, "target": date_value})["target"]
    assert normalized_target.startswith(("1900-", "2100-"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tz", -12.5),
        ("tz", 14.5),
        ("tz", float("nan")),
        ("tz", float("inf")),
        ("tz", "1e999"),
        ("lat", 90.5),
        ("lat", -90.5),
        ("lon", 181),
        ("lon", -181),
        ("date", "1899-12-31"),
        ("date", "2101-01-01"),
        ("date", "1990-13-45"),
        ("date", "1991-02-29"),
        ("date", "1_990-06-15"),
        ("time", "25:99"),
        ("time", "8: 5"),
        ("target", "1899-12-31"),
        ("target", "2101-01-01"),
        ("gender", "X"),
        ("ziwei_day_divide", "sideways"),
    ],
)
def test_rejects_out_of_contract_values_naming_the_field(field, value):
    with pytest.raises(ValueError) as excinfo:
        validate_input({**RAW, field: value})
    assert field in str(excinfo.value)


@pytest.mark.parametrize("field", ["date", "time", "tz", "lat", "lon", "gender"])
def test_rejects_missing_required_field_naming_it(field):
    raw = {k: v for k, v in RAW.items() if k != field}
    with pytest.raises(ValueError) as excinfo:
        validate_input(raw)
    assert field in str(excinfo.value)


def test_rejected_values_never_return_nonfinite_floats():
    # guard against float("1e999") == inf sneaking through as a "number"
    for bad in ("1e999", "-1e999"):
        with pytest.raises(ValueError):
            validate_input({**RAW, "lat": bad})
    good = validate_input(dict(RAW))
    for key in ("tz_offset", "lat", "lon"):
        assert math.isfinite(good[key])
