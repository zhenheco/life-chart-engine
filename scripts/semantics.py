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

# Top-level keys that must never appear on an Evidence object (spec §evidence schema).
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


def data_confidence_western(
    *,
    planet_a: str,
    planet_b: str,
    time_unknown_a: bool,
    time_unknown_b: bool,
) -> float:
    """Western synastry_aspect confidence (not HD channel rules)."""
    if not time_unknown_a and not time_unknown_b:
        return 0.95
    # Unknown-side Moon participation → 0.6
    if time_unknown_a and planet_a == "月亮":
        return 0.6
    if time_unknown_b and planet_b == "月亮":
        return 0.6
    return 0.85


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


def _is_unit_interval_rounded3(value: Any) -> bool:
    """True iff value is a real number in [0, 1] equal to round(value, 3)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    f = float(value)
    if not (0.0 <= f <= 1.0):
        return False
    return f == round(f, 3)


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
        # Substring match (case-insensitive for ASCII tokens) — same rule as
        # the recursive forbidden-key scan. Blocks score_total, compatibility_pct, etc.
        key_l = key.lower()
        for forbidden in FORBIDDEN_EVIDENCE_KEYS:
            if forbidden == "吉凶":
                if forbidden in key:
                    raise ValueError(f"evidence contains forbidden key: {key!r}")
            elif forbidden.lower() in key_l:
                raise ValueError(f"evidence contains forbidden key: {key!r}")

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
