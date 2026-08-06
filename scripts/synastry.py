"""Synastry (relationship) computation entry points.

E1 delivers a key-complete skeleton with empty evidence arrays. Later slices
fill western aspects (E2), house overlay / angle contacts (E3), and HD (E4).
"""

from __future__ import annotations

SCHEMA_VERSION = "1.2"

ZIWEI_METHODOLOGY_NOTE = (
    "紫微斗數沒有本引擎採用的合盤方法；兩人盤各自獨立計算，不做關係層級推論。"
)


def build_synastry(inp_a, inp_b):
    """Return the synastry block with all keys present and empty evidence arrays."""
    return {
        "western": {
            "aspects": [],
            "a_planets_in_b_houses": [],
            "b_planets_in_a_houses": [],
            "angle_contacts_a_to_b": [],
            "angle_contacts_b_to_a": [],
        },
        "human_design": {
            "channel_connections": [],
            "center_states": [],
            "participants": {
                "person_a": {},
                "person_b": {},
            },
        },
        "unavailable": [],
    }


def build_synastry_json(inp_a, inp_b):
    """Full dual-person JSON envelope (same shape as planned HTTP POST /synastry, E5).

    Does not call the Zi Wei Node sidecar — no per-request Node dependency.
    Empty aspects → evidence_completeness is always \"partial\" for this skeleton.
    """
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "western": {"person_a": {}, "person_b": {}},
        "human_design": {"person_a": {}, "person_b": {}},
        "ziwei": {
            "person_a": {},
            "person_b": {},
            "status": "not_computed",
            "methodology_note": ZIWEI_METHODOLOGY_NOTE,
        },
        "synastry": build_synastry(inp_a, inp_b),
        "evidence_completeness": "partial",
    }
