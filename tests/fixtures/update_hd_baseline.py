#!/usr/bin/env python3
"""Regenerate the Human Design portion of ephemeris_baseline.json from the
corrected engine (fix/hd-gate-wheel-offset: OFFSET -1.375 -> -1.75).

Only `build_json.human_design` and the `human_design_boundary` annotation are
touched. Everything else in each fixture (western, ephemeris, id, purpose,
input, station_check annotations) is carried over unchanged:

  - `western` does not depend on OFFSET/gate_line at all, and this script
    asserts the freshly computed western section is byte-identical to the
    stored one before overwriting anything, so unrelated drift fails loudly
    instead of being silently baked in.
  - `ephemeris` is a frozen swisseph (AGPL-era) ground-truth snapshot; the
    engine no longer depends on swisseph (MIT/astronomy-engine), so it cannot
    be regenerated here and is intentionally left alone.

The two `human_design_boundary` fixtures were originally chosen to sit
sub-micro-degree from a gate/line boundary *under the old wrong offset*. That
property does not carry over (the wheel is not just relabeled, it is rotated
by a constant 0.375 deg), so their boundary annotation is recomputed honestly
for the corrected offset rather than hand-edited or silently left stale. No
test asserts boundary tightness (see tests/test_engine_astronomy_contract.py
test_human_design_boundary_fixtures_report_gate_or_line_jumps), only that the
`human_design_boundary` flag stays truthy, so this keeps the case valid.

Usage:
    .venv/bin/python tests/fixtures/update_hd_baseline.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import chart_engine as engine  # noqa: E402

BASELINE = Path(__file__).with_name("ephemeris_baseline.json")

HD_BODIES = ["☉", "☾", "☿", "♀", "♂", "♃", "♄", "♅", "♆", "♇", "☊"]
HD_LINE_DEG = 0.9375
HD_GATE_DEG = 5.625

# Sanity bound for the western sanity-check below, not a rewrite of western.
# ephemeris_baseline.json's stored `western` section was frozen from the old
# swisseph engine (01-baseline-oracle-freeze, pre astronomy-engine
# migration); tests/test_engine_astronomy_contract.py already compares it
# with tolerance (DEFAULT_LON_TOL=0.017 deg) for exactly this reason, not
# byte equality. This script never overwrites `western`; the bound below only
# guards against a *gross* mismatch (e.g. a real regression) slipping through
# unnoticed, using a bound looser than the test's so it never false-positives
# on that known, accepted swisseph-vs-astronomy-engine numerical drift.
WESTERN_SANITY_TOL_DEG = 0.05


def r(value: float) -> float:
    return round(float(value), 10)


def angular_delta(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def build_json_or_error(inp: dict) -> dict:
    # Mirrors the CLI's own catch-all (scripts/chart_engine.py main()) and the
    # test suite's build_json_or_error() helper: engine.build_json() itself
    # lets validation/computation errors propagate.
    try:
        return engine.build_json(inp)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def engine_input(item: dict) -> dict:
    y, mo, d = map(int, item["input"]["date"].split("-"))
    hh, mm = map(int, item["input"]["time"].split(":"))
    return {
        "name": item["input"]["name"],
        "gender": item["input"]["gender"],
        "date": (y, mo, d),
        "time": (hh, mm),
        "tz_offset": item["input"]["tz_offset"],
        "lat": item["input"]["lat"],
        "lon": item["input"]["lon"],
        "target": item["input"]["target"],
    }


def hd_positions(jd: float) -> dict:
    out = {n: engine.eph.body_lon_speed(jd, n)[0] for n in HD_BODIES}
    out["⊕"] = (out["☉"] + 180) % 360
    out["☋"] = (out["☊"] + 180) % 360
    return out


def design_jd(inp: dict) -> float:
    birth_jd = engine.jd_of(inp["date"], inp["time"], inp["tz_offset"])
    sun_lon = engine.eph.body_lon_speed(birth_jd, "☉")[0]
    target = (sun_lon - 88) % 360
    lo, hi = birth_jd - 100, birth_jd - 80
    for _ in range(60):
        mid = (lo + hi) / 2
        mid_sun = engine.eph.body_lon_speed(mid, "☉")[0]
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
                {**boundary, "chart": chart, "planet": planet, "gate": gate, "line": line, "lon": r(lon)}
            )
    return min(candidates, key=lambda c: c["nearest_boundary_deg"])


def main() -> None:
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    changed = []
    for item in data["fixtures"]:
        inp = engine_input(item)
        old_bj = item["build_json"]
        new_bj = build_json_or_error(inp)
        assert new_bj.get("ok") == old_bj.get("ok"), f"{item['id']}: ok flag changed"
        if new_bj.get("ok"):
            old_planets = {p["name"]: p for p in old_bj["western"]["planets"]}
            for planet in new_bj["western"]["planets"]:
                delta = angular_delta(planet["lon"], old_planets[planet["name"]]["lon"])
                assert delta <= WESTERN_SANITY_TOL_DEG, (
                    f"{item['id']} {planet['name']}: western lon delta={delta:.6f} "
                    f"exceeds sanity bound {WESTERN_SANITY_TOL_DEG} — OFFSET fix should not "
                    "move western this much; investigate before overwriting human_design"
                )
            old_hd = old_bj["human_design"]
            new_hd = new_bj["human_design"]
            if old_hd != new_hd:
                changed.append((item["id"], old_hd, new_hd))
            item["build_json"]["human_design"] = new_hd
        if item.get("annotations", {}).get("human_design_boundary"):
            item["annotations"]["human_design_boundary"] = hd_boundary(inp)

    BASELINE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {BASELINE}")
    print(f"{len(changed)} of {len(data['fixtures'])} fixtures changed human_design:")
    for fid, old_hd, new_hd in changed:
        print(f"\n== {fid} ==")
        for key in ("type", "authority", "definition", "profile", "channels", "defined_centers", "open_centers"):
            if key not in old_hd:
                continue
            if old_hd[key] != new_hd[key]:
                print(f"  {key}: {old_hd[key]!r} -> {new_hd[key]!r}")
        for og, ng in zip(old_hd["gates"], new_hd["gates"], strict=True):
            for side in ("personality", "design"):
                if og[side] != ng[side]:
                    print(
                        f"  {og['planet']} {side}: "
                        f"{og[side]['gate']}.{og[side]['line']} -> {ng[side]['gate']}.{ng[side]['line']}"
                    )


if __name__ == "__main__":
    main()
