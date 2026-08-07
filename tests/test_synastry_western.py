"""E2 — western cross-chart aspects[] behaviour tests."""

from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import semantics  # noqa: E402
import synastry  # noqa: E402
from validation import validate_input  # noqa: E402


FORBIDDEN_KEY_SUBSTR = {
    "interpretive_valence",
    "score",
    "compatibility",
    "percentage",
    "rating",
    "total",
    "grade",
    "吉凶",
}


def _sample_pair(i=0):
    """Five distinct birth pairs for sample coverage."""
    pairs = [
        (
            {
                "name": "A0",
                "gender": "女",
                "date": "1990-06-15",
                "time": "08:30",
                "tz": 8,
                "lat": 25.033,
                "lon": 121.5654,
            },
            {
                "name": "B0",
                "gender": "男",
                "date": "1988-03-20",
                "time": "14:00",
                "tz": 8,
                "lat": 25.0,
                "lon": 121.5,
            },
        ),
        (
            {
                "name": "A1",
                "gender": "男",
                "date": "1985-12-01",
                "time": "03:15",
                "tz": 8,
                "lat": 24.15,
                "lon": 120.67,
            },
            {
                "name": "B1",
                "gender": "女",
                "date": "1992-07-22",
                "time": "19:45",
                "tz": 8,
                "lat": 22.63,
                "lon": 120.30,
            },
        ),
        (
            {
                "name": "A2",
                "gender": "女",
                "date": "1978-01-10",
                "time": "11:00",
                "tz": -5,
                "lat": 40.71,
                "lon": -74.01,
            },
            {
                "name": "B2",
                "gender": "男",
                "date": "1980-09-05",
                "time": "06:30",
                "tz": -5,
                "lat": 34.05,
                "lon": -118.24,
            },
        ),
        (
            {
                "name": "A3",
                "gender": "男",
                "date": "2000-01-01",
                "time": "12:00",
                "tz": 8,
                "lat": 25.033,
                "lon": 121.5654,
            },
            {
                "name": "B3",
                "gender": "女",
                "date": "1995-05-15",
                "time": "09:00",
                "tz": 9,
                "lat": 35.68,
                "lon": 139.69,
            },
        ),
        (
            {
                "name": "A4",
                "gender": "女",
                "date": "1969-07-20",
                "time": "20:17",
                "tz": -6,
                "lat": 29.76,
                "lon": -95.37,
            },
            {
                "name": "B4",
                "gender": "男",
                "date": "1971-11-11",
                "time": "01:00",
                "tz": 1,
                "lat": 48.86,
                "lon": 2.35,
            },
        ),
    ]
    a_raw, b_raw = pairs[i]
    return validate_input(a_raw), validate_input(b_raw)


def _all_keys(obj, found=None):
    if found is None:
        found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.append(k)
            _all_keys(v, found)
    elif isinstance(obj, list):
        for item in obj:
            _all_keys(item, found)
    return found


