"""E4 — Human Design channel connections, merged center states, participants."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import semantics  # noqa: E402
import synastry  # noqa: E402
from validation import validate_input  # noqa: E402

FEATURE_ID_RE = re.compile(r"^[a-z]+-[a-z0-9-]+$")

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

# ---------------------------------------------------------------------------
# Spec-derived expectations (design.md §themes / §type→strategy / §authority)
# ---------------------------------------------------------------------------

SPEC_STRATEGY_BY_TYPE = {
    "顯示者": "告知後行動",
    "生產者": "等待回應",
    "顯示生產者": "等待回應後告知",
    "投射者": "等待被邀請",
    "反映者": "等待一個完整月亮週期",
}

SPEC_AUTHORITIES = {
    "情緒型權威",
    "薦骨型權威",
    "直覺型(脾)權威",
    "意志力(心)權威",
    "自我投射型權威",
    "無內在權威(心智投射/月亮)",
}

CENTER_SEQUENCE_RAW = [
    "Head",
    "Ajna",
    "Throat",
    "G",
    "Heart",
    "Solar Plexus",
    "Sacral",
    "Spleen",
    "Root",
]

SPEC_CENTER_THEMES_BY_RAW = {
    "Head": ["communication", "decision_power"],
    "Ajna": ["communication", "decision_power"],
    "Throat": ["communication", "action_tempo"],
    "G": ["commitment_stability", "autonomy_boundary"],
    "Heart": ["money_division", "decision_power"],
    "Solar Plexus": ["emotion_regulation", "conflict_repair"],
    "Sacral": ["action_tempo", "intimacy_attraction"],
    "Spleen": ["timing_context", "autonomy_boundary"],
    "Root": ["action_tempo", "emotion_regulation"],
}

SPEC_LINK_THEMES = {
    "electromagnetic": ["intimacy_attraction", "conflict_repair"],
    "dominance": ["decision_power", "autonomy_boundary"],
    "compromise": ["autonomy_boundary", "conflict_repair"],
    "companionship": ["commitment_stability", "action_tempo"],
}

SPEC_LINK_EASE = {
    "companionship": "ease",
    "electromagnetic": "mixed",
    "dominance": "tension",
    "compromise": "tension",
}

STATE_VALUES = {
    "a_defined",
    "b_defined",
    "both_defined",
    "defined_by_merge",
    "undefined",
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PERSON_A0 = {
    "name": "A0",
    "gender": "女",
    "date": "1990-06-15",
    "time": "08:30",
    "tz": 8,
    "lat": 25.033,
    "lon": 121.5654,
}
PERSON_B0 = {
    "name": "B0",
    "gender": "男",
    "date": "1988-03-20",
    "time": "14:00",
    "tz": 8,
    "lat": 25.0,
    "lon": 121.5,
}
PERSON_A1 = {
    "name": "A1",
    "gender": "男",
    "date": "1985-12-01",
    "time": "03:15",
    "tz": 8,
    "lat": 24.15,
    "lon": 120.67,
}
PERSON_B1 = {
    "name": "B1",
    "gender": "女",
    "date": "1992-07-22",
    "time": "19:45",
    "tz": 8,
    "lat": 22.63,
    "lon": 120.30,
}


def _sample_pair(i=0):
    pairs = [(PERSON_A0, PERSON_B0), (PERSON_A1, PERSON_B1)]
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


def _collect_feature_ids(obj, found=None):
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


# ---------------------------------------------------------------------------
# 9-grid classification (spec §人類圖連結判定)
# ---------------------------------------------------------------------------


def test_grid_0_0_is_none():
    link, owner = synastry.classify_hd_channel(3, 60, {7}, {8})
    assert link is None
    assert owner is None


def test_grid_0_1_is_none():
    link, owner = synastry.classify_hd_channel(3, 60, {7}, {3})
    assert link is None
    assert owner is None


def test_grid_0_2_is_dominance_owner_b():
    link, owner = synastry.classify_hd_channel(3, 60, {7}, {3, 60})
    assert link == "dominance"
    assert owner == "B"


def test_grid_1_0_is_none():
    link, owner = synastry.classify_hd_channel(3, 60, {3}, {8})
    assert link is None
    assert owner is None


def test_grid_1_1_complementary_is_electromagnetic():
    link, owner = synastry.classify_hd_channel(3, 60, {3}, {60})
    assert link == "electromagnetic"
    assert owner is None
    link_r, owner_r = synastry.classify_hd_channel(3, 60, {60}, {3})
    assert link_r == "electromagnetic"
    assert owner_r is None


def test_grid_1_1_same_single_gate_is_none():
    link, owner = synastry.classify_hd_channel(3, 60, {3}, {3})
    assert link is None
    assert owner is None


def test_grid_1_2_is_compromise_owner_b_not_dominance():
    link, owner = synastry.classify_hd_channel(3, 60, {3}, {3, 60})
    assert link == "compromise"
    assert owner == "B"


def test_grid_2_0_is_dominance_owner_a():
    link, owner = synastry.classify_hd_channel(3, 60, {3, 60}, {8})
    assert link == "dominance"
    assert owner == "A"


def test_grid_2_1_is_compromise_owner_a_not_dominance():
    link, owner = synastry.classify_hd_channel(3, 60, {3, 60}, {60})
    assert link == "compromise"
    assert owner == "A"


def test_grid_2_2_is_companionship():
    link, owner = synastry.classify_hd_channel(3, 60, {3, 60}, {3, 60})
    assert link == "companionship"
    assert owner is None


# ---------------------------------------------------------------------------
# Active gate extraction: duplicates collapse to one active gate
# ---------------------------------------------------------------------------


def test_same_gate_multi_planet_counts_once_in_active_gates():
    rows = [
        ("☉", 5, 1, 5, 2),
        ("☾", 5, 3, 5, 4),
        ("♄", 7, 1, 9, 2),
    ]
    assert synastry.hd_active_gates(rows) == {5, 7, 9}


def test_fast_gates_only_from_moon_mercury_venus_mars():
    rows = [
        ("☾", 5, 1, 6, 2),
        ("☿", 7, 1, 8, 2),
        ("♀", 9, 1, 10, 2),
        ("♂", 11, 1, 12, 2),
        ("☉", 13, 1, 14, 2),
        ("♃", 15, 1, 16, 2),
        ("♄", 17, 1, 18, 2),
    ]
    assert synastry.hd_fast_gates(rows) == {5, 6, 7, 8, 9, 10, 11, 12}


# ---------------------------------------------------------------------------
# channel_connections[] emission rules
# ---------------------------------------------------------------------------


def test_channel_at_most_once_and_none_not_emitted():
    # (3,60): a=2,b=1 → compromise; (5,15): a=1,b=0 → none (not emitted)
    out = synastry.compute_hd_channel_connections({3, 60, 5}, {60})
    assert len(out) == 1
    assert [ev["raw_fact"]["channel"] for ev in out] == ["3-60"]
    assert out[0]["raw_fact"]["link_type"] == "compromise"


def test_a_gates_b_gates_sorted_asc_and_centers_lo_to_hi():
    out = synastry.compute_hd_channel_connections({60, 3}, {3, 60})
    assert len(out) == 1
    rf = out[0]["raw_fact"]
    assert rf["channel"] == "3-60"
    assert rf["a_gates"] == [3, 60]
    assert rf["b_gates"] == [3, 60]
    assert rf["centers"] == ["Sacral", "Root"]


def test_merged_channels_normalized_and_sorted():
    merged = synastry.merged_hd_channels({34, 10, 5}, {20})
    assert merged == [(10, 20), (10, 34), (20, 34)]


# ---------------------------------------------------------------------------
# Four link-type salience constants (one test each — no other AC catches these)
# ---------------------------------------------------------------------------


def test_salience_electromagnetic_is_0_9():
    out = synastry.compute_hd_channel_connections({3}, {60})
    assert out
    assert out[0]["raw_fact"]["link_type"] == "electromagnetic"
    assert out[0]["salience"] == 0.9


def test_salience_companionship_is_0_9():
    out = synastry.compute_hd_channel_connections({3, 60}, {3, 60})
    assert out
    assert out[0]["raw_fact"]["link_type"] == "companionship"
    assert out[0]["salience"] == 0.9


def test_salience_dominance_is_0_8():
    out = synastry.compute_hd_channel_connections({3, 60}, set())
    assert out
    assert out[0]["raw_fact"]["link_type"] == "dominance"
    assert out[0]["salience"] == 0.8


def test_salience_compromise_is_0_7():
    out = synastry.compute_hd_channel_connections({3, 60}, {3})
    assert out
    assert out[0]["raw_fact"]["link_type"] == "compromise"
    assert out[0]["salience"] == 0.7


@pytest.mark.parametrize(
    "gates_a,gates_b,link_type",
    [
        ({3}, {60}, "electromagnetic"),
        ({3, 60}, {3, 60}, "companionship"),
        ({3, 60}, set(), "dominance"),
        ({3, 60}, {3}, "compromise"),
    ],
)
def test_ease_or_tension_by_link_type(gates_a, gates_b, link_type):
    out = synastry.compute_hd_channel_connections(gates_a, gates_b)
    assert out
    assert out[0]["raw_fact"]["link_type"] == link_type
    assert out[0]["ease_or_tension"] == SPEC_LINK_EASE[link_type]


def test_dimensions_link_then_lo_center_then_hi_center_deduped():
    # electromagnetic 3-60: link themes + Sacral(3) themes + Root(60) themes.
    # intimacy_attraction recurs in the Sacral row and action_tempo recurs in
    # the Root row — first-seen dedupe keeps each exactly once.
    out = synastry.compute_hd_channel_connections({3}, {60})
    assert out
    assert out[0]["dimensions"] == [
        "intimacy_attraction",
        "conflict_repair",
        "action_tempo",
        "emotion_regulation",
    ]


@pytest.mark.parametrize(
    "gates_a,gates_b,link_type",
    [
        ({3}, {60}, "electromagnetic"),
        ({3, 60}, {3, 60}, "companionship"),
        ({3, 60}, set(), "dominance"),
        ({3, 60}, {3}, "compromise"),
    ],
)
def test_dimensions_prefix_is_spec_link_themes_for_all_four_link_types(
    gates_a, gates_b, link_type
):
    # Link-type themes lead the dimensions list for every link type; swapping
    # any type's HD_LINK_THEMES entry must fail here.
    out = synastry.compute_hd_channel_connections(gates_a, gates_b)
    assert out
    assert out[0]["raw_fact"]["link_type"] == link_type
    assert out[0]["dimensions"][:2] == SPEC_LINK_THEMES[link_type]


# ---------------------------------------------------------------------------
# Integration pin: pair 0 known-time — full expected channel_connections
# ---------------------------------------------------------------------------

EXPECTED_PAIR0_CONNECTIONS = [
    dict(
        feature_id="hd-chan-10-20-electromagnetic",
        subject="A",
        object="B",
        raw_fact={
            "channel": "10-20",
            "link_type": "electromagnetic",
            "a_gates": [20],
            "b_gates": [10],
            "centers": ["G", "Throat"],
            "full_channel_owner": None,
        },
        dimensions=[
            "intimacy_attraction",
            "conflict_repair",
            "commitment_stability",
            "autonomy_boundary",
            "communication",
            "action_tempo",
        ],
        salience=0.9,
        ease_or_tension="mixed",
        data_confidence=0.95,
    ),
    dict(
        feature_id="hd-chan-19-49-electromagnetic",
        subject="A",
        object="B",
        raw_fact={
            "channel": "19-49",
            "link_type": "electromagnetic",
            "a_gates": [19],
            "b_gates": [49],
            # Pins CURRENT engine behaviour (GATE_CENTER[19] is wrongly 情緒);
            # see .scratch/engine-synastry-e1-e5--c7bd29598e/FINDINGS-out-of-scope.md
            # (F-1) — expected to go red when that table is fixed separately.
            "centers": ["Solar Plexus", "Solar Plexus"],
            "full_channel_owner": None,
        },
        dimensions=["intimacy_attraction", "conflict_repair", "emotion_regulation"],
        salience=0.9,
        ease_or_tension="mixed",
        data_confidence=0.95,
    ),
    dict(
        feature_id="hd-chan-13-33-dominance",
        subject="A",
        object="B",
        raw_fact={
            "channel": "13-33",
            "link_type": "dominance",
            "a_gates": [13, 33],
            "b_gates": [],
            "centers": ["G", "Throat"],
            "full_channel_owner": "A",
        },
        dimensions=[
            "decision_power",
            "autonomy_boundary",
            "commitment_stability",
            "communication",
            "action_tempo",
        ],
        salience=0.8,
        ease_or_tension="tension",
        data_confidence=0.95,
    ),
    dict(
        feature_id="hd-chan-25-51-dominance",
        subject="B",
        object="A",
        raw_fact={
            "channel": "25-51",
            "link_type": "dominance",
            "a_gates": [],
            "b_gates": [25, 51],
            "centers": ["G", "Heart"],
            "full_channel_owner": "B",
        },
        dimensions=[
            "decision_power",
            "autonomy_boundary",
            "commitment_stability",
            "money_division",
        ],
        salience=0.8,
        ease_or_tension="tension",
        data_confidence=0.95,
    ),
]


def test_pair0_channel_connections_fully_pinned():
    inp_a, inp_b = _sample_pair(0)
    block = synastry.build_synastry(inp_a, inp_b)
    conns = block["human_design"]["channel_connections"]
    assert len(conns) == len(EXPECTED_PAIR0_CONNECTIONS)
    for ev, exp in zip(conns, EXPECTED_PAIR0_CONNECTIONS):
        assert ev["feature_id"] == exp["feature_id"]
        assert ev["system"] == "human_design"
        assert ev["method"] == "hd_channel_connection"
        assert ev["method_version"] == "human-design-synastry-v1"
        assert ev["method_consensus"] == "core"
        assert ev["subject"] == exp["subject"]
        assert ev["object"] == exp["object"]
        assert ev["raw_fact"] == exp["raw_fact"]
        assert ev["dimensions"] == exp["dimensions"]
        assert ev["salience"] == exp["salience"]
        assert ev["ease_or_tension"] == exp["ease_or_tension"]
        assert ev["data_confidence"] == exp["data_confidence"]
        assert ev["participates_in_convergence"] is True


@pytest.mark.parametrize("sample_i", [0, 1])
def test_channel_connections_validate_and_channel_unique(sample_i):
    inp_a, inp_b = _sample_pair(sample_i)
    block = synastry.build_synastry(inp_a, inp_b)
    conns = block["human_design"]["channel_connections"]
    assert conns, f"sample {sample_i} produced no channel connections"
    for ev in conns:
        semantics.validate_evidence(ev)
        assert ev["method_version"] == "human-design-synastry-v1"
    channels = [ev["raw_fact"]["channel"] for ev in conns]
    assert len(set(channels)) == len(channels)
    # salience desc → feature_id asc total order
    keys = [(-ev["salience"], ev["feature_id"]) for ev in conns]
    assert keys == sorted(keys)


def test_full_channel_owner_domain_and_null_for_directionless():
    inp_a, inp_b = _sample_pair(0)
    block = synastry.build_synastry(inp_a, inp_b)
    conns = block["human_design"]["channel_connections"]
    assert conns
    for ev in conns:
        owner = ev["raw_fact"]["full_channel_owner"]
        assert owner in ("A", "B", None)
        if ev["raw_fact"]["link_type"] in ("electromagnetic", "companionship"):
            assert owner is None
        else:
            assert owner in ("A", "B")
    owners_by_fid = {
        ev["feature_id"]: ev["raw_fact"]["full_channel_owner"] for ev in conns
    }
    assert owners_by_fid["hd-chan-10-20-electromagnetic"] is None
    assert owners_by_fid["hd-chan-19-49-electromagnetic"] is None
    assert owners_by_fid["hd-chan-13-33-dominance"] == "A"
    assert owners_by_fid["hd-chan-25-51-dominance"] == "B"


# ---------------------------------------------------------------------------
# center_states[]
# ---------------------------------------------------------------------------

EXPECTED_PAIR0_CENTER_STATES = [
    ("Head", "undefined", []),
    ("Ajna", "undefined", []),
    ("Throat", "a_defined", []),
    ("G", "both_defined", []),
    ("Heart", "b_defined", []),
    ("Solar Plexus", "defined_by_merge", ["19-49"]),
    ("Sacral", "undefined", []),
    ("Spleen", "undefined", []),
    ("Root", "undefined", []),
]

EXPECTED_PAIR0_CENTER_FIDS = [
    "hd-ctr-head-undefined",
    "hd-ctr-ajna-undefined",
    "hd-ctr-throat-a-defined",
    "hd-ctr-g-both-defined",
    "hd-ctr-heart-b-defined",
    "hd-ctr-solar-plexus-defined-by-merge",
    "hd-ctr-sacral-undefined",
    "hd-ctr-spleen-undefined",
    "hd-ctr-root-undefined",
]


def test_pair0_center_states_full_sequence_pinned():
    inp_a, inp_b = _sample_pair(0)
    block = synastry.build_synastry(inp_a, inp_b)
    states = block["human_design"]["center_states"]
    assert len(states) == 9
    assert [ev["raw_fact"]["center"] for ev in states] == CENTER_SEQUENCE_RAW
    for ev, (center, state, causing) in zip(states, EXPECTED_PAIR0_CENTER_STATES):
        assert ev["raw_fact"]["center"] == center
        assert ev["raw_fact"]["state"] == state
        assert ev["raw_fact"]["causing_channels"] == causing
        assert ev["raw_fact"]["state"] in STATE_VALUES
    assert [ev["feature_id"] for ev in states] == EXPECTED_PAIR0_CENTER_FIDS


def test_center_states_validate_and_fixed_fields():
    inp_a, inp_b = _sample_pair(0)
    block = synastry.build_synastry(inp_a, inp_b)
    states = block["human_design"]["center_states"]
    assert len(states) == 9
    for ev in states:
        semantics.validate_evidence(ev)
        assert ev["system"] == "human_design"
        assert ev["method"] == "hd_center_state"
        assert ev["method_version"] == "human-design-synastry-v1"
        assert ev["salience"] == 0.5
        assert ev["ease_or_tension"] == "mixed"
        assert ev["participates_in_convergence"] is False
        assert ev["subject"] is None
        assert ev["object"] is None


def test_center_state_dimensions_equal_spec_center_themes():
    inp_a, inp_b = _sample_pair(0)
    block = synastry.build_synastry(inp_a, inp_b)
    states = block["human_design"]["center_states"]
    assert states
    for ev in states:
        center_raw = ev["raw_fact"]["center"]
        assert ev["dimensions"] == SPEC_CENTER_THEMES_BY_RAW[center_raw]


def test_center_state_feature_id_shape_and_no_underscore():
    inp_a, inp_b = _sample_pair(0)
    block = synastry.build_synastry(inp_a, inp_b)
    states = block["human_design"]["center_states"]
    assert states
    for ev in states:
        fid = ev["feature_id"]
        assert fid.startswith("hd-ctr-")
        assert "_" not in fid
        assert FEATURE_ID_RE.fullmatch(fid)


def test_center_state_defined_by_merge_causing_channels_string_asc():
    # (6,59) and (19,49) both touch Solar Plexus; string order puts "19-49"
    # BEFORE "6-59" (numeric order would be the opposite).
    states = synastry.compute_hd_center_states(set(), set(), [(6, 59), (19, 49)])
    by_center = {ev["raw_fact"]["center"]: ev for ev in states}
    sp = by_center["Solar Plexus"]
    assert sp["raw_fact"]["state"] == "defined_by_merge"
    assert sp["raw_fact"]["causing_channels"] == ["19-49", "6-59"]
    sacral = by_center["Sacral"]
    assert sacral["raw_fact"]["state"] == "defined_by_merge"
    assert sacral["raw_fact"]["causing_channels"] == ["6-59"]
    assert by_center["Head"]["raw_fact"]["state"] == "undefined"
    assert by_center["Head"]["raw_fact"]["causing_channels"] == []


def test_center_state_data_confidence_both_known_and_unknown():
    inp_a, inp_b = _sample_pair(0)
    known = synastry.build_synastry(inp_a, inp_b)["human_design"]["center_states"]
    assert len(known) == 9
    assert all(ev["data_confidence"] == 0.95 for ev in known)

    b_unknown = validate_input(
        {**PERSON_B0, "time": "unknown"}, allow_unknown_time=True
    )
    unknown = synastry.build_synastry(inp_a, b_unknown)["human_design"][
        "center_states"
    ]
    assert len(unknown) == 9
    assert all(ev["data_confidence"] == 0.85 for ev in unknown)


# ---------------------------------------------------------------------------
# participants
# ---------------------------------------------------------------------------


def test_pair0_participants_fully_pinned():
    inp_a, inp_b = _sample_pair(0)
    block = synastry.build_synastry(inp_a, inp_b)
    pa = block["human_design"]["participants"]["person_a"]
    pb = block["human_design"]["participants"]["person_b"]
    assert pa == {
        "type": "投射者",
        "strategy": "等待被邀請",
        "authority": "自我投射型權威",
        "split_bridges": [],
        "hanging_gates_completed": [
            {"own_gate": 19, "partner_gate": 49, "channel": "19-49"},
            {"own_gate": 20, "partner_gate": 10, "channel": "10-20"},
        ],
    }
    assert pb == {
        "type": "投射者",
        "strategy": "等待被邀請",
        "authority": "意志力(心)權威",
        "split_bridges": [],
        "hanging_gates_completed": [
            {"own_gate": 10, "partner_gate": 20, "channel": "10-20"},
            {"own_gate": 49, "partner_gate": 19, "channel": "19-49"},
        ],
    }


def test_pair1_split_bridges_binary_definition_per_value():
    inp_a, inp_b = _sample_pair(1)
    block = synastry.build_synastry(inp_a, inp_b)
    pa = block["human_design"]["participants"]["person_a"]
    pb = block["human_design"]["participants"]["person_b"]
    # A1 is 二分人 but no merged channel bridges its two components.
    assert pa["split_bridges"] == []
    # B1 is 二分人; merged channels 10-34 and 5-15 bridge its split.
    # "10-34" < "5-15" proves string (not numeric) ascending order.
    assert pb["split_bridges"] == [
        {"channel": "10-34", "centers": ["G", "Sacral"]},
        {"channel": "5-15", "centers": ["Sacral", "G"]},
    ]


def test_split_bridges_synthetic_binary_and_single_definition():
    # Two components: {G, Throat} via 10-20 and {Sacral, Spleen} via 27-50.
    own = {10, 20, 27, 50}
    partner = {34}
    bridges = synastry.compute_split_bridges(own, partner)
    assert bridges == [
        {"channel": "10-34", "centers": ["G", "Sacral"]},
        {"channel": "20-34", "centers": ["Throat", "Sacral"]},
    ]
    # Partner holds a single gate → no own definition → no bridges.
    assert synastry.compute_split_bridges(partner, own) == []
    # Single-definition owner: same merged channels but only one component.
    assert synastry.compute_split_bridges({10, 20}, {34}) == []


def test_split_bridges_partner_only_channel_can_bridge_own_components():
    # Spec: a bridge is NOT required to have any endpoint held by the person —
    # only that own cannot complete it alone, the merge completes it, and it
    # spans two of own's components. Partner supplies both gates of 2-14
    # (G-Sacral); own holds neither, yet it bridges own's {G, Throat} (10-20)
    # and {Sacral, Spleen} (27-50) components.
    bridges = synastry.compute_split_bridges({10, 20, 27, 50}, {2, 14})
    assert bridges == [
        {"channel": "2-14", "centers": ["G", "Sacral"]},
    ]


def test_hanging_gates_completed_direction_not_swapped():
    gates_a = {62, 3}
    gates_b = {17, 60}
    hanging_a = synastry.compute_hanging_gates_completed(gates_a, gates_b)
    hanging_b = synastry.compute_hanging_gates_completed(gates_b, gates_a)
    assert hanging_a == [
        {"own_gate": 3, "partner_gate": 60, "channel": "3-60"},
        {"own_gate": 62, "partner_gate": 17, "channel": "17-62"},
    ]
    assert hanging_b == [
        {"own_gate": 17, "partner_gate": 62, "channel": "17-62"},
        {"own_gate": 60, "partner_gate": 3, "channel": "3-60"},
    ]
    assert hanging_a != hanging_b


def test_hanging_gates_secondary_key_channel_asc_within_same_own_gate():
    # Gate 34 belongs to three channels; two of them completed by partner.
    assert synastry.compute_hanging_gates_completed({34}, {10, 20}) == [
        {"own_gate": 34, "partner_gate": 10, "channel": "10-34"},
        {"own_gate": 34, "partner_gate": 20, "channel": "20-34"},
    ]
    # Same proof via gate 10 (partner completes 10-34 and 10-57).
    assert synastry.compute_hanging_gates_completed({10}, {34, 57}) == [
        {"own_gate": 10, "partner_gate": 34, "channel": "10-34"},
        {"own_gate": 10, "partner_gate": 57, "channel": "10-57"},
    ]


def test_hanging_gates_secondary_key_discriminates_beyond_own_gate():
    # Gate 10 belongs to three channels and partner completes all three;
    # CHANNELS iteration order differs from channel string order here, so a
    # sort keyed on own_gate alone cannot produce this order.
    assert synastry.compute_hanging_gates_completed({10}, {20, 34, 57}) == [
        {"own_gate": 10, "partner_gate": 20, "channel": "10-20"},
        {"own_gate": 10, "partner_gate": 34, "channel": "10-34"},
        {"own_gate": 10, "partner_gate": 57, "channel": "10-57"},
    ]


def test_hanging_gate_excluded_when_own_holds_both_channel_ends():
    # 10-20 is already complete in own gates, so even though partner also
    # holds 20, gate 10 is not hanging (spec: 自己持有一端、自己另一端未持有).
    assert synastry.compute_hanging_gates_completed({10, 20}, {20, 34}) == [
        {"own_gate": 10, "partner_gate": 34, "channel": "10-34"},
        {"own_gate": 20, "partner_gate": 34, "channel": "20-34"},
    ]
    # Symmetric direction: partner holds the LOW end (10) of the own-complete
    # channel 10-20, so gate 20 is not hanging there either.
    assert synastry.compute_hanging_gates_completed({10, 20}, {10, 34}) == [
        {"own_gate": 10, "partner_gate": 34, "channel": "10-34"},
        {"own_gate": 20, "partner_gate": 34, "channel": "20-34"},
    ]


def test_strategy_table_matches_spec_for_five_types():
    assert semantics.STRATEGY_BY_TYPE == SPEC_STRATEGY_BY_TYPE


_TYPE_COVERAGE = [
    ("1962-08-05", "16:40", "顯示者", "告知後行動"),
    ("1985-12-01", "03:15", "生產者", "等待回應"),
    ("2000-01-01", "12:00", "顯示生產者", "等待回應後告知"),
    ("1990-06-15", "08:30", "投射者", "等待被邀請"),
    ("2011-11-19", "6:45", "反映者", "等待一個完整月亮週期"),
]


@pytest.mark.parametrize(
    "date,time,expected_type,expected_strategy", _TYPE_COVERAGE
)
def test_participant_strategy_covers_all_five_types(
    date, time, expected_type, expected_strategy
):
    inp_a = validate_input(
        {
            "name": "P",
            "gender": "女",
            "date": date,
            "time": time,
            "tz": 8,
            "lat": 25.033,
            "lon": 121.5654,
        }
    )
    inp_b = validate_input(PERSON_B0)
    block = synastry.build_synastry(inp_a, inp_b)
    pa = block["human_design"]["participants"]["person_a"]
    assert pa["type"] == expected_type
    assert pa["strategy"] == expected_strategy
    assert pa["strategy"] == semantics.STRATEGY_BY_TYPE[pa["type"]]
    assert pa["authority"] in SPEC_AUTHORITIES
    assert isinstance(pa["split_bridges"], list)
    assert isinstance(pa["hanging_gates_completed"], list)


# ---------------------------------------------------------------------------
# Time-unknown behaviour
# ---------------------------------------------------------------------------


def test_time_unknown_participants_still_emitted_from_noon_chart():
    inp_a = validate_input(PERSON_A0)
    b_unknown = validate_input(
        {**PERSON_B0, "time": "unknown"}, allow_unknown_time=True
    )
    b_noon = validate_input({**PERSON_B0, "time": "12:00"})

    out_unknown = synastry.build_synastry_json(inp_a, b_unknown)
    out_noon = synastry.build_synastry_json(inp_a, b_noon)

    assert "hd_lines" in out_unknown["synastry"]["unavailable"]

    hd_u = out_unknown["synastry"]["human_design"]
    hd_n = out_noon["synastry"]["human_design"]

    for person in ("person_a", "person_b"):
        p_u = hd_u["participants"][person]
        assert p_u["type"]
        assert p_u["strategy"]
        assert p_u["authority"]
        assert isinstance(p_u["split_bridges"], list)
        assert isinstance(p_u["hanging_gates_completed"], list)
        # Content computed from the unknown side's local 12:00 estimate.
        assert p_u == hd_n["participants"][person]

    # Channel wiring identical to the noon run; confidence degraded.
    conns_u = hd_u["channel_connections"]
    conns_n = hd_n["channel_connections"]
    assert conns_u
    assert [ev["feature_id"] for ev in conns_u] == [
        ev["feature_id"] for ev in conns_n
    ]
    for ev_u, ev_n in zip(conns_u, conns_n):
        assert ev_u["raw_fact"] == ev_n["raw_fact"]
        assert ev_u["salience"] == ev_n["salience"]
        assert ev_u["dimensions"] == ev_n["dimensions"]
    confs = {ev["data_confidence"] for ev in conns_u}
    assert confs <= {0.6, 0.85}
    assert 0.95 not in confs


def test_time_unknown_channel_confidence_exhaustive_split_pinned():
    inp_a = validate_input(PERSON_A0)
    b_unknown = validate_input(
        {**PERSON_B0, "time": "unknown"}, allow_unknown_time=True
    )
    conns = synastry.build_synastry(inp_a, b_unknown)["human_design"][
        "channel_connections"
    ]
    # B's noon fast-planet gates are {2,3,10,13,43,54,55,60}; a connection is
    # 0.6 iff one of its endpoints is in that set, else 0.85.
    expected = {
        "hd-chan-3-60-dominance": 0.6,
        "hd-chan-10-20-electromagnetic": 0.6,
        "hd-chan-13-33-compromise": 0.6,
        "hd-chan-25-51-dominance": 0.85,
    }
    assert {ev["feature_id"] for ev in conns} == set(expected)
    for ev in conns:
        assert ev["data_confidence"] == expected[ev["feature_id"]]


# ---------------------------------------------------------------------------
# data_confidence exhaustive split — unit level
# ---------------------------------------------------------------------------


def test_confidence_unknown_side_moon_activates_endpoint_is_0_6():
    out = synastry.compute_hd_channel_connections(
        {5, 15},
        set(),
        time_unknown_a=True,
        fast_gates_a={5, 15},
    )
    assert out
    assert out[0]["data_confidence"] == 0.6


def test_confidence_unknown_side_saturn_only_is_0_85():
    rows = [("♄", 5, 1, 15, 2)]
    assert synastry.hd_fast_gates(rows) == set()
    out = synastry.compute_hd_channel_connections(
        synastry.hd_active_gates(rows),
        set(),
        time_unknown_a=True,
        fast_gates_a=synastry.hd_fast_gates(rows),
    )
    assert out
    assert out[0]["raw_fact"]["link_type"] == "dominance"
    assert out[0]["data_confidence"] == 0.85


def test_confidence_unknown_side_jupiter_only_is_0_85():
    rows = [("♃", 5, 1, 15, 2)]
    assert synastry.hd_fast_gates(rows) == set()
    out = synastry.compute_hd_channel_connections(
        synastry.hd_active_gates(rows),
        set(),
        time_unknown_a=True,
        fast_gates_a=synastry.hd_fast_gates(rows),
    )
    assert out
    assert out[0]["data_confidence"] == 0.85


def test_confidence_only_b_unknown_with_a_moon_activation_is_0_85():
    out = synastry.compute_hd_channel_connections(
        {5, 15},
        set(),
        time_unknown_a=False,
        time_unknown_b=True,
        fast_gates_a={5, 15},  # A-side Moon — A is known, must NOT degrade
        fast_gates_b=set(),
    )
    assert out
    assert out[0]["data_confidence"] == 0.85


def test_confidence_only_a_unknown_with_b_moon_activation_is_0_85():
    out = synastry.compute_hd_channel_connections(
        {5, 15},
        set(),
        time_unknown_a=True,
        time_unknown_b=False,
        fast_gates_a=set(),
        fast_gates_b={5, 15},  # B-side Moon — B is known, must NOT degrade
    )
    assert out
    assert out[0]["data_confidence"] == 0.85


# ---------------------------------------------------------------------------
# Guards: forbidden keys, no incarnation pairing, feature_id uniqueness
# ---------------------------------------------------------------------------


def test_forbidden_keys_absent_in_hd_block():
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    keys = _all_keys(payload["synastry"]["human_design"])
    assert keys
    for k in keys:
        kl = k.lower() if isinstance(k, str) else str(k)
        for bad in FORBIDDEN_KEY_SUBSTR:
            if bad == "吉凶":
                assert bad not in str(k)
            else:
                assert bad not in kl


def test_no_incarnation_cross_pairing_emitted():
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    hd = payload["synastry"]["human_design"]
    assert set(hd.keys()) == {"channel_connections", "center_states", "participants"}
    for person in ("person_a", "person_b"):
        assert set(hd["participants"][person].keys()) == {
            "type",
            "strategy",
            "authority",
            "split_bridges",
            "hanging_gates_completed",
        }
    blob = json.dumps(hd, ensure_ascii=False).lower()
    for token in ("incarnation", "cross", "輪迴"):
        assert token not in blob


def test_feature_ids_unique_and_hd_present_in_full_payload():
    inp_a, inp_b = _sample_pair(0)
    payload = synastry.build_synastry_json(inp_a, inp_b)
    fids = _collect_feature_ids(payload)
    assert fids
    assert any(fid.startswith("hd-chan-") for fid in fids)
    assert any(fid.startswith("hd-ctr-") for fid in fids)
    assert len(fids) == len(set(fids))
    for fid in fids:
        assert FEATURE_ID_RE.fullmatch(fid)


def test_hd_block_byte_identical_across_two_runs():
    inp_a, inp_b = _sample_pair(1)
    one = json.dumps(
        synastry.build_synastry_json(inp_a, inp_b)["synastry"]["human_design"],
        ensure_ascii=False,
        sort_keys=False,
    )
    two = json.dumps(
        synastry.build_synastry_json(inp_a, inp_b)["synastry"]["human_design"],
        ensure_ascii=False,
        sort_keys=False,
    )
    assert one == two
