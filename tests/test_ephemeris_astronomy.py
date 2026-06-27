import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ephemeris_astronomy as eph  # noqa: E402


BASELINE = ROOT / "tests" / "fixtures" / "ephemeris_baseline.json"
DEFAULT_LON_TOL = 0.017
LON_TOL = {"月亮": 0.05, "北交點": 0.05}
SPEED_TOL = 0.005
HOUSE_FIXTURE_TOLS = {
    "taipei_standard": 0.05,
    "london_solar_sign_cusp": 0.05,
    "high_latitude_65_valid": 0.2,
}


def angular_delta(a, b):
    return abs((a - b + 180) % 360 - 180)


def baseline_fixtures():
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    return [item for item in data["fixtures"] if item["ephemeris"]["ok"]]


def all_baseline_fixtures():
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    return data["fixtures"]


def local_ut_hour(item):
    hh, mm = map(int, item["input"]["time"].split(":"))
    return hh + mm / 60 - item["input"]["tz_offset"]


def test_astronomy_julday_matches_baseline():
    for item in baseline_fixtures():
        y, mo, d = map(int, item["input"]["date"].split("-"))
        got = eph.julday(y, mo, d, local_ut_hour(item))
        expected = item["ephemeris"]["julian_day_ut"]
        assert abs(got - expected) <= 1e-9, f"{item['id']} jd delta={got - expected!r}"


def test_astronomy_planet_longitudes_match_baseline():
    for item in baseline_fixtures():
        jd = item["ephemeris"]["julian_day_ut"]
        for planet in item["ephemeris"]["planets"]:
            got_lon, _ = eph.body_lon_speed(jd, planet["name"])
            delta = angular_delta(got_lon, planet["lon"])
            tol = LON_TOL.get(planet["name"], DEFAULT_LON_TOL)
            assert delta <= tol, (
                f"{item['id']} {planet['name']} lon delta={delta:.8f} "
                f"got={got_lon:.10f} expected={planet['lon']:.10f} tol={tol}"
            )


def test_astronomy_planet_speeds_match_baseline():
    for item in baseline_fixtures():
        jd = item["ephemeris"]["julian_day_ut"]
        for planet in item["ephemeris"]["planets"]:
            _, got_speed = eph.body_lon_speed(jd, planet["name"])
            delta = abs(got_speed - planet["speed"])
            assert delta <= SPEED_TOL, (
                f"{item['id']} {planet['name']} speed delta={delta:.8f} "
                f"got={got_speed:.10f} expected={planet['speed']:.10f} tol={SPEED_TOL}"
            )


def test_astronomy_retrograde_matches_station_and_nodes():
    for item in baseline_fixtures():
        jd = item["ephemeris"]["julian_day_ut"]
        station = item.get("annotations", {}).get("station_check")
        required = {"北交點"}
        if station:
            required.add(station["planet"])
        for planet in item["ephemeris"]["planets"]:
            if planet["name"] not in required:
                continue
            _, speed = eph.body_lon_speed(jd, planet["name"])
            got = speed < 0
            assert got is planet["retrograde"], (
                f"{item['id']} {planet['name']} retro got={got} "
                f"expected={planet['retrograde']} speed={speed:.10f}"
            )


def test_astronomy_hd_symbol_aliases_match_chinese_body_names():
    jd = baseline_fixtures()[0]["ephemeris"]["julian_day_ut"]
    aliases = {
        "☉": "太陽",
        "☾": "月亮",
        "☿": "水星",
        "♀": "金星",
        "♂": "火星",
        "♃": "木星",
        "♄": "土星",
        "♅": "天王星",
        "♆": "海王星",
        "♇": "冥王星",
        "☊": "北交點",
    }
    for symbol, name in aliases.items():
        symbol_lon, symbol_speed = eph.body_lon_speed(jd, symbol)
        name_lon, name_speed = eph.body_lon_speed(jd, name)
        assert angular_delta(symbol_lon, name_lon) == 0
        assert symbol_speed == name_speed


def test_astronomy_placidus_houses_match_baseline():
    max_deltas = {}
    for item in all_baseline_fixtures():
        if item["id"] not in HOUSE_FIXTURE_TOLS:
            continue
        jd = item["ephemeris"]["julian_day_ut"]
        inp = item["input"]
        expected = item["ephemeris"]["houses"]
        cusps, asc, mc = eph.houses_asc_mc(jd, inp["lat"], inp["lon"])
        deltas = [
            angular_delta(got, want)
            for got, want in zip(cusps, expected["cusps"], strict=True)
        ]
        deltas.extend(
            [
                angular_delta(asc, expected["ascendant"]),
                angular_delta(mc, expected["midheaven"]),
            ]
        )
        max_delta = max(deltas)
        max_deltas[item["id"]] = max_delta
        print(
            item["id"],
            "house deltas",
            " ".join(f"{i + 1}:{d:.6f}" for i, d in enumerate(deltas[:12])),
            f"asc:{deltas[12]:.6f}",
            f"mc:{deltas[13]:.6f}",
            f"max:{max_delta:.6f}",
        )
        assert len(cusps) == 12
        assert asc == cusps[0]
        assert mc == cusps[9]
        assert max_delta <= HOUSE_FIXTURE_TOLS[item["id"]]
    print("houses max deltas", max_deltas)


def test_astronomy_placidus_houses_raise_at_invalid_high_latitude():
    item = next(i for i in all_baseline_fixtures() if i["id"] == "placidus_lat70_invalid")
    y, mo, d = map(int, item["input"]["date"].split("-"))
    jd = eph.julday(y, mo, d, local_ut_hour(item))
    try:
        eph.houses_asc_mc(jd, item["input"]["lat"], item["input"]["lon"])
    except ValueError as exc:
        assert "placidus undefined" in str(exc)
    else:
        raise AssertionError("expected Placidus high-latitude failure")
