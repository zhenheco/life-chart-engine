"""E3 — western house overlay + angle contacts behaviour tests."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import semantics  # noqa: E402
import synastry  # noqa: E402
from chart_engine import western  # noqa: E402
from validation import validate_input  # noqa: E402

# Exact 11-body English raw_fact set for overlay / angle-contact planet slots.
EXPECTED_OVERLAY_PLANETS = {
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "North Node",
}

FEATURE_ID_RE = re.compile(r"^[a-z]+-[a-z0-9-]+$")
OVERLAY_FID_RE = re.compile(
    r"^w-ovl-(?P<sub>a|b)-(?P<planet>[a-z0-9-]+)-in-(?P<obj>a|b)-h(?P<h>\d+)$"
)
ANGLE_FID_RE = re.compile(
    r"^w-ang-(?P<sub>a|b)-(?P<planet>[a-z0-9-]+)-(?P<aspect>[a-z]+)"
    r"-(?P<obj>a|b)-(?P<angle>asc|desc|mc|ic)$"
)

# Equal-house cusps starting at 0°: house n covers [(n-1)*30, n*30).
EQUAL_CUSPS_0 = [float(i * 30) for i in range(12)]


def _sample_pair(i=0):
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
    ]
    a_raw, b_raw = pairs[i]
    return validate_input(a_raw), validate_input(b_raw)


def _house_of_cusps(cusps):
    """Placidus-style house_of closure over fixed cusps (same logic as chart_engine)."""

    def house_of(lon):
        lon %= 360
        for i in range(12):
            a = cusps[i]
            b = cusps[(i + 1) % 12]
            if a < b:
                if a <= lon < b:
                    return i + 1
            else:
                if lon >= a or lon < b:
                    return i + 1
        return 12

    return house_of


def _pos_map(**kwargs):
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


def _assert_sorted_salience_fid(arr):
    keys = [(-e["salience"], e["feature_id"]) for e in arr]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# House overlay — shape, direction, salience, asymmetry
# ---------------------------------------------------------------------------


def test_overlay_arrays_validate_and_raw_fact_shape():
    house_of_b = _house_of_cusps(EQUAL_CUSPS_0)
    pos_a = _pos_map(太陽=5.0, 火星=275.0)  # h1 and h10
    arr = synastry.compute_house_overlay(
        pos_a, house_of_b, visitor="A", owner="B"
    )
    assert arr, "expected at least one overlay entry"
    for ev in arr:
        semantics.validate_evidence(ev)
        assert ev["method"] == "house_overlay"
        rf = ev["raw_fact"]
        assert set(rf.keys()) == {"planet", "house_number", "house_system"}
        assert rf["house_system"] == "placidus"
        assert isinstance(rf["house_number"], int)
        assert 1 <= rf["house_number"] <= 12
        assert rf["planet"] in semantics.SLUGS["raw_to_internal"]


def test_overlay_feature_id_and_subject_object_direction():
    house_of_b = _house_of_cusps(EQUAL_CUSPS_0)
    pos_a = _pos_map(火星=275.0)  # house 10
    a_in_b = synastry.compute_house_overlay(
        pos_a, house_of_b, visitor="A", owner="B"
    )
    assert a_in_b
    for ev in a_in_b:
        assert ev["subject"] == "A"
        assert ev["object"] == "B"
        m = OVERLAY_FID_RE.fullmatch(ev["feature_id"])
        assert m, ev["feature_id"]
        assert m.group("sub") == "a"
        assert m.group("obj") == "b"
        assert FEATURE_ID_RE.fullmatch(ev["feature_id"])

    house_of_a = _house_of_cusps(EQUAL_CUSPS_0)
    pos_b = _pos_map(水星=45.0)
    b_in_a = synastry.compute_house_overlay(
        pos_b, house_of_a, visitor="B", owner="A"
    )
    assert b_in_a
    for ev in b_in_a:
        assert ev["subject"] == "B"
        assert ev["object"] == "A"
        m = OVERLAY_FID_RE.fullmatch(ev["feature_id"])
        assert m, ev["feature_id"]
        assert m.group("sub") == "b"
        assert m.group("obj") == "a"


def test_overlay_salience_ease_and_convergence_flags():
    house_of = _house_of_cusps(EQUAL_CUSPS_0)
    # 太陽 weight 1.0 → salience = round(1.0 * 0.8, 3) = 0.8
    pos = _pos_map(太陽=10.0)
    arr = synastry.compute_house_overlay(pos, house_of, visitor="A", owner="B")
    sun = next(e for e in arr if e["raw_fact"]["planet"] == "Sun")
    assert sun["salience"] == round(semantics.PLANET_WEIGHT["太陽"] * 0.8, 3)
    assert sun["salience"] == 0.8
    assert sun["ease_or_tension"] == "mixed"
    assert sun["participates_in_convergence"] is False


def test_overlay_asymmetric_mars_tenth_house():
    """A Mars in B H10 does not imply B Mars in A H10."""
    # B houses: equal from 0° → H10 = [270, 300)
    house_of_b = _house_of_cusps(EQUAL_CUSPS_0)
    # A houses: equal from 90° → H1=[90,120), … H10=[0,30)
    house_of_a = _house_of_cusps([(90.0 + i * 30.0) % 360 for i in range(12)])

    pos_a = _pos_map(火星=280.0)  # in B H10
    pos_b = _pos_map(火星=50.0)  # in A: 50 is in H11 of offset-90 cusps, not H10

    a_in_b = synastry.compute_house_overlay(
        pos_a, house_of_b, visitor="A", owner="B"
    )
    b_in_a = synastry.compute_house_overlay(
        pos_b, house_of_a, visitor="B", owner="A"
    )

    a_mars_h = {
        e["raw_fact"]["house_number"]
        for e in a_in_b
        if e["raw_fact"]["planet"] == "Mars"
    }
    b_mars_h = {
        e["raw_fact"]["house_number"]
        for e in b_in_a
        if e["raw_fact"]["planet"] == "Mars"
    }
    assert 10 in a_mars_h
    assert 10 not in b_mars_h
    # arrays are independent (different feature_id prefixes / subjects)
    assert {e["subject"] for e in a_in_b} == {"A"}
    assert {e["subject"] for e in b_in_a} == {"B"}


def test_overlay_includes_north_node_excludes_south_node():
    house_of = _house_of_cusps(EQUAL_CUSPS_0)
    pos = _pos_map()
    arr = synastry.compute_house_overlay(pos, house_of, visitor="A", owner="B")
    planets = {e["raw_fact"]["planet"] for e in arr}
    assert planets == EXPECTED_OVERLAY_PLANETS
    blob = json.dumps(arr, ensure_ascii=False)
    assert "南交點" not in blob
    assert "south-node" not in blob


def test_overlay_sorted_salience_desc_feature_id_asc():
    house_of = _house_of_cusps(EQUAL_CUSPS_0)
    pos = _pos_map()
    arr = synastry.compute_house_overlay(pos, house_of, visitor="A", owner="B")
    assert len(arr) == 11  # all 11 bodies, one house each
    _assert_sorted_salience_fid(arr)


# ---------------------------------------------------------------------------
# Angle contacts — salience hand calc, orbs, no angle-angle, validate
# ---------------------------------------------------------------------------


def test_angle_longitudes_derives_desc_and_ic():
    assert synastry.angle_longitudes(10.0, 100.0) == {
        "上升": 10.0,
        "下降": 190.0,
        "天頂": 100.0,
        "天底": 280.0,
    }
    # wrap around 0°
    assert synastry.angle_longitudes(350.0, 20.0) == {
        "上升": 350.0,
        "下降": 170.0,
        "天頂": 20.0,
        "天底": 200.0,
    }
    # normalize inputs outside [0, 360)
    out = synastry.angle_longitudes(370.0, -10.0)
    assert out["上升"] == 10.0
    assert out["下降"] == 190.0
    assert out["天頂"] == 350.0
    assert out["天底"] == 170.0


def test_angle_contact_sun_trine_asc_hand_calc_salience():
    # Sun at 118°, ASC at 0° → shortest arc 118 ≈ trine 120, orb 2.0
    pos = _pos_map(太陽=118.0)
    angles = {"上升": 0.0, "下降": 180.0, "天頂": 90.0, "天底": 270.0}
    arr = synastry.compute_angle_contacts(
        pos, angles, subject="A", obj="B"
    )
    hit = [
        e
        for e in arr
        if e["raw_fact"]["planet"] == "Sun"
        and e["raw_fact"]["angle"] == "asc"
        and e["raw_fact"]["aspect"] == "trine"
    ]
    assert len(hit) == 1
    ev = hit[0]
    assert abs(ev["raw_fact"]["orb"] - 2.0) < 1e-9
    # orb_weight = 1-(2/4)^2 = 0.75; planet_weight fixed 0.5 → salience 0.375
    assert ev["salience"] == 0.375
    assert ev["salience"] != 0.75
    assert ev["participates_in_convergence"] is True
    semantics.validate_evidence(ev)


def test_angle_contact_orb_exactly_at_max_included_with_zero_salience():
    # Mercury–ASC conjunction special orb = 3°; place at exact boundary.
    pos = _pos_map(水星=3.0)
    angles = {"上升": 0.0, "下降": 180.0, "天頂": 90.0, "天底": 270.0}
    assert semantics.resolve_max_orb("水星", "上升", "conjunction") == 3.0
    arr = synastry.compute_angle_contacts(
        pos, angles, subject="A", obj="B"
    )
    hit = [
        e
        for e in arr
        if e["raw_fact"]["planet"] == "Mercury"
        and e["raw_fact"]["angle"] == "asc"
        and e["raw_fact"]["aspect"] == "conjunction"
    ]
    assert len(hit) == 1
    assert hit[0]["raw_fact"]["orb"] == 3.0
    assert hit[0]["salience"] == 0.0


def test_angle_contact_moon_asc_dimensions():
    pos = _pos_map(月亮=0.5)
    angles = {"上升": 0.0, "下降": 180.0, "天頂": 90.0, "天底": 270.0}
    arr = synastry.compute_angle_contacts(
        pos, angles, subject="A", obj="B"
    )
    hit = [
        e
        for e in arr
        if e["raw_fact"]["planet"] == "Moon"
        and e["raw_fact"]["angle"] == "asc"
        and e["raw_fact"]["aspect"] == "conjunction"
    ]
    assert len(hit) == 1
    assert hit[0]["dimensions"] == [
        "emotion_regulation",
        "intimacy_attraction",
        "timing_context",
        "autonomy_boundary",
    ]
    # Must include angle themes, not planet-only dimensions_for_planet.
    assert hit[0]["dimensions"] != semantics.dimensions_for_planet("月亮")


def test_angle_contact_opposition_and_square():
    angles = {"上升": 0.0, "下降": 180.0, "天頂": 90.0, "天底": 270.0}
    # Sun–ASC opposition, orb 1.0 (within luminary–angle 4°)
    pos_opp = _pos_map(太陽=179.0)
    arr_opp = synastry.compute_angle_contacts(
        pos_opp, angles, subject="A", obj="B"
    )
    opp = [
        e
        for e in arr_opp
        if e["raw_fact"]["planet"] == "Sun"
        and e["raw_fact"]["angle"] == "asc"
        and e["raw_fact"]["aspect"] == "opposition"
    ]
    assert len(opp) == 1
    assert abs(opp[0]["raw_fact"]["orb"] - 1.0) < 1e-9
    assert opp[0]["raw_fact"]["exact_angle"] == 180
    assert opp[0]["ease_or_tension"] == "tension"

    # Mars–ASC square, exact (non-luminary–angle max orb 3°)
    pos_sq = _pos_map(火星=90.0)
    arr_sq = synastry.compute_angle_contacts(
        pos_sq, angles, subject="A", obj="B"
    )
    sq = [
        e
        for e in arr_sq
        if e["raw_fact"]["planet"] == "Mars"
        and e["raw_fact"]["angle"] == "asc"
        and e["raw_fact"]["aspect"] == "square"
    ]
    assert len(sq) == 1
    assert abs(sq[0]["raw_fact"]["orb"] - 0.0) < 1e-9
    assert sq[0]["raw_fact"]["exact_angle"] == 90
    assert sq[0]["ease_or_tension"] == "tension"


def test_angle_contacts_validate_and_feature_id_template():
    pos_a = _pos_map(太陽=0.0)
    angles_b = {"上升": 0.5, "下降": 180.5, "天頂": 90.0, "天底": 270.0}
    a_to_b = synastry.compute_angle_contacts(
        pos_a, angles_b, subject="A", obj="B"
    )
    assert a_to_b
    for ev in a_to_b:
        semantics.validate_evidence(ev)
        assert ev["method"] == "angle_contact"
        assert ev["subject"] == "A"
        assert ev["object"] == "B"
        m = ANGLE_FID_RE.fullmatch(ev["feature_id"])
        assert m, ev["feature_id"]
        assert m.group("sub") == "a"
        assert m.group("obj") == "b"

    pos_b = _pos_map(月亮=30.0)
    angles_a = {"上升": 30.0, "下降": 210.0, "天頂": 120.0, "天底": 300.0}
    b_to_a = synastry.compute_angle_contacts(
        pos_b, angles_a, subject="B", obj="A"
    )
    assert b_to_a
    for ev in b_to_a:
        semantics.validate_evidence(ev)
        assert ev["subject"] == "B"
        assert ev["object"] == "A"
        m = ANGLE_FID_RE.fullmatch(ev["feature_id"])
        assert m, ev["feature_id"]
        assert m.group("sub") == "b"
        assert m.group("obj") == "a"


def test_angle_orb_north_node_to_asc_is_two_degrees():
    # Node at 1.5° from ASC → within 2° special orb
    pos = _pos_map(北交點=1.5)
    angles = {"上升": 0.0, "下降": 180.0, "天頂": 90.0, "天底": 270.0}
    arr = synastry.compute_angle_contacts(
        pos, angles, subject="A", obj="B"
    )
    node_asc = [
        e
        for e in arr
        if e["raw_fact"]["planet"] == "North Node"
        and e["raw_fact"]["angle"] == "asc"
        and e["raw_fact"]["aspect"] == "conjunction"
    ]
    assert len(node_asc) == 1
    assert abs(node_asc[0]["raw_fact"]["orb"] - 1.5) < 1e-9

    # 2.1° > 2° max → excluded
    pos_out = _pos_map(北交點=2.1)
    arr_out = synastry.compute_angle_contacts(
        pos_out, angles, subject="A", obj="B"
    )
    node_out = [
        e
        for e in arr_out
        if e["raw_fact"]["planet"] == "North Node"
        and e["raw_fact"]["angle"] == "asc"
        and e["raw_fact"]["aspect"] == "conjunction"
    ]
    assert node_out == []


def test_angle_orb_moon_trine_asc_uses_4_not_6():
    # Moon–ASC special orb = 4° (not luminary aspect base 5+1=6)
    angles = {"上升": 0.0, "下降": 180.0, "天頂": 90.0, "天底": 270.0}
    # trine target 120°; orb 3.9 → inside 4°
    pos_in = _pos_map(月亮=120.0 - 3.9)
    arr_in = synastry.compute_angle_contacts(
        pos_in, angles, subject="A", obj="B"
    )
    hits_in = [
        e
        for e in arr_in
        if e["raw_fact"]["planet"] == "Moon"
        and e["raw_fact"]["angle"] == "asc"
        and e["raw_fact"]["aspect"] == "trine"
    ]
    assert len(hits_in) == 1

    # orb 4.1 → outside 4° (would be inside if wrongly using 6°)
    pos_out = _pos_map(月亮=120.0 - 4.1)
    arr_out = synastry.compute_angle_contacts(
        pos_out, angles, subject="A", obj="B"
    )
    hits_out = [
        e
        for e in arr_out
        if e["raw_fact"]["planet"] == "Moon"
        and e["raw_fact"]["angle"] == "asc"
        and e["raw_fact"]["aspect"] == "trine"
    ]
    assert hits_out == []


def test_angle_to_angle_produces_no_evidence():
    """Only planets (11-set) aspect angles; angle–angle pairs never emit."""
    # Put "planet" longitudes on angle positions only — but compute takes planets
    # vs angles. Guard: raw_fact.angle is always an angle slug, planet never is.
    pos = _pos_map(太陽=0.0, 月亮=90.0)
    angles = {"上升": 0.0, "下降": 180.0, "天頂": 90.0, "天底": 270.0}
    arr = synastry.compute_angle_contacts(
        pos, angles, subject="A", obj="B"
    )
    assert arr, "expected angle-contact evidence for sun/moon near angles"
    angle_slugs = {"asc", "desc", "mc", "ic"}
    for ev in arr:
        assert ev["raw_fact"]["angle"] in angle_slugs
        assert ev["raw_fact"]["planet"] not in {
            "Ascendant",
            "Descendant",
            "Midheaven",
            "Imum Coeli",
        }
    # Explicit: feature_id never has angle slug in the planet slot against angle
    for ev in arr:
        m = ANGLE_FID_RE.fullmatch(ev["feature_id"])
        assert m
        assert m.group("planet") not in angle_slugs


def test_angle_contacts_include_north_node_exclude_south_node():
    # All 11 bodies present so the set equality is meaningful (not a subset
    # of a hand-picked one-body map).
    pos = _pos_map(北交點=0.0)
    angles = {"上升": 0.5, "下降": 180.5, "天頂": 90.0, "天底": 270.0}
    arr = synastry.compute_angle_contacts(
        pos, angles, subject="A", obj="B"
    )
    assert arr
    planets = {e["raw_fact"]["planet"] for e in arr}
    assert "North Node" in planets
    assert planets <= EXPECTED_OVERLAY_PLANETS
    assert "South Node" not in planets


def test_angle_contacts_sorted_salience_desc_feature_id_asc():
    pos = _pos_map(太陽=0.0, 月亮=0.5, 水星=1.0)
    angles = {"上升": 0.0, "下降": 180.0, "天頂": 90.0, "天底": 270.0}
    arr = synastry.compute_angle_contacts(
        pos, angles, subject="A", obj="B"
    )
    assert arr
    _assert_sorted_salience_fid(arr)


# ---------------------------------------------------------------------------
# build_synastry integration: time unknown, completeness, determinism, sort
# ---------------------------------------------------------------------------


def _known_person(side: str):
    if side == "a":
        return validate_input(
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
    return validate_input(
        {
            "name": "B",
            "gender": "男",
            "date": "1988-03-20",
            "time": "14:00",
            "tz": 8,
            "lat": 25.0,
            "lon": 121.5,
        }
    )


def _unknown_person(side: str):
    if side == "a":
        return validate_input(
            {
                "name": "A",
                "gender": "女",
                "date": "1990-06-15",
                "time": "unknown",
                "tz": 8,
                "lat": 25.033,
                "lon": 121.5654,
            },
            allow_unknown_time=True,
        )
    return validate_input(
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


@pytest.mark.parametrize("unknown_side", ["a", "b"])
def test_time_unknown_empties_four_arrays_and_sets_unavailable_partial(unknown_side):
    if unknown_side == "a":
        inp_a, inp_b = _unknown_person("a"), _known_person("b")
    else:
        inp_a, inp_b = _known_person("a"), _unknown_person("b")
    payload = synastry.build_synastry_json(inp_a, inp_b)
    assert payload["ok"] is True  # HTTP 200 equivalent
    w = payload["synastry"]["western"]
    for key in (
        "a_planets_in_b_houses",
        "b_planets_in_a_houses",
        "angle_contacts_a_to_b",
        "angle_contacts_b_to_a",
    ):
        assert key in w
        assert w[key] == []
    assert payload["synastry"]["unavailable"] == [
        "house_overlay",
        "angle_contacts",
        "hd_lines",
    ]
    assert payload["evidence_completeness"] == "partial"
    # Aspects are time-independent for completeness of the pair geometry;
    # they must remain non-empty when only overlay/angles are suppressed.
    assert payload["synastry"]["western"]["aspects"]


def test_evidence_completeness_full_when_aspects_and_available():
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    assert payload["synastry"]["western"]["aspects"]
    assert payload["synastry"]["unavailable"] == []
    assert payload["evidence_completeness"] == "full"
    assert payload["ok"] is True


def test_evidence_completeness_partial_when_aspects_empty(monkeypatch):
    """aspects empty → partial (still ok / HTTP 200), even with times known.

    Motivating case is far-apart birthdays; we force empty aspects via
    compute_western_aspects so the completeness rule is isolated and stable.
    """
    monkeypatch.setattr(synastry, "compute_western_aspects", lambda *a, **k: [])
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    assert payload["synastry"]["western"]["aspects"] == []
    assert payload["evidence_completeness"] == "partial"
    assert payload["ok"] is True
    # Times known → overlay/angles still available; unavailable stays empty.
    assert payload["synastry"]["unavailable"] == []


def test_evidence_completeness_domain_is_exactly_full_or_partial(monkeypatch):
    """Across all completeness branches the engine only ever emits full|partial."""
    collected: set[str] = set()

    # 1) both times known, aspects non-empty
    p_full = synastry.build_synastry_json(_known_person("a"), _known_person("b"))
    collected.add(p_full["evidence_completeness"])
    assert p_full["evidence_completeness"] == "full"

    # 2) A unknown
    p_a = synastry.build_synastry_json(_unknown_person("a"), _known_person("b"))
    collected.add(p_a["evidence_completeness"])
    assert p_a["evidence_completeness"] == "partial"

    # 3) B unknown
    p_b = synastry.build_synastry_json(_known_person("a"), _unknown_person("b"))
    collected.add(p_b["evidence_completeness"])
    assert p_b["evidence_completeness"] == "partial"

    # 4) both unknown
    p_both = synastry.build_synastry_json(
        _unknown_person("a"), _unknown_person("b")
    )
    collected.add(p_both["evidence_completeness"])
    assert p_both["evidence_completeness"] == "partial"

    # 5) aspects forced empty, times known
    monkeypatch.setattr(synastry, "compute_western_aspects", lambda *a, **k: [])
    p_empty = synastry.build_synastry_json(_known_person("a"), _known_person("b"))
    collected.add(p_empty["evidence_completeness"])
    assert p_empty["evidence_completeness"] == "partial"

    assert collected == {"full", "partial"}


def test_build_synastry_four_arrays_sorted_and_nonempty_when_times_known():
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    w = payload["synastry"]["western"]
    for key in (
        "a_planets_in_b_houses",
        "b_planets_in_a_houses",
        "angle_contacts_a_to_b",
        "angle_contacts_b_to_a",
    ):
        arr = w[key]
        assert arr, f"{key} should be non-empty when both times known"
        for ev in arr:
            semantics.validate_evidence(ev)
            assert ev["data_confidence"] == 0.95
        _assert_sorted_salience_fid(arr)

    # Direction checks on live charts
    for ev in w["a_planets_in_b_houses"]:
        assert ev["subject"] == "A" and ev["object"] == "B"
    for ev in w["b_planets_in_a_houses"]:
        assert ev["subject"] == "B" and ev["object"] == "A"
    for ev in w["angle_contacts_a_to_b"]:
        assert ev["subject"] == "A" and ev["object"] == "B"
    for ev in w["angle_contacts_b_to_a"]:
        assert ev["subject"] == "B" and ev["object"] == "A"


def test_build_synastry_overlay_and_angles_wired_to_object_chart():
    """Payload path must use the object chart's houses/angles, not the subject's.

    Labels alone are not enough: a swapped house_of / angles dict keeps
    subject/object strings correct while placing planets in the wrong chart.
    """
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    w = payload["synastry"]["western"]

    _jd_a, pos_a, _r_a, _c_a, asc_a, mc_a, house_of_a = western(inp_a)
    _jd_b, pos_b, _r_b, _c_b, asc_b, mc_b, house_of_b = western(inp_b)
    angles_a = synastry.angle_longitudes(asc_a, mc_a)
    angles_b = synastry.angle_longitudes(asc_b, mc_b)

    # House overlay: each planet's house_number must match object house_of.
    for ev in w["a_planets_in_b_houses"]:
        internal = semantics.raw_fact_to_internal(ev["raw_fact"]["planet"])
        assert ev["raw_fact"]["house_number"] == house_of_b(pos_a[internal])
    assert w["b_planets_in_a_houses"], "expected non-empty b_planets_in_a_houses"
    for ev in w["b_planets_in_a_houses"]:
        internal = semantics.raw_fact_to_internal(ev["raw_fact"]["planet"])
        assert ev["raw_fact"]["house_number"] == house_of_a(pos_b[internal])

    # If wiring were swapped, many houses would disagree with the correct object.
    swapped_a = [
        e
        for e in w["a_planets_in_b_houses"]
        if e["raw_fact"]["house_number"]
        != house_of_a(pos_a[semantics.raw_fact_to_internal(e["raw_fact"]["planet"])])
    ]
    # At least one body must land in a different house in A vs B (real charts).
    assert swapped_a, "charts must disagree on at least one house placement"

    # Angle contacts: each contact must match recomputation against object angles.
    def _assert_angle_contacts(arr, planet_pos, object_angles, subject, obj):
        expected = {
            e["feature_id"]: e
            for e in synastry.compute_angle_contacts(
                planet_pos, object_angles, subject=subject, obj=obj
            )
        }
        assert arr, f"expected angle contacts for {subject}->{obj}"
        for ev in arr:
            exp = expected[ev["feature_id"]]
            assert ev["raw_fact"] == exp["raw_fact"]
            assert ev["salience"] == exp["salience"]
        assert {e["feature_id"] for e in arr} == set(expected)

    _assert_angle_contacts(
        w["angle_contacts_a_to_b"], pos_a, angles_b, "A", "B"
    )
    _assert_angle_contacts(
        w["angle_contacts_b_to_a"], pos_b, angles_a, "B", "A"
    )

    # Wrong object angles must not equal the shipped arrays (mutation guard).
    wrong_a_to_b = synastry.compute_angle_contacts(
        pos_a, angles_a, subject="A", obj="B"
    )
    assert {e["feature_id"] for e in w["angle_contacts_a_to_b"]} != {
        e["feature_id"] for e in wrong_a_to_b
    }


def test_build_synastry_excludes_south_node_from_real_positions():
    """western() includes 南交點 in pos; synastry arrays must still omit it."""
    inp_a, inp_b = _sample_pair(0)
    _jd, pos_a, *_rest = western(inp_a)
    assert "南交點" in pos_a

    payload = synastry.build_synastry_json(inp_a, inp_b)
    w = payload["synastry"]["western"]
    for key in (
        "a_planets_in_b_houses",
        "b_planets_in_a_houses",
        "angle_contacts_a_to_b",
        "angle_contacts_b_to_a",
        "aspects",
    ):
        assert w[key], f"expected non-empty {key}"
        blob = json.dumps(w[key], ensure_ascii=False)
        assert "南交點" not in blob
        assert "South Node" not in blob
        assert "south-node" not in blob
    overlay_planets = {
        e["raw_fact"]["planet"] for e in w["a_planets_in_b_houses"]
    }
    assert overlay_planets == EXPECTED_OVERLAY_PLANETS


def test_production_house_of_wraparound_used_by_overlay():
    """Cusp closure that crosses 0° must come from production western().house_of."""
    inp_a, inp_b = _sample_pair(0)
    _jd_b, _pos_b, _r_b, cusps_b, _asc_b, _mc_b, house_of_b = western(inp_b)

    wrap_i = None
    for i in range(12):
        a = cusps_b[i]
        b = cusps_b[(i + 1) % 12]
        if a > b:
            wrap_i = i
            break
    assert wrap_i is not None, "Placidus must have one cusp pair crossing 0°"

    a = cusps_b[wrap_i]
    b = cusps_b[(wrap_i + 1) % 12]
    # Just after start cusp, and just before end cusp — both in house wrap_i+1.
    lon_after_a = (a + 0.01) % 360
    lon_before_b = (b - 0.01) % 360
    assert house_of_b(lon_after_a) == wrap_i + 1
    assert house_of_b(lon_before_b) == wrap_i + 1
    assert house_of_b(b % 360) == ((wrap_i + 1) % 12) + 1

    # Ship path: feed a visitor body at the wrap longitude and require the
    # overlay house_number match production house_of_b (not a local reimplementation).
    pos_a = {body: 0.0 for body in synastry.ASPECT_BODIES}
    pos_a["太陽"] = lon_after_a
    arr = synastry.compute_house_overlay(
        pos_a, house_of_b, visitor="A", owner="B"
    )
    sun = next(e for e in arr if e["raw_fact"]["planet"] == "Sun")
    assert sun["raw_fact"]["house_number"] == house_of_b(lon_after_a)

    # Full payload path also uses production house_of for the object chart.
    payload = synastry.build_synastry_json(inp_a, inp_b)
    _jd_a, pos_a_live, *_ = western(inp_a)
    for ev in payload["synastry"]["western"]["a_planets_in_b_houses"]:
        internal = semantics.raw_fact_to_internal(ev["raw_fact"]["planet"])
        assert ev["raw_fact"]["house_number"] == house_of_b(pos_a_live[internal])


def test_same_input_byte_identical_across_hash_seeds():
    """Stdout must match under different PYTHONHASHSEED (subprocess, not same proc)."""
    script = ROOT / "scripts" / "chart_engine.py"
    base_args = [
        sys.executable,
        str(script),
        "--json",
        "--name",
        "A",
        "--gender",
        "女",
        "--date",
        "1990-06-15",
        "--time",
        "08:30",
        "--tz",
        "8",
        "--lat",
        "25.033",
        "--lon",
        "121.5654",
        "--date-b",
        "1988-03-20",
        "--time-b",
        "14:00",
        "--tz-b",
        "8",
        "--lat-b",
        "25.0",
        "--lon-b",
        "121.5",
        "--gender-b",
        "男",
    ]

    def _stdout(seed: int) -> bytes:
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = str(seed)
        result = subprocess.run(
            base_args,
            cwd=ROOT,
            capture_output=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout, "expected dual-mode JSON on stdout"
        return result.stdout

    out0 = _stdout(0)
    out1 = _stdout(1)
    assert out0 == out1
    # Sanity: parseable synastry payload
    payload = json.loads(out0.decode("utf-8"))
    assert payload["ok"] is True
    assert payload["synastry"]["western"]["aspects"]
