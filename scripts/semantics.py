"""Synastry semantics-v1: themes, slugs, orb rules, evidence shape, validation.

Rule body for E2+ (western aspects, house overlay, angle contacts, HD).
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

METHOD_VERSION_WESTERN = "western-synastry-v1"
METHOD_VERSION_HD = "human-design-synastry-v1"

THEMES_V1: list[str] = [
    "communication",
    "emotion_regulation",
    "decision_power",
    "action_tempo",
    "intimacy_attraction",
    "autonomy_boundary",
    "commitment_stability",
    "money_division",
    "conflict_repair",
    "timing_context",
]

# Human Design type → strategy (Chinese display strings; E4 consumes this).
STRATEGY_BY_TYPE: dict[str, str] = {
    "顯示者": "告知後行動",
    "生產者": "等待回應",
    "顯示生產者": "等待回應後告知",
    "投射者": "等待被邀請",
    "反映者": "等待一個完整月亮週期",
}

# Internal Chinese name → (raw_fact English, feature_id slug)
_BODY_ROWS: list[tuple[str, str, str]] = [
    ("太陽", "Sun", "sun"),
    ("月亮", "Moon", "moon"),
    ("水星", "Mercury", "mercury"),
    ("金星", "Venus", "venus"),
    ("火星", "Mars", "mars"),
    ("木星", "Jupiter", "jupiter"),
    ("土星", "Saturn", "saturn"),
    ("天王星", "Uranus", "uranus"),
    ("海王星", "Neptune", "neptune"),
    ("冥王星", "Pluto", "pluto"),
    ("北交點", "North Node", "north-node"),
    ("上升", "Ascendant", "asc"),
    ("下降", "Descendant", "desc"),
    ("天頂", "Midheaven", "mc"),
    ("天底", "Imum Coeli", "ic"),
]

_ASPECT_ROWS: list[tuple[str, str, str, int, float, str]] = [
    # internal, raw_fact, slug, exact_angle, base_orb, ease_or_tension
    ("合相", "conjunction", "conjunction", 0, 6.0, "mixed"),
    ("六合", "sextile", "sextile", 60, 3.0, "ease"),
    ("四分", "square", "square", 90, 5.0, "tension"),
    ("三分", "trine", "trine", 120, 5.0, "ease"),
    ("對分", "opposition", "opposition", 180, 6.0, "tension"),
]

SLUGS: dict[str, dict[str, str]] = {
    "internal_to_raw": {row[0]: row[1] for row in _BODY_ROWS},
    "internal_to_slug": {row[0]: row[2] for row in _BODY_ROWS},
    "raw_to_internal": {row[1]: row[0] for row in _BODY_ROWS},
    "slug_to_internal": {row[2]: row[0] for row in _BODY_ROWS},
    "aspect_to_raw": {row[0]: row[1] for row in _ASPECT_ROWS},
    "aspect_to_slug": {row[0]: row[2] for row in _ASPECT_ROWS},
    "aspect_slug_to_internal": {row[2]: row[0] for row in _ASPECT_ROWS},
}

# Also index aspects by English slug for resolve_max_orb / evidence
ASPECT_BY_SLUG: dict[str, dict[str, Any]] = {
    row[2]: {
        "internal": row[0],
        "raw": row[1],
        "slug": row[2],
        "exact_angle": row[3],
        "base_orb": row[4],
        "ease_or_tension": row[5],
    }
    for row in _ASPECT_ROWS
}

PLANET_WEIGHT: dict[str, float] = {
    "太陽": 1.0,
    "月亮": 1.0,
    "水星": 0.9,
    "金星": 0.9,
    "火星": 0.9,
    "木星": 0.8,
    "土星": 0.8,
    "天王星": 0.6,
    "海王星": 0.6,
    "冥王星": 0.6,
    "北交點": 0.5,
    "上升": 0.5,
    "下降": 0.5,
    "天頂": 0.5,
    "天底": 0.5,
}

OUTER_PLANETS = frozenset({"天王星", "海王星", "冥王星"})
LUMINARIES = frozenset({"太陽", "月亮"})
ANGLE_BODIES = frozenset({"上升", "下降", "天頂", "天底"})
NORTH_NODE = "北交點"

PLANET_THEMES: dict[str, list[str]] = {
    "太陽": ["decision_power", "commitment_stability"],
    "月亮": ["emotion_regulation", "intimacy_attraction"],
    "水星": ["communication"],
    "金星": ["intimacy_attraction", "money_division"],
    "火星": ["action_tempo", "conflict_repair"],
    "木星": ["money_division", "commitment_stability"],
    "土星": ["commitment_stability", "autonomy_boundary"],
    "天王星": ["autonomy_boundary"],
    "海王星": ["emotion_regulation"],
    "冥王星": ["decision_power", "conflict_repair"],
    "北交點": ["timing_context"],
    "上升": ["timing_context", "autonomy_boundary"],
    "下降": ["timing_context", "autonomy_boundary"],
    "天頂": ["timing_context", "autonomy_boundary"],
    "天底": ["timing_context", "autonomy_boundary"],
}

# Human Design centers. Row order IS the center_states[] output order
# (頭→邏輯→喉→G→意志→情緒→薦骨→脾→根). (internal, raw_fact, slug, themes)
HD_CENTER_ROWS: list[tuple[str, str, str, list[str]]] = [
    ("頭", "Head", "head", ["communication", "decision_power"]),
    ("邏輯", "Ajna", "ajna", ["communication", "decision_power"]),
    ("喉", "Throat", "throat", ["communication", "action_tempo"]),
    ("G", "G", "g", ["commitment_stability", "autonomy_boundary"]),
    ("意志", "Heart", "heart", ["money_division", "decision_power"]),
    ("情緒", "Solar Plexus", "solar-plexus", ["emotion_regulation", "conflict_repair"]),
    ("薦骨", "Sacral", "sacral", ["action_tempo", "intimacy_attraction"]),
    ("脾", "Spleen", "spleen", ["timing_context", "autonomy_boundary"]),
    ("根", "Root", "root", ["action_tempo", "emotion_regulation"]),
]

HD_CENTER_ORDER: tuple[str, ...] = tuple(row[0] for row in HD_CENTER_ROWS)
HD_CENTER_RAW: dict[str, str] = {row[0]: row[1] for row in HD_CENTER_ROWS}
HD_CENTER_SLUG: dict[str, str] = {row[0]: row[2] for row in HD_CENTER_ROWS}
HD_CENTER_THEMES: dict[str, list[str]] = {row[0]: list(row[3]) for row in HD_CENTER_ROWS}

# Link type → themes / salience / ease_or_tension (spec §人類圖連結判定).
HD_LINK_THEMES: dict[str, list[str]] = {
    "electromagnetic": ["intimacy_attraction", "conflict_repair"],
    "dominance": ["decision_power", "autonomy_boundary"],
    "compromise": ["autonomy_boundary", "conflict_repair"],
    "companionship": ["commitment_stability", "action_tempo"],
}

HD_LINK_SALIENCE: dict[str, float] = {
    "electromagnetic": 0.9,
    "companionship": 0.9,
    "dominance": 0.8,
    "compromise": 0.7,
}

HD_LINK_EASE: dict[str, str] = {
    "companionship": "ease",
    "electromagnetic": "mixed",
    "dominance": "tension",
    "compromise": "tension",
}

HD_STATE_SLUG: dict[str, str] = {
    "a_defined": "a-defined",
    "b_defined": "b-defined",
    "both_defined": "both-defined",
    "defined_by_merge": "defined-by-merge",
    "undefined": "undefined",
}

# Center states rank below every channel connection.
HD_CENTER_STATE_SALIENCE = 0.5
# Channel/center confidence when any side's birth time is unknown.
DATA_CONFIDENCE_HD_UNKNOWN = 0.85
DATA_CONFIDENCE_HD_UNKNOWN_FAST = 0.6

REQUIRED_EVIDENCE_KEYS: tuple[str, ...] = (
    "feature_id",
    "system",
    "method",
    "method_version",
    "subject",
    "object",
    "raw_fact",
    "dimensions",
    "salience",
    "ease_or_tension",
    "method_consensus",
    "data_confidence",
    "participates_in_convergence",
)

# Keys that must never appear anywhere on an Evidence object — scanned at the
# top level and recursively inside raw_fact (spec §evidence schema).
FORBIDDEN_EVIDENCE_KEYS: frozenset[str] = frozenset(
    {
        "interpretive_valence",
        "score",
        "compatibility",
        "percentage",
        "rating",
        "total",
        "grade",
        "吉凶",
    }
)

METHOD_VERSION_BY_METHOD: dict[str, str] = {
    "synastry_aspect": METHOD_VERSION_WESTERN,
    "house_overlay": METHOD_VERSION_WESTERN,
    "angle_contact": METHOD_VERSION_WESTERN,
    "hd_channel_connection": METHOD_VERSION_HD,
    "hd_center_state": METHOD_VERSION_HD,
}

_SYSTEM_DOMAIN = frozenset({"western", "human_design"})
# Spec lists core|named_school|experimental but the latter two are out of scope;
# only "core" is accepted in this engine.
_METHOD_CONSENSUS_DOMAIN = frozenset({"core"})
_FEATURE_ID_RE = re.compile(r"^[a-z]+-[a-z0-9-]+$")
_EASE_DOMAIN = frozenset({"ease", "tension", "mixed"})
_THEMES_SET = frozenset(THEMES_V1)


def shortest_arc(lon_a: float, lon_b: float) -> float:
    """Shortest angular distance on the circle in degrees ∈ [0, 180]."""
    d = abs(float(lon_a) - float(lon_b)) % 360.0
    return min(d, 360.0 - d)


def orb_weight(orb: float, max_orb: float) -> float:
    """``max(0, 1 - (actual_orb / max_orb)²)``."""
    if max_orb <= 0:
        return 0.0
    return max(0.0, 1.0 - (float(orb) / float(max_orb)) ** 2)


def _is_angle(body: str) -> bool:
    return body in ANGLE_BODIES


def _is_node(body: str) -> bool:
    return body == NORTH_NODE


def resolve_max_orb(a: str, b: str, aspect: str) -> float:
    """Orb allowance for bodies ``a``/``b`` and aspect slug (e.g. ``square``).

    Order:
    1. Either end angle or North Node → special orb; no luminary +1°.
       Both special → take the smaller.
    2. Else aspect base orb; luminary either end → +1°; hard cap 7°.
    """
    specials: list[float] = []
    for body in (a, b):
        if _is_node(body):
            specials.append(2.0)
        elif _is_angle(body):
            other = b if body == a else a
            # Sun/Moon to angle → 4°; otherwise angle 3°
            specials.append(4.0 if other in LUMINARIES else 3.0)

    if specials:
        return min(specials)

    meta = ASPECT_BY_SLUG[aspect]
    base = float(meta["base_orb"])
    if a in LUMINARIES or b in LUMINARIES:
        base = min(base + 1.0, 7.0)
    return base


def planet_weight_for_aspect(a: str, b: str) -> float:
    """Cross-aspect planet_weight.

    North Node or any angle point on either end → fixed 0.5 (not max with partner).
    Otherwise max(w_a, w_b).
    """
    if _is_node(a) or _is_node(b) or _is_angle(a) or _is_angle(b):
        return 0.5
    return max(PLANET_WEIGHT[a], PLANET_WEIGHT[b])


def dimensions_for_aspect(planet_a: str, planet_b: str) -> list[str]:
    """A-side themes (row order) then B-side; first-seen dedupe."""
    out: list[str] = []
    seen: set[str] = set()
    for theme in PLANET_THEMES[planet_a] + PLANET_THEMES[planet_b]:
        if theme not in seen:
            seen.add(theme)
            out.append(theme)
    return out


def raw_fact_to_internal(raw_name: str) -> str:
    return SLUGS["raw_to_internal"][raw_name]


def feature_id(method: str, **parts: str) -> str:
    """Build a feature_id from method + slug parts. Never contains underscores."""
    if method == "synastry_aspect":
        return (
            f"w-syn-a-{parts['planet_a']}-{parts['aspect']}-b-{parts['planet_b']}"
        )
    if method == "house_overlay":
        return (
            f"w-ovl-{parts['visitor']}-{parts['planet']}-in-"
            f"{parts['owner']}-h{parts['house_number']}"
        )
    if method == "angle_contact":
        return (
            f"w-ang-{parts['subject']}-{parts['planet']}-{parts['aspect']}-"
            f"{parts['object']}-{parts['angle']}"
        )
    if method == "hd_channel_connection":
        return f"hd-chan-{parts['lo']}-{parts['hi']}-{parts['link_type']}"
    if method == "hd_center_state":
        return f"hd-ctr-{parts['center_slug']}-{parts['state_slug']}"
    raise ValueError(f"unknown method for feature_id: {method!r}")


# Both birth times known (western overlay / angle contact / both-known aspects).
DATA_CONFIDENCE_BOTH_KNOWN = 0.95


def data_confidence_western(
    *,
    planet_a: str,
    planet_b: str,
    time_unknown_a: bool,
    time_unknown_b: bool,
) -> float:
    """Western synastry_aspect confidence (not HD channel rules)."""
    if not time_unknown_a and not time_unknown_b:
        return DATA_CONFIDENCE_BOTH_KNOWN
    # Unknown-side Moon participation → 0.6
    if time_unknown_a and planet_a == "月亮":
        return 0.6
    if time_unknown_b and planet_b == "月亮":
        return 0.6
    return 0.85


# House-overlay salience scale (planet_weight × this factor).
HOUSE_OVERLAY_WEIGHT = 0.8
# Angle-contact planet_weight is fixed (not max with the angle body).
ANGLE_CONTACT_PLANET_WEIGHT = 0.5

ANGLE_INTERNAL_ORDER: tuple[str, ...] = ("上升", "下降", "天頂", "天底")


def dimensions_for_planet(planet: str) -> list[str]:
    """Themes for a single planet (house overlay)."""
    return list(PLANET_THEMES[planet])


def dimensions_for_angle_contact(planet: str, angle: str) -> list[str]:
    """Planet themes then angle themes; first-seen dedupe."""
    out: list[str] = []
    seen: set[str] = set()
    for theme in PLANET_THEMES[planet] + PLANET_THEMES[angle]:
        if theme not in seen:
            seen.add(theme)
            out.append(theme)
    return out


def dimensions_for_hd_channel(
    link_type: str, center_lo: str, center_hi: str
) -> list[str]:
    """Link-type themes → lo gate's center themes → hi gate's center themes.

    First-seen dedupe. Centers are internal Chinese names.
    """
    out: list[str] = []
    seen: set[str] = set()
    themes = (
        HD_LINK_THEMES[link_type]
        + HD_CENTER_THEMES[center_lo]
        + HD_CENTER_THEMES[center_hi]
    )
    for theme in themes:
        if theme not in seen:
            seen.add(theme)
            out.append(theme)
    return out


def data_confidence_hd_channel(
    *,
    channel_gates: Sequence[int],
    fast_gates_a: Any,
    fast_gates_b: Any,
    time_unknown_a: bool,
    time_unknown_b: bool,
) -> float:
    """Exhaustive split for HD channels (spec §時間未知與 data_confidence).

    Unknown side's Moon/Mercury/Venus/Mars activating either endpoint → 0.6;
    otherwise 0.85 when any side is unknown; 0.95 when both known.
    """
    if not time_unknown_a and not time_unknown_b:
        return DATA_CONFIDENCE_BOTH_KNOWN
    gates = set(channel_gates)
    if time_unknown_a and gates & set(fast_gates_a):
        return DATA_CONFIDENCE_HD_UNKNOWN_FAST
    if time_unknown_b and gates & set(fast_gates_b):
        return DATA_CONFIDENCE_HD_UNKNOWN_FAST
    return DATA_CONFIDENCE_HD_UNKNOWN


def evidence(
    *,
    method: str,
    planet_a: str,
    planet_b: str,
    aspect: str,
    actual_angle: float,
    orb: float,
    time_unknown_a: bool = False,
    time_unknown_b: bool = False,
) -> dict[str, Any]:
    """Build one ``synastry_aspect`` evidence object from internal planet names."""
    if method != "synastry_aspect":
        raise ValueError(f"evidence() only builds synastry_aspect in E2; got {method!r}")
    meta = ASPECT_BY_SLUG[aspect]
    max_orb = resolve_max_orb(planet_a, planet_b, aspect)
    ow = orb_weight(orb, max_orb)
    pw = planet_weight_for_aspect(planet_a, planet_b)
    slug_a = SLUGS["internal_to_slug"][planet_a]
    slug_b = SLUGS["internal_to_slug"][planet_b]
    fid = feature_id(
        "synastry_aspect",
        planet_a=slug_a,
        aspect=meta["slug"],
        planet_b=slug_b,
    )
    conf = data_confidence_western(
        planet_a=planet_a,
        planet_b=planet_b,
        time_unknown_a=time_unknown_a,
        time_unknown_b=time_unknown_b,
    )
    return {
        "feature_id": fid,
        "system": "western",
        "method": "synastry_aspect",
        "method_version": METHOD_VERSION_WESTERN,
        "subject": "A",
        "object": "B",
        "raw_fact": {
            "planet_a": SLUGS["internal_to_raw"][planet_a],
            "aspect": meta["raw"],
            "planet_b": SLUGS["internal_to_raw"][planet_b],
            "exact_angle": int(meta["exact_angle"]),
            "actual_angle": actual_angle,
            "orb": orb,
        },
        "dimensions": dimensions_for_aspect(planet_a, planet_b),
        "salience": round(ow * pw, 3),
        "ease_or_tension": meta["ease_or_tension"],
        "method_consensus": "core",
        "data_confidence": round(conf, 3),
        "participates_in_convergence": True,
    }


def evidence_house_overlay(
    *,
    planet: str,
    house_number: int,
    visitor: str,
    owner: str,
) -> dict[str, Any]:
    """Build one ``house_overlay`` evidence object.

    ``visitor`` / ``owner`` are ``"A"`` or ``"B"`` (subject = visitor, object = owner).
    Only emitted when both birth times are known (caller responsibility).
    """
    if visitor not in ("A", "B") or owner not in ("A", "B"):
        raise ValueError(f"visitor/owner must be A or B; got {visitor!r}/{owner!r}")
    if not isinstance(house_number, int) or not (1 <= house_number <= 12):
        raise ValueError(f"house_number must be int 1–12; got {house_number!r}")
    slug = SLUGS["internal_to_slug"][planet]
    v = visitor.lower()
    o = owner.lower()
    fid = feature_id(
        "house_overlay",
        visitor=v,
        planet=slug,
        owner=o,
        house_number=str(house_number),
    )
    pw = PLANET_WEIGHT[planet]
    return {
        "feature_id": fid,
        "system": "western",
        "method": "house_overlay",
        "method_version": METHOD_VERSION_WESTERN,
        "subject": visitor,
        "object": owner,
        "raw_fact": {
            "planet": SLUGS["internal_to_raw"][planet],
            "house_number": house_number,
            "house_system": "placidus",
        },
        "dimensions": dimensions_for_planet(planet),
        "salience": round(pw * HOUSE_OVERLAY_WEIGHT, 3),
        "ease_or_tension": "mixed",
        "method_consensus": "core",
        "data_confidence": DATA_CONFIDENCE_BOTH_KNOWN,
        "participates_in_convergence": False,
    }


def evidence_angle_contact(
    *,
    planet: str,
    angle: str,
    aspect: str,
    actual_angle: float,
    orb: float,
    subject: str,
    obj: str,
) -> dict[str, Any]:
    """Build one ``angle_contact`` evidence object.

    ``planet_weight`` is fixed at ``ANGLE_CONTACT_PLANET_WEIGHT`` (0.5), not max.
    ``angle`` is an internal name (上升/下降/天頂/天底).
    Only emitted when both birth times are known (caller responsibility).
    ``obj`` is the object chart label (``"A"`` / ``"B"``); the evidence key
    remains ``"object"``.
    """
    if subject not in ("A", "B") or obj not in ("A", "B"):
        raise ValueError(f"subject/object must be A or B; got {subject!r}/{obj!r}")
    if angle not in ANGLE_BODIES:
        raise ValueError(f"angle must be an angle body; got {angle!r}")
    meta = ASPECT_BY_SLUG[aspect]
    max_orb = resolve_max_orb(planet, angle, aspect)
    ow = orb_weight(orb, max_orb)
    slug_p = SLUGS["internal_to_slug"][planet]
    slug_ang = SLUGS["internal_to_slug"][angle]
    fid = feature_id(
        "angle_contact",
        subject=subject.lower(),
        planet=slug_p,
        aspect=meta["slug"],
        object=obj.lower(),
        angle=slug_ang,
    )
    return {
        "feature_id": fid,
        "system": "western",
        "method": "angle_contact",
        "method_version": METHOD_VERSION_WESTERN,
        "subject": subject,
        "object": obj,
        "raw_fact": {
            "planet": SLUGS["internal_to_raw"][planet],
            "angle": slug_ang,
            "aspect": meta["raw"],
            "exact_angle": int(meta["exact_angle"]),
            "actual_angle": actual_angle,
            "orb": orb,
        },
        "dimensions": dimensions_for_angle_contact(planet, angle),
        "salience": round(ow * ANGLE_CONTACT_PLANET_WEIGHT, 3),
        "ease_or_tension": meta["ease_or_tension"],
        "method_consensus": "core",
        "data_confidence": DATA_CONFIDENCE_BOTH_KNOWN,
        "participates_in_convergence": True,
    }


def evidence_hd_channel_connection(
    *,
    lo: int,
    hi: int,
    link_type: str,
    full_channel_owner: str | None,
    a_gates: Sequence[int],
    b_gates: Sequence[int],
    center_lo: str,
    center_hi: str,
    time_unknown_a: bool = False,
    time_unknown_b: bool = False,
    fast_gates_a: Any = frozenset(),
    fast_gates_b: Any = frozenset(),
) -> dict[str, Any]:
    """Build one ``hd_channel_connection`` evidence object.

    ``lo``/``hi`` are normalized gate numbers (lo < hi); ``center_lo`` /
    ``center_hi`` are the internal Chinese center names of those gates.
    ``full_channel_owner`` is ``"A"``/``"B"`` for dominance/compromise and
    ``None`` for electromagnetic/companionship (directionless: subject A,
    object B).
    """
    if link_type not in HD_LINK_SALIENCE:
        raise ValueError(f"unknown HD link type: {link_type!r}")
    if full_channel_owner not in ("A", "B", None):
        raise ValueError(
            f"full_channel_owner must be 'A', 'B' or None; got {full_channel_owner!r}"
        )
    if link_type in ("electromagnetic", "companionship"):
        if full_channel_owner is not None:
            raise ValueError(f"{link_type} has no full_channel_owner")
        subject, obj = "A", "B"
    else:
        if full_channel_owner is None:
            raise ValueError(f"{link_type} requires full_channel_owner")
        subject = full_channel_owner
        obj = "B" if full_channel_owner == "A" else "A"
    conf = data_confidence_hd_channel(
        channel_gates=(lo, hi),
        fast_gates_a=fast_gates_a,
        fast_gates_b=fast_gates_b,
        time_unknown_a=time_unknown_a,
        time_unknown_b=time_unknown_b,
    )
    return {
        "feature_id": feature_id(
            "hd_channel_connection", lo=str(lo), hi=str(hi), link_type=link_type
        ),
        "system": "human_design",
        "method": "hd_channel_connection",
        "method_version": METHOD_VERSION_HD,
        "subject": subject,
        "object": obj,
        "raw_fact": {
            "channel": f"{lo}-{hi}",
            "link_type": link_type,
            "a_gates": sorted(a_gates),
            "b_gates": sorted(b_gates),
            "centers": [HD_CENTER_RAW[center_lo], HD_CENTER_RAW[center_hi]],
            "full_channel_owner": full_channel_owner,
        },
        "dimensions": dimensions_for_hd_channel(link_type, center_lo, center_hi),
        "salience": round(HD_LINK_SALIENCE[link_type], 3),
        "ease_or_tension": HD_LINK_EASE[link_type],
        "method_consensus": "core",
        "data_confidence": round(conf, 3),
        "participates_in_convergence": True,
    }


def evidence_hd_center_state(
    *,
    center: str,
    state: str,
    causing_channels: Sequence[str],
    time_unknown_a: bool = False,
    time_unknown_b: bool = False,
) -> dict[str, Any]:
    """Build one ``hd_center_state`` evidence object.

    ``center`` is the internal Chinese name; ``state`` uses the underscore
    enum (hyphenated slug only appears in the feature_id). Non-directional:
    subject/object are None and the entry never votes in convergence.
    """
    if center not in HD_CENTER_SLUG:
        raise ValueError(f"unknown HD center: {center!r}")
    if state not in HD_STATE_SLUG:
        raise ValueError(f"unknown HD center state: {state!r}")
    if time_unknown_a or time_unknown_b:
        conf = DATA_CONFIDENCE_HD_UNKNOWN
    else:
        conf = DATA_CONFIDENCE_BOTH_KNOWN
    return {
        "feature_id": feature_id(
            "hd_center_state",
            center_slug=HD_CENTER_SLUG[center],
            state_slug=HD_STATE_SLUG[state],
        ),
        "system": "human_design",
        "method": "hd_center_state",
        "method_version": METHOD_VERSION_HD,
        "subject": None,
        "object": None,
        "raw_fact": {
            "center": HD_CENTER_RAW[center],
            "state": state,
            "causing_channels": sorted(causing_channels),
        },
        "dimensions": list(HD_CENTER_THEMES[center]),
        "salience": HD_CENTER_STATE_SALIENCE,
        "ease_or_tension": "mixed",
        "method_consensus": "core",
        "data_confidence": round(conf, 3),
        "participates_in_convergence": False,
    }


def _is_unit_interval_rounded3(value: Any) -> bool:
    """True iff value is a real number in [0, 1] equal to round(value, 3)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    f = float(value)
    if not (0.0 <= f <= 1.0):
        return False
    return f == round(f, 3)


