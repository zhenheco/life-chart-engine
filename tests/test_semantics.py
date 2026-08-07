"""E2 — semantics-v1 unit tests (orb, themes, feature_id, validate_evidence)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import semantics  # noqa: E402
from semantics import REQUIRED_EVIDENCE_KEYS  # noqa: E402


def _valid_evidence(**overrides):
    base = {
        "feature_id": "w-syn-a-mercury-square-b-saturn",
        "system": "western",
        "method": "synastry_aspect",
        "method_version": "western-synastry-v1",
        "subject": "A",
        "object": "B",
        "raw_fact": {
            "planet_a": "Mercury",
            "aspect": "square",
            "planet_b": "Saturn",
            "exact_angle": 90,
            "actual_angle": 89.3,
            "orb": 0.7,
        },
        "dimensions": ["communication", "commitment_stability", "autonomy_boundary"],
        "salience": 0.882,
        "ease_or_tension": "tension",
        "method_consensus": "core",
        "data_confidence": 0.95,
        "participates_in_convergence": True,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Step 1 — validate_evidence rejection (must be green before other AC shape tests)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_key", REQUIRED_EVIDENCE_KEYS)
def test_validate_evidence_rejects_missing_required_key(missing_key):
    obj = _valid_evidence()
    del obj[missing_key]
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_ease_or_tension_out_of_domain():
    obj = _valid_evidence(ease_or_tension="hostile")
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_feature_id_with_underscore():
    obj = _valid_evidence(feature_id="w-syn-a-north_node-square-b-saturn")
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_feature_id_not_matching_pattern():
    # uppercase and slash — fails ^[a-z]+-[a-z0-9-]+$
    obj = _valid_evidence(feature_id="W-syn/a-mercury")
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)
    assert not re.fullmatch(r"^[a-z]+-[a-z0-9-]+$", "W-syn/a-mercury")


def test_validate_evidence_rejects_dimensions_outside_themes_v1():
    obj = _valid_evidence(dimensions=["communication", "not_a_theme"])
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_system_out_of_domain():
    obj = _valid_evidence(system="vedic")
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_method_version_mismatch():
    # valid method with the wrong school's method_version
    obj = _valid_evidence(
        method="synastry_aspect",
        method_version="human-design-synastry-v1",
    )
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_method_consensus_out_of_domain():
    obj = _valid_evidence(method_consensus="experimental")
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_raw_fact_not_mapping():
    obj = _valid_evidence(raw_fact=["not", "a", "mapping"])
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_participates_in_convergence_not_bool():
    obj = _valid_evidence(participates_in_convergence=1)
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_salience_not_unit_interval_rounded3():
    # 0.8821 != round(0.8821, 3); also covers the round(x, 3) half of the rule
    obj = _valid_evidence(salience=0.8821)
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_data_confidence_not_unit_interval_rounded3():
    # out of [0, 1]
    obj = _valid_evidence(data_confidence=1.5)
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_rejects_forbidden_key():
    obj = _valid_evidence()
    obj["interpretive_valence"] = "positive"
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


@pytest.mark.parametrize("forbidden_key", ["score_total", "compatibility_pct"])
def test_validate_evidence_rejects_forbidden_key_substrings(forbidden_key):
    """Forbidden tokens are substring matches (e.g. score_total contains 'score')."""
    obj = _valid_evidence()
    obj[forbidden_key] = 0.5
    with pytest.raises(ValueError):
        semantics.validate_evidence(obj)


def test_validate_evidence_accepts_canonical_example():
    semantics.validate_evidence(_valid_evidence())


# ---------------------------------------------------------------------------
# orb_weight
# ---------------------------------------------------------------------------


def test_orb_weight_zero_orb_is_one():
    assert semantics.orb_weight(0.0, 5.0) == 1.0


def test_orb_weight_at_max_is_zero():
    assert semantics.orb_weight(5.0, 5.0) == 0.0


def test_orb_weight_canonical_mercury_saturn():
    # 1 - (0.7/5)^2 = 0.9804
    assert abs(semantics.orb_weight(0.7, 5.0) - 0.9804) < 1e-12


# ---------------------------------------------------------------------------
# resolve_max_orb — order: node/angle special → no sun/moon +1; else aspect + optional +1 ≤7
# ---------------------------------------------------------------------------


def test_resolve_max_orb_sun_square_north_node_uses_two_not_six():
    """North Node either end → 2°, no +1° for Sun."""
    max_orb = semantics.resolve_max_orb("太陽", "北交點", "square")
    assert max_orb == 2.0


def test_resolve_max_orb_never_exceeds_seven():
    """Invariant: no (body, body, aspect) combination yields max_orb > 7°.

    The 7° hard cap in ``resolve_max_orb`` is defensive; current base orbs
    never force it. This test documents the ≤7 invariant, not that the cap
    itself is reachable under today's ``_ASPECT_ROWS``.
    """
    bodies = list(semantics.PLANET_WEIGHT)
    for a in bodies:
        for b in bodies:
            for aspect in semantics.ASPECT_BY_SLUG:
                assert semantics.resolve_max_orb(a, b, aspect) <= 7.0


def test_resolve_max_orb_luminary_and_non_luminary_examples():
    # opposition base 6 +1 = 7
    assert semantics.resolve_max_orb("太陽", "月亮", "opposition") == 7.0
    # conjunction base 6 +1 = 7
    assert semantics.resolve_max_orb("太陽", "水星", "conjunction") == 7.0
    # square base 5 +1 = 6
    assert semantics.resolve_max_orb("月亮", "金星", "square") == 6.0
    # no luminary → square stays 5
    assert semantics.resolve_max_orb("水星", "土星", "square") == 5.0
    # no luminary → sextile/trine base orbs (not luminary-boosted)
    assert semantics.resolve_max_orb("水星", "土星", "sextile") == 3.0
    assert semantics.resolve_max_orb("水星", "土星", "trine") == 5.0


# ---------------------------------------------------------------------------
# planet_weight_for_aspect — angle points
# ---------------------------------------------------------------------------


def test_planet_weight_sun_ascendant_is_half_not_one():
    w = semantics.planet_weight_for_aspect("太陽", "上升")
    assert w == 0.5
    assert w != 1.0


def test_planet_weight_moon_midheaven_is_half_not_one():
    w = semantics.planet_weight_for_aspect("月亮", "天頂")
    assert w == 0.5
    assert w != 1.0


# ---------------------------------------------------------------------------
# feature_id
# ---------------------------------------------------------------------------


def test_feature_id_synastry_aspect_template():
    fid = semantics.feature_id(
        "synastry_aspect",
        planet_a="mercury",
        aspect="square",
        planet_b="saturn",
    )
    assert fid == "w-syn-a-mercury-square-b-saturn"
    assert re.fullmatch(r"^[a-z]+-[a-z0-9-]+$", fid)
    assert "_" not in fid


def test_feature_id_deterministic():
    a = semantics.feature_id(
        "synastry_aspect", planet_a="sun", aspect="trine", planet_b="mars"
    )
    b = semantics.feature_id(
        "synastry_aspect", planet_a="sun", aspect="trine", planet_b="mars"
    )
    assert a == b == "w-syn-a-sun-trine-b-mars"


# ---------------------------------------------------------------------------
# dimensions order (A planet themes then B, first-seen dedupe)
# ---------------------------------------------------------------------------


def test_dimensions_mercury_square_saturn_order():
    dims = semantics.dimensions_for_aspect("水星", "土星")
    assert dims == ["communication", "commitment_stability", "autonomy_boundary"]


def test_dimensions_dedupe_first_seen():
    # 太陽 has commitment_stability; 土星 also — only first kept
    dims = semantics.dimensions_for_aspect("太陽", "土星")
    assert dims == ["decision_power", "commitment_stability", "autonomy_boundary"]
    assert dims.count("commitment_stability") == 1


# ---------------------------------------------------------------------------
# THEMES_V1 vs fixture
# ---------------------------------------------------------------------------


def test_themes_v1_matches_checked_in_fixture():
    fixture = json.loads(
        (ROOT / "tests" / "fixtures" / "themes-v1.json").read_text(encoding="utf-8")
    )
    assert fixture["themes"] == list(semantics.THEMES_V1)


# ---------------------------------------------------------------------------
# ASPECT_BY_SLUG ease_or_tension table (all five major aspects)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "slug,expected_eot",
    [
        ("conjunction", "mixed"),
        ("sextile", "ease"),
        ("square", "tension"),
        ("trine", "ease"),
        ("opposition", "tension"),
    ],
)
def test_aspect_by_slug_ease_or_tension(slug, expected_eot):
    assert semantics.ASPECT_BY_SLUG[slug]["ease_or_tension"] == expected_eot


# ---------------------------------------------------------------------------
# Canonical evidence fields (mercury square saturn orb 0.7)
# ---------------------------------------------------------------------------


def test_canonical_mercury_square_saturn_evidence_fields():
    ev = semantics.evidence(
        method="synastry_aspect",
        planet_a="水星",
        planet_b="土星",
        aspect="square",
        actual_angle=89.3,
        orb=0.7,
        time_unknown_a=False,
        time_unknown_b=False,
    )
    assert ev["system"] == "western"
    assert ev["method"] == "synastry_aspect"
    assert ev["method_version"] == "western-synastry-v1"
    assert ev["subject"] == "A"
    assert ev["object"] == "B"
    assert ev["participates_in_convergence"] is True
    assert ev["salience"] == 0.882
    assert ev["dimensions"] == [
        "communication",
        "commitment_stability",
        "autonomy_boundary",
    ]
    assert ev["data_confidence"] == 0.95
    assert ev["raw_fact"]["aspect"] == "square"
    assert ev["feature_id"] == "w-syn-a-mercury-square-b-saturn"
    assert ev["ease_or_tension"] == "tension"
    assert ev["raw_fact"]["exact_angle"] == 90
    assert ev["raw_fact"]["planet_a"] == "Mercury"
    assert ev["raw_fact"]["planet_b"] == "Saturn"
    assert ev["raw_fact"]["orb"] == 0.7
    assert ev["raw_fact"]["actual_angle"] == 89.3
    semantics.validate_evidence(ev)


def test_north_node_planet_weight_is_half_not_max():
    """North Node either end → planet_weight 0.5 (not max with Venus 0.9)."""
    ev = semantics.evidence(
        method="synastry_aspect",
        planet_a="北交點",
        planet_b="金星",
        aspect="conjunction",
        actual_angle=0.5,
        orb=0.5,
        time_unknown_a=False,
        time_unknown_b=False,
    )
    ow = semantics.orb_weight(0.5, 2.0)
    # if wrongly max(0.5, 0.9)=0.9 → salience = round(ow*0.9, 3)
    wrong = round(ow * 0.9, 3)
    right = round(ow * 0.5, 3)
    assert ev["salience"] == right
    assert ev["salience"] != wrong


def test_data_confidence_both_known():
    ev = semantics.evidence(
        method="synastry_aspect",
        planet_a="水星",
        planet_b="土星",
        aspect="square",
        actual_angle=89.3,
        orb=0.7,
        time_unknown_a=False,
        time_unknown_b=False,
    )
    assert ev["data_confidence"] == 0.95


def test_data_confidence_unknown_side_moon_is_0_6():
    ev = semantics.evidence(
        method="synastry_aspect",
        planet_a="月亮",
        planet_b="土星",
        aspect="square",
        actual_angle=90.0,
        orb=0.0,
        time_unknown_a=True,
        time_unknown_b=False,
    )
    assert ev["data_confidence"] == 0.6


def test_data_confidence_known_side_moon_other_unknown_is_0_85():
    """Known-side Moon participates but the other side is unknown → 0.85 not 0.95."""
    ev = semantics.evidence(
        method="synastry_aspect",
        planet_a="月亮",
        planet_b="土星",
        aspect="square",
        actual_angle=90.0,
        orb=0.0,
        time_unknown_a=False,
        time_unknown_b=True,
    )
    assert ev["data_confidence"] == 0.85
