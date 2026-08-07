"""Synastry (relationship) computation entry points.

E1 delivered the key-complete skeleton. E2 fills ``western.aspects[]``.
E3 fills house overlay, angle contacts, and time-unknown ``unavailable``.
E4 fills Human Design.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

if __package__:
    from . import semantics
else:
    import semantics

SCHEMA_VERSION = "1.2"

ZIWEI_METHODOLOGY_NOTE = (
    "紫微斗數沒有本引擎採用的合盤方法；兩人盤各自獨立計算，不做關係層級推論。"
)

# Fixed 11-body set for aspects[] / overlay / angle contacts
# (South Node excluded; no angles; no Chiron).
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

# Time-dependent tokens; order is fixed by the array-sort contract.
UNAVAILABLE_TIME_UNKNOWN: tuple[str, ...] = (
    "house_overlay",
    "angle_contacts",
    "hd_lines",
)


def _import_western():
    """Load ``western`` without creating a package-level cycle with chart_engine."""
    if __package__:
        from .chart_engine import western
    else:
        from chart_engine import western
    return western


def _sort_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda e: (-e["salience"], e["feature_id"]))


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
    return _sort_evidence(out)


def compute_house_overlay(
    visitor_pos: Mapping[str, float],
    owner_house_of: Callable[[float], int],
    *,
    visitor: str,
    owner: str,
) -> list[dict[str, Any]]:
    """Place visitor's 11 bodies into the owner's Placidus houses."""
    out: list[dict[str, Any]] = []
    for body in ASPECT_BODIES:
        lon = visitor_pos[body]
        house = int(owner_house_of(lon))
        out.append(
            semantics.evidence_house_overlay(
                planet=body,
                house_number=house,
                visitor=visitor,
                owner=owner,
            )
        )
    return _sort_evidence(out)


def angle_longitudes(asc: float, mc: float) -> dict[str, float]:
    """Four angle points from ASC / MC (DESC = ASC+180, IC = MC+180)."""
    return {
        "上升": float(asc) % 360.0,
        "下降": (float(asc) + 180.0) % 360.0,
        "天頂": float(mc) % 360.0,
        "天底": (float(mc) + 180.0) % 360.0,
    }


def compute_angle_contacts(
    planet_pos: Mapping[str, float],
    angles: Mapping[str, float],
    *,
    subject: str,
    obj: str,
) -> list[dict[str, Any]]:
    """Subject's 11 planets against object's four angle points.

    Angle–angle pairs are never considered (planets only on the subject side).
    ``obj`` is the object chart label (``"A"`` / ``"B"``); evidence key stays ``"object"``.
    """
    out: list[dict[str, Any]] = []
    for body in ASPECT_BODIES:
        lon_p = planet_pos[body]
        for angle_name in semantics.ANGLE_INTERNAL_ORDER:
            lon_a = angles[angle_name]
            actual = semantics.shortest_arc(lon_p, lon_a)
            for aspect_slug, meta in semantics.ASPECT_BY_SLUG.items():
                exact = float(meta["exact_angle"])
                orb = abs(actual - exact)
                max_orb = semantics.resolve_max_orb(body, angle_name, aspect_slug)
                if orb > max_orb:
                    continue
                out.append(
                    semantics.evidence_angle_contact(
                        planet=body,
                        angle=angle_name,
                        aspect=aspect_slug,
                        actual_angle=actual,
                        orb=orb,
                        subject=subject,
                        obj=obj,
                    )
                )
    return _sort_evidence(out)


def build_synastry(inp_a, inp_b):
    """Return the synastry block; E2 aspects + E3 overlay / angle contacts."""
    western = _import_western()
    _jd_a, pos_a, _retro_a, _cusps_a, asc_a, mc_a, house_of_a = western(inp_a)
    _jd_b, pos_b, _retro_b, _cusps_b, asc_b, mc_b, house_of_b = western(inp_b)

    time_unknown_a = bool(inp_a.get("time_unknown"))
    time_unknown_b = bool(inp_b.get("time_unknown"))
    time_unknown_any = time_unknown_a or time_unknown_b

    aspects = compute_western_aspects(
        pos_a,
        pos_b,
        time_unknown_a=time_unknown_a,
        time_unknown_b=time_unknown_b,
    )

    if time_unknown_any:
        a_in_b: list[dict[str, Any]] = []
        b_in_a: list[dict[str, Any]] = []
        ang_a_to_b: list[dict[str, Any]] = []
        ang_b_to_a: list[dict[str, Any]] = []
        unavailable: list[str] = list(UNAVAILABLE_TIME_UNKNOWN)
    else:
        a_in_b = compute_house_overlay(
            pos_a, house_of_b, visitor="A", owner="B"
        )
        b_in_a = compute_house_overlay(
            pos_b, house_of_a, visitor="B", owner="A"
        )
        angles_a = angle_longitudes(asc_a, mc_a)
        angles_b = angle_longitudes(asc_b, mc_b)
        ang_a_to_b = compute_angle_contacts(
            pos_a, angles_b, subject="A", obj="B"
        )
        ang_b_to_a = compute_angle_contacts(
            pos_b, angles_a, subject="B", obj="A"
        )
        unavailable = []

    return {
        "western": {
            "aspects": aspects,
            "a_planets_in_b_houses": a_in_b,
            "b_planets_in_a_houses": b_in_a,
            "angle_contacts_a_to_b": ang_a_to_b,
            "angle_contacts_b_to_a": ang_b_to_a,
        },
        "human_design": {
            "channel_connections": [],
            "center_states": [],
            "participants": {
                "person_a": {},
                "person_b": {},
            },
        },
        "unavailable": unavailable,
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
