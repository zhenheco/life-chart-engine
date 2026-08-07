"""Synastry (relationship) computation entry points.

E1 delivered the key-complete skeleton. E2 fills ``western.aspects[]``.
E3/E4 fill house overlay, angle contacts, and Human Design.
"""

from __future__ import annotations

from typing import Any, Mapping

if __package__:
    from . import semantics
else:
    import semantics

SCHEMA_VERSION = "1.2"

ZIWEI_METHODOLOGY_NOTE = (
    "紫微斗數沒有本引擎採用的合盤方法；兩人盤各自獨立計算，不做關係層級推論。"
)

# Fixed 11-body set for aspects[] (South Node excluded; no angles; no Chiron).
ASPECT_BODIES: tuple[str, ...] = (
    "太陽",
    "月亮",
    "水星",
    "金星",
    "火星",
    "木星",
    "土星",
    "天王星",
    "海王星",
    "冥王星",
    "北交點",
)


def _import_western():
    """Load ``western`` without creating a package-level cycle with chart_engine."""
    if __package__:
        from .chart_engine import western
    else:
        from chart_engine import western
    return western


def compute_western_aspects(
    pos_a: Mapping[str, float],
    pos_b: Mapping[str, float],
    *,
    time_unknown_a: bool = False,
    time_unknown_b: bool = False,
) -> list[dict[str, Any]]:
    """Pair A×B longitudes into ``synastry_aspect`` evidence, sorted.

    Does **not** reuse chart_engine.aspects() (in-chart orbs / angle points).
    """
    out: list[dict[str, Any]] = []
    for body_a in ASPECT_BODIES:
        lon_a = pos_a[body_a]
        for body_b in ASPECT_BODIES:
            # Both outer planets → skip entirely
            if body_a in semantics.OUTER_PLANETS and body_b in semantics.OUTER_PLANETS:
                continue
            lon_b = pos_b[body_b]
            actual = semantics.shortest_arc(lon_a, lon_b)
            for aspect_slug, meta in semantics.ASPECT_BY_SLUG.items():
                exact = float(meta["exact_angle"])
                orb = abs(actual - exact)
                max_orb = semantics.resolve_max_orb(body_a, body_b, aspect_slug)
                if orb > max_orb:
                    continue
                out.append(
                    semantics.evidence(
                        method="synastry_aspect",
                        planet_a=body_a,
                        planet_b=body_b,
                        aspect=aspect_slug,
                        actual_angle=actual,
                        orb=orb,
                        time_unknown_a=time_unknown_a,
                        time_unknown_b=time_unknown_b,
                    )
                )
    # salience desc → feature_id asc
    out.sort(key=lambda e: (-e["salience"], e["feature_id"]))
    return out


def build_synastry(inp_a, inp_b):
    """Return the synastry block; E2 fills ``western.aspects``."""
    western = _import_western()
    _jd_a, pos_a, _retro_a, _cusps_a, _asc_a, _mc_a, _house_of_a = western(inp_a)
    _jd_b, pos_b, _retro_b, _cusps_b, _asc_b, _mc_b, _house_of_b = western(inp_b)

    time_unknown_a = bool(inp_a.get("time_unknown"))
    time_unknown_b = bool(inp_b.get("time_unknown"))

    aspects = compute_western_aspects(
        pos_a,
        pos_b,
        time_unknown_a=time_unknown_a,
        time_unknown_b=time_unknown_b,
    )

    return {
        "western": {
            "aspects": aspects,
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
    """Full dual-person JSON envelope (same shape as planned HTTP POST /synastry).

    Does not call the Zi Wei Node sidecar — no per-request Node dependency.
    """
    syn = build_synastry(inp_a, inp_b)
    aspects = syn["western"]["aspects"]
    unavailable = syn["unavailable"]
    if aspects and not unavailable:
        completeness = "full"
    else:
        completeness = "partial"
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
        "synastry": syn,
        "evidence_completeness": completeness,
    }
