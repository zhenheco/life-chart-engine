#!/usr/bin/env python3
"""Freeze the current pyswisseph-backed engine output as an oracle fixture."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "scripts"
OUT = Path(__file__).with_name("ephemeris_baseline.json")

sys.path.insert(0, str(SCRIPT_DIR))

import chart_engine as engine  # noqa: E402
import swisseph as swe  # noqa: E402

PLANETS = [
    ("太陽", swe.SUN),
    ("月亮", swe.MOON),
    ("水星", swe.MERCURY),
    ("金星", swe.VENUS),
    ("火星", swe.MARS),
    ("木星", swe.JUPITER),
    ("土星", swe.SATURN),
    ("天王星", swe.URANUS),
    ("海王星", swe.NEPTUNE),
    ("冥王星", swe.PLUTO),
    ("北交點", swe.TRUE_NODE),
]

HD_BODIES = {
    "☉": swe.SUN,
    "☾": swe.MOON,
    "☿": swe.MERCURY,
    "♀": swe.VENUS,
    "♂": swe.MARS,
    "♃": swe.JUPITER,
    "♄": swe.SATURN,
    "♅": swe.URANUS,
    "♆": swe.NEPTUNE,
    "♇": swe.PLUTO,
    "☊": swe.TRUE_NODE,
}
HD_ORDER = ["☉", "⊕", "☊", "☋", "☾", "☿", "♀", "♂", "♃", "♄", "♅", "♆", "♇"]
HD_LINE_DEG = 0.9375
HD_GATE_DEG = 5.625

FIXTURES = [
    {
        "id": "taipei_standard",
        "purpose": "mid-latitude ordinary chart; README sample shape",
        "input": {
            "name": "baseline-taipei",
            "gender": "女",
            "date": (1990, 6, 15),
            "time": (8, 30),
            "tz_offset": 8.0,
            "lat": 25.033,
            "lon": 121.5654,
            "target": "2025-01-01",
        },
    },
    {
        "id": "london_solar_sign_cusp",
        "purpose": "different season chart with the Sun on a sign boundary",
        "input": {
            "name": "baseline-cusp",
            "gender": "男",
            "date": (2001, 3, 20),
            "time": (13, 30),
            "tz_offset": 0.0,
            "lat": 51.5074,
            "lon": -0.1278,
            "target": "2025-01-01",
        },
    },
    {
        "id": "high_latitude_65_valid",
        "purpose": "lat 65 Placidus chart that current houses_ex accepts",
        "input": {
            "name": "baseline-lat65",
            "gender": "女",
            "date": (2004, 2, 29),
            "time": (23, 45),
            "tz_offset": 0.0,
            "lat": 65.0,
            "lon": -18.0,
            "target": "2025-01-01",
        },
    },
    {
        "id": "placidus_lat70_invalid",
        "purpose": "lat 70 Placidus chart that current houses_ex rejects",
        "input": {
            "name": "baseline-lat70",
            "gender": "女",
            "date": (2004, 2, 29),
            "time": (23, 45),
            "tz_offset": 0.0,
            "lat": 70.0,
            "lon": -18.0,
            "target": "2025-01-01",
        },
    },
    {
        "id": "jupiter_station_before",
        "purpose": "Jupiter station neighborhood, day before direct station",
        "input": {
            "name": "baseline-jupiter-before",
            "gender": "男",
            "date": (2025, 2, 3),
            "time": (12, 0),
            "tz_offset": 0.0,
            "lat": 0.0,
            "lon": 0.0,
            "target": "2025-02-03",
        },
        "annotations": {"station_check": {"planet": "木星", "position": "before"}},
    },
    {
        "id": "jupiter_station_middle",
        "purpose": "Jupiter station neighborhood, station date",
        "input": {
            "name": "baseline-jupiter-middle",
            "gender": "男",
            "date": (2025, 2, 4),
            "time": (12, 0),
            "tz_offset": 0.0,
            "lat": 0.0,
            "lon": 0.0,
            "target": "2025-02-04",
        },
        "annotations": {"station_check": {"planet": "木星", "position": "middle"}},
    },
    {
        "id": "jupiter_station_after",
        "purpose": "Jupiter station neighborhood, day after direct station",
        "input": {
            "name": "baseline-jupiter-after",
            "gender": "男",
            "date": (2025, 2, 5),
            "time": (12, 0),
            "tz_offset": 0.0,
            "lat": 0.0,
            "lon": 0.0,
            "target": "2025-02-05",
        },
        "annotations": {"station_check": {"planet": "木星", "position": "after"}},
    },
    {
        "id": "saturn_station_before",
        "purpose": "Saturn station neighborhood, day before retrograde station",
        "input": {
            "name": "baseline-saturn-before",
            "gender": "女",
            "date": (2025, 7, 12),
            "time": (12, 0),
            "tz_offset": 0.0,
            "lat": 0.0,
            "lon": 0.0,
            "target": "2025-07-12",
        },
        "annotations": {"station_check": {"planet": "土星", "position": "before"}},
    },
    {
        "id": "saturn_station_middle",
        "purpose": "Saturn station neighborhood, station date",
        "input": {
            "name": "baseline-saturn-middle",
            "gender": "女",
            "date": (2025, 7, 13),
            "time": (12, 0),
            "tz_offset": 0.0,
            "lat": 0.0,
            "lon": 0.0,
            "target": "2025-07-13",
        },
        "annotations": {"station_check": {"planet": "土星", "position": "middle"}},
    },
    {
        "id": "saturn_station_after",
        "purpose": "Saturn station neighborhood, day after retrograde station",
        "input": {
            "name": "baseline-saturn-after",
            "gender": "女",
            "date": (2025, 7, 14),
            "time": (12, 0),
            "tz_offset": 0.0,
            "lat": 0.0,
            "lon": 0.0,
            "target": "2025-07-14",
        },
        "annotations": {"station_check": {"planet": "土星", "position": "after"}},
    },
    {
        "id": "hd_boundary_design_sun",
        "purpose": "Human Design design-Sun line boundary fixture",
        "input": {
            "name": "baseline-hd-design-sun",
            "gender": "女",
            "date": (1983, 11, 11),
            "time": (12, 0),
            "tz_offset": 8.0,
            "lat": 25.033,
            "lon": 121.5654,
            "target": "2025-01-01",
        },
        "annotations": {"human_design_boundary": True},
    },
    {
        "id": "hd_boundary_personality_moon",
        "purpose": "Human Design personality-Moon gate boundary fixture",
        "input": {
            "name": "baseline-hd-personality-moon",
            "gender": "男",
            "date": (1991, 12, 30),
            "time": (0, 0),
            "tz_offset": 8.0,
            "lat": 25.033,
            "lon": 121.5654,
            "target": "2025-01-01",
        },
        "annotations": {"human_design_boundary": True},
    },
]


def r(value: float) -> float:
    return round(float(value), 10)


def public_input(inp: dict) -> dict:
    y, m, d = inp["date"]
    hh, mm = inp["time"]
    return {
        "name": inp["name"],
        "gender": inp["gender"],
        "date": f"{y:04d}-{m:02d}-{d:02d}",
        "time": f"{hh:02d}:{mm:02d}",
        "tz_offset": inp["tz_offset"],
        "lat": inp["lat"],
        "lon": inp["lon"],
        "target": inp["target"],
    }


def ephemeris(inp: dict) -> dict:
    try:
        jd = engine.jd_of(inp["date"], inp["time"], inp["tz_offset"])
        planets = []
        for name, body in PLANETS:
            values = swe.calc_ut(jd, body, engine.FLG)[0]
            planets.append(
                {
                    "name": name,
                    "swe_id": body,
                    "lon": r(values[0]),
                    "speed": r(values[3]),
                    "retrograde": values[3] < 0,
                }
            )
        cusps, ascmc = swe.houses_ex(jd, inp["lat"], inp["lon"], b"P", engine.FLG)
        return {
            "ok": True,
            "julian_day_ut": r(jd),
            "planets": planets,
            "houses": {
                "system": "Placidus",
                "cusps": [r(cusp % 360) for cusp in cusps],
                "ascendant": r(ascmc[0]),
                "midheaven": r(ascmc[1]),
            },
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def build_json(inp: dict) -> dict:
    try:
        return engine.build_json(inp)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "schema_version": "1.1"}


def hd_positions(jd: float) -> dict:
    out = {name: swe.calc_ut(jd, body, engine.FLG)[0][0] for name, body in HD_BODIES.items()}
    out["⊕"] = (out["☉"] + 180) % 360
    out["☋"] = (out["☊"] + 180) % 360
    return out


def design_jd(inp: dict) -> float:
    birth_jd = engine.jd_of(inp["date"], inp["time"], inp["tz_offset"])
    sun_lon = swe.calc_ut(birth_jd, swe.SUN, engine.FLG)[0][0]
    target = (sun_lon - 88) % 360
    lo, hi = birth_jd - 100, birth_jd - 80
    for _ in range(60):
        mid = (lo + hi) / 2
        mid_sun = swe.calc_ut(mid, swe.SUN, engine.FLG)[0][0]
        diff = (mid_sun - target + 180) % 360 - 180
        if diff < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def nearest_hd_boundary(lon: float) -> dict:
    wheel_lon = (lon - engine.OFFSET) % 360
    line_rem = wheel_lon % HD_LINE_DEG
    gate_rem = wheel_lon % HD_GATE_DEG
    line_distance = min(line_rem, HD_LINE_DEG - line_rem)
    gate_distance = min(gate_rem, HD_GATE_DEG - gate_rem)
    return {
        "line_boundary_deg": r(line_distance),
        "gate_boundary_deg": r(gate_distance),
        "nearest_boundary_deg": r(min(line_distance, gate_distance)),
    }


def hd_boundary(inp: dict) -> dict:
    birth_jd = engine.jd_of(inp["date"], inp["time"], inp["tz_offset"])
    candidates = []
    for chart, jd in (("personality", birth_jd), ("design", design_jd(inp))):
        for planet, lon in hd_positions(jd).items():
            gate, line = engine.gate_line(lon)
            boundary = nearest_hd_boundary(lon)
            candidates.append(
                {
                    **boundary,
                    "chart": chart,
                    "planet": planet,
                    "gate": gate,
                    "line": line,
                    "lon": r(lon),
                }
            )
    return min(candidates, key=lambda item: item["nearest_boundary_deg"])


def fixture(spec: dict) -> dict:
    annotations = dict(spec.get("annotations", {}))
    if annotations.get("human_design_boundary") is True:
        annotations["human_design_boundary"] = hd_boundary(spec["input"])
    return {
        "id": spec["id"],
        "purpose": spec["purpose"],
        "input": public_input(spec["input"]),
        "annotations": annotations,
        "ephemeris": ephemeris(spec["input"]),
        "build_json": build_json(spec["input"]),
    }


def baseline() -> dict:
    fixtures = [fixture(spec) for spec in FIXTURES]
    by_id = {item["id"]: item for item in fixtures}
    assert by_id["high_latitude_65_valid"]["build_json"]["ok"] is True
    assert by_id["placidus_lat70_invalid"]["build_json"]["ok"] is False
    assert by_id["placidus_lat70_invalid"]["ephemeris"]["ok"] is False
    assert sum(1 for item in fixtures if item["annotations"].get("human_design_boundary")) >= 2
    return {
        "schema_version": "ephemeris-baseline-1",
        "engine_schema_version": "1.1",
        "generator": "tests/fixtures/gen_ephemeris_baseline.py",
        "python": platform.python_version(),
        "swisseph": {
            "package_version": getattr(swe, "__version__", None),
            "library_version": swe.version,
            "flags": ["FLG_MOSEPH", "FLG_SPEED"],
            "house_system": "Placidus",
        },
        "fixtures": fixtures,
    }


def main() -> None:
    data = baseline()
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