def _pos_map(**kwargs):
    """Longitude map for all 11 bodies.

    Defaults place each body 30° apart from the previous. When the *same*
    default map is used for both A and B, every same-named body pair is an
    exact conjunction (orb 0). Override longitudes when a controlled pair is
    needed; spread-only defaults do **not** mean "no aspects".
    """
    base = {
        "太陽": 0.0,
        "月亮": 30.0,
        "水星": 60.0,
        "金星": 100.0,
        "火星": 140.0,
        "木星": 170.0,
        "土星": 200.0,
        "天王星": 230.0,
        "海王星": 260.0,
        "冥王星": 290.0,
        "北交點": 320.0,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Pairing / membership
# ---------------------------------------------------------------------------


def test_aspects_from_controlled_positions_validate_and_exclude_south_node():
    # A 水星–B 土星 square orb 0.7
    pos_a = _pos_map(水星=0.0)
    pos_b = _pos_map(土星=89.3)
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    assert aspects, "expected at least one aspect"
    for ev in aspects:
        semantics.validate_evidence(ev)
    blob = json.dumps(aspects, ensure_ascii=False)
    assert "南交點" not in blob
    assert "South Node" not in blob
    assert "south-node" not in blob


def test_aspects_exclude_angle_points():
    # All four angle raw_fact names from the slug table (Ascendant, Descendant,
    # Midheaven, Imum Coeli) — not only the two previously checked.
    angle_raw_names = {
        semantics.SLUGS["internal_to_raw"][body] for body in semantics.ANGLE_BODIES
    }
    assert angle_raw_names == {
        "Ascendant",
        "Descendant",
        "Midheaven",
        "Imum Coeli",
    }
    pos_a = _pos_map(太陽=0.0)
    pos_b = _pos_map(月亮=90.0)
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    assert aspects
    for ev in aspects:
        rf = ev["raw_fact"]
        for key in ("planet_a", "planet_b"):
            assert rf[key] not in angle_raw_names
        fid = ev["feature_id"]
        for token in ("-asc-", "-desc-", "-mc-", "-ic-"):
            assert token not in fid


def test_no_chiron_in_body_set_or_output():
    assert "凱龍" not in synastry.ASPECT_BODIES
    assert "Chiron" not in synastry.ASPECT_BODIES
    assert all("chiron" not in str(b).lower() for b in synastry.ASPECT_BODIES)
    pos_a = _pos_map()
    pos_b = _pos_map(太陽=0.1)  # near conjunction with A's sun default 0
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    assert aspects
    text = json.dumps(aspects, ensure_ascii=False).lower()
    assert "chiron" not in text
    assert "凱龍" not in text


def test_both_outer_planets_suppressed():
    # Uranus–Neptune only near-aspect; no non-outer partners aligned
    pos_a = _pos_map(天王星=0.0, 太陽=50.0, 月亮=80.0, 水星=110.0)
    pos_b = _pos_map(海王星=0.5, 太陽=150.0, 月亮=180.0, 水星=210.0)
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    for ev in aspects:
        pair = {ev["raw_fact"]["planet_a"], ev["raw_fact"]["planet_b"]}
        outers = {"Uranus", "Neptune", "Pluto"}
        assert not pair <= outers, f"outer-outer aspect leaked: {ev['feature_id']}"


def test_jupiter_participates():
    pos_a = _pos_map(木星=0.0)
    pos_b = _pos_map(太陽=0.2)
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    fids = [e["feature_id"] for e in aspects]
    assert any("jupiter" in f for f in fids)


def test_saturn_participates():
    pos_a = _pos_map(土星=0.0)
    pos_b = _pos_map(月亮=0.2)
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    fids = [e["feature_id"] for e in aspects]
    assert any("saturn" in f for f in fids)


# ---------------------------------------------------------------------------
# orb inclusion boundaries
# ---------------------------------------------------------------------------


def test_orb_exactly_at_max_included_with_zero_salience():
    # mercury–saturn square max_orb=5; place at exact boundary
    pos_a = _pos_map(水星=0.0)
    pos_b = _pos_map(土星=95.0)  # actual 95, exact 90, orb 5.0
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    hit = [
        e
        for e in aspects
        if e["feature_id"] == "w-syn-a-mercury-square-b-saturn"
    ]
    assert len(hit) == 1
    assert hit[0]["raw_fact"]["orb"] == 5.0
    assert semantics.orb_weight(5.0, 5.0) == 0.0
    assert hit[0]["salience"] == 0.0


def test_orb_slightly_over_max_excluded():
    pos_a = _pos_map(水星=0.0)
    pos_b = _pos_map(土星=95.01)  # orb 5.01 > 5
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    fids = [e["feature_id"] for e in aspects]
    assert "w-syn-a-mercury-square-b-saturn" not in fids


def test_sun_square_north_node_inside_two_degrees_included():
    pos_a = _pos_map(太陽=0.0)
    pos_b = _pos_map(北交點=91.5)  # orb 1.5 ≤ 2
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    hit = [e for e in aspects if e["feature_id"] == "w-syn-a-sun-square-b-north-node"]
    assert len(hit) == 1
    assert hit[0]["raw_fact"]["orb"] == 1.5


def test_sun_square_north_node_outside_two_degrees_excluded():
    pos_a = _pos_map(太陽=0.0)
    pos_b = _pos_map(北交點=93.0)  # orb 3 > 2 (would be inside 6 if wrongly using sun+square)
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    fids = [e["feature_id"] for e in aspects]
    assert "w-syn-a-sun-square-b-north-node" not in fids


def test_wraparound_conjunction_orb_is_one_not_359():
    pos_a = _pos_map(太陽=359.5)
    pos_b = _pos_map(月亮=0.5)
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    hit = [e for e in aspects if e["feature_id"] == "w-syn-a-sun-conjunction-b-moon"]
    assert len(hit) == 1
    assert abs(hit[0]["raw_fact"]["orb"] - 1.0) < 1e-9
    assert hit[0]["raw_fact"]["orb"] != 359
    assert abs(hit[0]["raw_fact"]["actual_angle"] - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# sorting / uniqueness / forbidden keys / raw precision
# ---------------------------------------------------------------------------


def test_aspects_sorted_salience_desc_feature_id_asc_tiebreak():
    """Equal salience → feature_id ascending as tie-break."""
    from itertools import groupby

    # 水星-木星 and 金星-土星 at orb 0: both planet_weight max(0.9, 0.8)=0.9
    pos_a = _pos_map(水星=0.0, 金星=10.0)
    pos_b = _pos_map(木星=0.0, 土星=10.0)
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    targets = [
        e
        for e in aspects
        if e["feature_id"]
        in (
            "w-syn-a-mercury-conjunction-b-jupiter",
            "w-syn-a-venus-conjunction-b-saturn",
        )
    ]
    assert len(targets) == 2
    assert targets[0]["salience"] == targets[1]["salience"]
    saliences = [e["salience"] for e in aspects]
    assert saliences == sorted(saliences, reverse=True)
    for _sal, group in groupby(aspects, key=lambda e: e["salience"]):
        fids = [e["feature_id"] for e in group]
        assert fids == sorted(fids)


def _collect_feature_ids(obj, found=None):
    """Recursively collect every ``feature_id`` value in a payload tree."""
    if found is None:
        found = []
    if isinstance(obj, dict):
        if "feature_id" in obj:
            found.append(obj["feature_id"])
        for v in obj.values():
            _collect_feature_ids(v, found)
    elif isinstance(obj, list):
        for item in obj:
            _collect_feature_ids(item, found)
    return found


def test_feature_ids_globally_unique_in_full_response():
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    fids = _collect_feature_ids(payload)
    assert fids, "expected at least one feature_id in the full response"
    assert len(fids) == len(set(fids))


def test_forbidden_keys_absent_recursively():
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    keys = _all_keys(payload)
    for k in keys:
        kl = k.lower() if isinstance(k, str) else k
        for bad in FORBIDDEN_KEY_SUBSTR:
            assert bad.lower() not in kl if bad != "吉凶" else bad not in str(k)


def _has_more_than_three_decimals(value: float) -> bool:
    """True if value is not pre-rounded to 3 decimal places."""
    if abs(value - round(value, 3)) > 1e-12:
        return True
    s = repr(float(value))
    if "." in s:
        frac = s.split(".")[-1].rstrip("0")
        if len(frac) > 3:
            return True
    return False


def test_raw_orb_not_rounded_has_more_than_three_decimals():
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    aspects = payload["synastry"]["western"]["aspects"]
    assert aspects
    # at least one orb whose float residual/repr shows >3 decimal places
    found_orb = any(
        _has_more_than_three_decimals(ev["raw_fact"]["orb"]) for ev in aspects
    )
    assert found_orb, "expected at least one unrounded orb with >3 decimal places of precision"
    # same for actual_angle — rounding either field would silently drop precision
    found_angle = any(
        _has_more_than_three_decimals(ev["raw_fact"]["actual_angle"]) for ev in aspects
    )
    assert found_angle, (
        "expected at least one unrounded actual_angle with >3 decimal places of precision"
    )


# ---------------------------------------------------------------------------
# 5 sample charts — dimensions ⊂ themes-v1 and rule-ordered
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sample_i", range(5))
def test_sample_chart_dimensions_subset_and_ordered(sample_i):
    inp_a, inp_b = _sample_pair(sample_i)
    block = synastry.build_synastry(inp_a, inp_b)
    aspects = block["western"]["aspects"]
    themes = set(semantics.THEMES_V1)
    assert aspects, f"sample {sample_i} produced no aspects"
    for ev in aspects:
        semantics.validate_evidence(ev)
        dims = ev["dimensions"]
        assert set(dims) <= themes
        # reconstruct expected from raw_fact planets
        pa = semantics.raw_fact_to_internal(ev["raw_fact"]["planet_a"])
        pb = semantics.raw_fact_to_internal(ev["raw_fact"]["planet_b"])
        assert dims == semantics.dimensions_for_aspect(pa, pb)


# ---------------------------------------------------------------------------
# local 12:00 vs explicit --time 12:00 for non-zero tz unknown side
# ---------------------------------------------------------------------------


def test_unknown_time_uses_local_noon_not_utc():
    """Unknown-time side must equal the same person with explicit local 12:00."""
    a_known = validate_input(
        {
            "name": "A",
            "gender": "女",
            "date": "1990-06-15",
            "time": "08:30",
            "tz": 8,
            "lat": 25.033,
            "lon": 121.5654,
        }
    )
    b_unknown = validate_input(
        {
            "name": "B",
            "gender": "男",
            "date": "1988-03-20",
            "time": "unknown",
            "tz": 8,
            "lat": 25.0,
            "lon": 121.5,
        },
        allow_unknown_time=True,
    )
    b_noon = validate_input(
        {
            "name": "B",
            "gender": "男",
            "date": "1988-03-20",
            "time": "12:00",
            "tz": 8,
            "lat": 25.0,
            "lon": 121.5,
        }
    )
    assert b_unknown.get("time_unknown") is True
    assert b_unknown["time"] == (12, 0)
    assert b_unknown["tz_offset"] == 8.0

    out_unknown = synastry.build_synastry_json(a_known, b_unknown)
    out_noon = synastry.build_synastry_json(a_known, b_noon)

    asp_u = out_unknown["synastry"]["western"]["aspects"]
    asp_n = out_noon["synastry"]["western"]["aspects"]
    assert len(asp_u) == len(asp_n)
    # Same feature set and raw geometry (data_confidence may differ by time_unknown)
    by_u = {e["feature_id"]: e for e in asp_u}
    by_n = {e["feature_id"]: e for e in asp_n}
    assert set(by_u) == set(by_n)
    for fid in by_u:
        assert by_u[fid]["raw_fact"] == by_n[fid]["raw_fact"]
        assert by_u[fid]["salience"] == by_n[fid]["salience"]
        assert by_u[fid]["dimensions"] == by_n[fid]["dimensions"]
    # data_confidence: known-time group is always 0.95; unknown-time group is
    # only 0.6 (unknown-side Moon) or 0.85 (other unknown-side participation).
    assert asp_n and asp_u
    assert all(e["data_confidence"] == 0.95 for e in asp_n)
    assert all(e["data_confidence"] in {0.6, 0.85} for e in asp_u)
    assert 0.95 not in {e["data_confidence"] for e in asp_u}


# ---------------------------------------------------------------------------
# no-network socket guard
# ---------------------------------------------------------------------------


def test_build_synastry_json_works_with_socket_guard():
    """Mirror the spirit of test_sidecar_no_network: no network needed at runtime."""
    real_socket = socket.socket

    class GuardedSocket(socket.socket):
        def __init__(self, *a, **kw):
            raise RuntimeError("network forbidden during synastry compute")

        def connect(self, *a, **kw):  # pragma: no cover
            raise RuntimeError("network forbidden")

    socket.socket = GuardedSocket
    try:
        inp_a, inp_b = _sample_pair(0)
        payload = synastry.build_synastry_json(inp_a, inp_b)
        assert payload["ok"] is True
        assert "synastry" in payload
        assert isinstance(payload["synastry"]["western"]["aspects"], list)
    finally:
        socket.socket = real_socket


# ---------------------------------------------------------------------------
# full response: aspects non-empty when both times known; each validates
# ---------------------------------------------------------------------------


def test_build_synastry_fills_aspects_and_completeness():
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    aspects = payload["synastry"]["western"]["aspects"]
    assert aspects
    for ev in aspects:
        semantics.validate_evidence(ev)
    assert payload["synastry"]["unavailable"] == []
    assert payload["evidence_completeness"] == "full"


def test_minor_aspects_and_asteroids_not_emitted():
    pos_a = _pos_map(太陽=0.0)
    pos_b = _pos_map(月亮=45.0)  # semi-square territory — must not invent minor aspects
    aspects = synastry.compute_western_aspects(
        pos_a, pos_b, time_unknown_a=False, time_unknown_b=False
    )
    assert aspects
    for ev in aspects:
        assert ev["raw_fact"]["aspect"] in {
            "conjunction",
            "sextile",
            "square",
            "trine",
            "opposition",
        }