def _reject_forbidden_key(key: str) -> None:
    # Substring match (case-insensitive for ASCII tokens) — same rule as
    # the recursive forbidden-key scan. Blocks score_total, compatibility_pct, etc.
    key_l = key.lower()
    for forbidden in FORBIDDEN_EVIDENCE_KEYS:
        if forbidden == "吉凶":
            if forbidden in key:
                raise ValueError(f"evidence contains forbidden key: {key!r}")
        elif forbidden.lower() in key_l:
            raise ValueError(f"evidence contains forbidden key: {key!r}")


def _reject_forbidden_keys(node: Any) -> None:
    """Apply ``FORBIDDEN_EVIDENCE_KEYS`` to every dict key inside ``node``."""
    if isinstance(node, Mapping):
        for key, value in node.items():
            if isinstance(key, str):
                _reject_forbidden_key(key)
            _reject_forbidden_keys(value)
    elif isinstance(node, (list, tuple)):
        for item in node:
            _reject_forbidden_keys(item)


def validate_evidence(obj: Mapping[str, Any]) -> None:
    """Raise ``ValueError`` if ``obj`` is not a well-formed Evidence dict."""
    if not isinstance(obj, Mapping):
        raise ValueError("evidence must be a mapping")
    for key in REQUIRED_EVIDENCE_KEYS:
        if key not in obj:
            raise ValueError(f"evidence missing required key: {key}")

    for key in obj:
        if not isinstance(key, str):
            raise ValueError(f"evidence key must be a string: {key!r}")
        _reject_forbidden_key(key)

    fid = obj["feature_id"]
    if not isinstance(fid, str):
        raise ValueError("feature_id must be a string")
    if "_" in fid:
        raise ValueError(f"feature_id must not contain underscore: {fid!r}")
    if not _FEATURE_ID_RE.fullmatch(fid):
        raise ValueError(f"feature_id does not match required pattern: {fid!r}")

    system = obj["system"]
    if system not in _SYSTEM_DOMAIN:
        raise ValueError(f"system out of domain: {system!r}")

    method = obj["method"]
    if method not in METHOD_VERSION_BY_METHOD:
        raise ValueError(f"method out of domain: {method!r}")
    expected_version = METHOD_VERSION_BY_METHOD[method]
    version = obj["method_version"]
    if version != expected_version:
        raise ValueError(
            f"method_version {version!r} does not match method {method!r} "
            f"(expected {expected_version!r})"
        )

    consensus = obj["method_consensus"]
    if consensus not in _METHOD_CONSENSUS_DOMAIN:
        raise ValueError(f"method_consensus out of domain: {consensus!r}")

    raw = obj["raw_fact"]
    if not isinstance(raw, Mapping):
        raise ValueError("raw_fact must be a mapping")
    # Recurse into raw_fact: scoring-named keys nested there would slip past a
    # top-level-only scan of the evidence object.
    _reject_forbidden_keys(raw)

    pic = obj["participates_in_convergence"]
    if not isinstance(pic, bool):
        raise ValueError("participates_in_convergence must be a bool")

    for num_key in ("salience", "data_confidence"):
        val = obj[num_key]
        if not _is_unit_interval_rounded3(val):
            raise ValueError(
                f"{num_key} must be a number in [0.0, 1.0] equal to round(x, 3); "
                f"got {val!r}"
            )

    eot = obj["ease_or_tension"]
    if eot not in _EASE_DOMAIN:
        raise ValueError(f"ease_or_tension out of domain: {eot!r}")

    dims = obj["dimensions"]
    if not isinstance(dims, Sequence) or isinstance(dims, (str, bytes)):
        raise ValueError("dimensions must be a list")
    for d in dims:
        if d not in _THEMES_SET:
            raise ValueError(f"dimensions contains non-themes-v1 id: {d!r}")
