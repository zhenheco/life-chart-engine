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

# Error contract shared by HTTP POST /synastry and CLI dual mode
# (spec §完整度、錯誤與安全). Tokens are machine-parsable; messages are fixed
# strings — exception text is never surfaced to callers.
ERROR_COMPUTATION_UNSUPPORTED = "computation_unsupported"
ERROR_INTERNAL = "internal_error"
MESSAGE_COMPUTATION_UNSUPPORTED = (
    "chart cannot be computed for the given coordinates"
)
MESSAGE_INTERNAL = "synastry computation failed"

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

# Bodies whose gate activations degrade channel confidence to 0.6 when their
# side's birth time is unknown (Moon/Mercury/Venus/Mars — spec §HD 窮盡切分).
HD_FAST_BODIES: frozenset[str] = frozenset({"☾", "☿", "♀", "♂"})


def _import_western():
    """Load ``western`` without creating a package-level cycle with chart_engine."""
    if __package__:
        from .chart_engine import western
    else:
        from chart_engine import western
    return western


def _import_hd_tables():
    """Load ``human_design`` / ``CHANNELS`` / ``GATE_CENTER`` (same cycle rule)."""
    if __package__:
        from .chart_engine import CHANNELS, GATE_CENTER, human_design
    else:
        from chart_engine import CHANNELS, GATE_CENTER, human_design
    return human_design, CHANNELS, GATE_CENTER


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


def hd_active_gates(rows) -> set[int]:
    """Distinct active gates from ``human_design()`` rows.

    Each row is ``(body, personality_gate, personality_line, design_gate,
    design_line)``. The same gate activated by several bodies collapses to a
    single active gate (set membership is binary).
    """
    gates: set[int] = set()
    for _body, p_gate, _p_line, d_gate, _d_line in rows:
        gates.add(p_gate)
        gates.add(d_gate)
    return gates


def hd_fast_gates(rows) -> set[int]:
    """Gates activated by Moon/Mercury/Venus/Mars (personality or design)."""
    gates: set[int] = set()
    for body, p_gate, _p_line, d_gate, _d_line in rows:
        if body in HD_FAST_BODIES:
            gates.add(p_gate)
            gates.add(d_gate)
    return gates


def classify_hd_channel(lo: int, hi: int, gates_a, gates_b):
    """Classify one channel by the 9-grid (spec §人類圖連結判定).

    Returns ``(link_type, full_channel_owner)``; ``(None, None)`` when the
    channel produces no connection (never emitted).
    """
    a_count = (lo in gates_a) + (hi in gates_a)
    b_count = (lo in gates_b) + (hi in gates_b)
    if a_count == 2 and b_count == 2:
        return "companionship", None
    if a_count == 2 and b_count == 1:
        return "compromise", "A"
    if a_count == 1 and b_count == 2:
        return "compromise", "B"
    if a_count == 2 and b_count == 0:
        return "dominance", "A"
    if a_count == 0 and b_count == 2:
        return "dominance", "B"
    if a_count == 1 and b_count == 1:
        # Complementary ends → electromagnetic; both hold the same single
        # gate → no connection.
        if (lo in gates_a) != (lo in gates_b):
            return "electromagnetic", None
        return None, None
    return None, None


def merged_hd_channels(gates_a, gates_b) -> list[tuple[int, int]]:
    """Channels complete in the A∪B gate union, normalized, ascending."""
    _hd_fn, channels, _gate_center = _import_hd_tables()
    union = set(gates_a) | set(gates_b)
    out = []
    for g1, g2 in channels:
        lo, hi = min(g1, g2), max(g1, g2)
        if lo in union and hi in union:
            out.append((lo, hi))
    return sorted(out)


def compute_hd_channel_connections(
    gates_a,
    gates_b,
    *,
    time_unknown_a: bool = False,
    time_unknown_b: bool = False,
    fast_gates_a=frozenset(),
    fast_gates_b=frozenset(),
) -> list[dict[str, Any]]:
    """One ``hd_channel_connection`` per connected channel, sorted.

    Gate activation sets come from ``human_design()`` via
    ``hd_active_gates`` — never recomputed here.
    """
    _hd_fn, channels, gate_center = _import_hd_tables()
    out: list[dict[str, Any]] = []
    for g1, g2 in channels:
        lo, hi = min(g1, g2), max(g1, g2)
        link_type, owner = classify_hd_channel(lo, hi, gates_a, gates_b)
        if link_type is None:
            continue
        out.append(
            semantics.evidence_hd_channel_connection(
                lo=lo,
                hi=hi,
                link_type=link_type,
                full_channel_owner=owner,
                a_gates=[g for g in (lo, hi) if g in gates_a],
                b_gates=[g for g in (lo, hi) if g in gates_b],
                center_lo=gate_center[lo],
                center_hi=gate_center[hi],
                time_unknown_a=time_unknown_a,
                time_unknown_b=time_unknown_b,
                fast_gates_a=fast_gates_a,
                fast_gates_b=fast_gates_b,
            )
        )
    return _sort_evidence(out)


def compute_hd_center_states(
    defined_a,
    defined_b,
    merged_channels,
    *,
    time_unknown_a: bool = False,
    time_unknown_b: bool = False,
) -> list[dict[str, Any]]:
    """One ``hd_center_state`` per center in fixed 頭→…→根 row order.

    ``defined_a`` / ``defined_b`` are the persons' own defined-center name
    sets (internal Chinese); ``merged_channels`` are normalized (lo, hi)
    pairs complete in the union.
    """
    _hd_fn, _channels, gate_center = _import_hd_tables()
    merged_defined: set[str] = set()
    for lo, hi in merged_channels:
        merged_defined.add(gate_center[lo])
        merged_defined.add(gate_center[hi])
    out: list[dict[str, Any]] = []
    for center in semantics.HD_CENTER_ORDER:
        if center in defined_a and center in defined_b:
            state = "both_defined"
        elif center in defined_a:
            state = "a_defined"
        elif center in defined_b:
            state = "b_defined"
        elif center in merged_defined:
            state = "defined_by_merge"
        else:
            state = "undefined"
        if state == "defined_by_merge":
            causing = [
                f"{lo}-{hi}"
                for lo, hi in merged_channels
                if gate_center[lo] == center or gate_center[hi] == center
            ]
        else:
            causing = []
        out.append(
            semantics.evidence_hd_center_state(
                center=center,
                state=state,
                causing_channels=causing,
                time_unknown_a=time_unknown_a,
                time_unknown_b=time_unknown_b,
            )
        )
    return out


def _center_components(defined, own_channels, gate_center) -> dict[str, int]:
    """Map each defined center to a component id via the person's own channels."""
    adj = {c: set() for c in sorted(defined)}
    for lo, hi in own_channels:
        c1, c2 = gate_center[lo], gate_center[hi]
        if c1 != c2 and c1 in adj and c2 in adj:
            adj[c1].add(c2)
            adj[c2].add(c1)
    comp: dict[str, int] = {}
    next_id = 0
    for center in sorted(defined):
        if center in comp:
            continue
        next_id += 1
        stack = [center]
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp[x] = next_id
            stack.extend(y for y in sorted(adj[x]) if y not in comp)
    return comp


def compute_split_bridges(own_gates, partner_gates) -> list[dict[str, Any]]:
    """Merged channels bridging two of the person's own definition components.

    Channels the person cannot complete alone but the merge completes, whose
    two centers lie in different own connected components. Sorted by channel
    string ascending.
    """
    _hd_fn, channels, gate_center = _import_hd_tables()
    own: set[tuple[int, int]] = set()
    merged: list[tuple[int, int]] = []
    for g1, g2 in channels:
        lo, hi = min(g1, g2), max(g1, g2)
        if lo in own_gates and hi in own_gates:
            own.add((lo, hi))
        lo_any = lo in own_gates or lo in partner_gates
        hi_any = hi in own_gates or hi in partner_gates
        if lo_any and hi_any:
            merged.append((lo, hi))
    defined: set[str] = set()
    for lo, hi in sorted(own):
        defined.add(gate_center[lo])
        defined.add(gate_center[hi])
    comp = _center_components(defined, sorted(own), gate_center)
    bridges: list[dict[str, Any]] = []
    for lo, hi in merged:
        c1, c2 = gate_center[lo], gate_center[hi]
        if c1 in comp and c2 in comp and comp[c1] != comp[c2]:
            bridges.append(
                {
                    "channel": f"{lo}-{hi}",
                    "centers": [
                        semantics.HD_CENTER_RAW[c1],
                        semantics.HD_CENTER_RAW[c2],
                    ],
                }
            )
    return sorted(bridges, key=lambda b: b["channel"])


def compute_hanging_gates_completed(
    own_gates, partner_gates
) -> list[dict[str, Any]]:
    """The person's hanging gates completed by the partner's gates.

    Sorted by own_gate ascending, then channel string ascending (a gate in
    three channels can be completed more than once).
    """
    _hd_fn, channels, _gate_center = _import_hd_tables()
    out: list[dict[str, Any]] = []
    for g1, g2 in channels:
        lo, hi = min(g1, g2), max(g1, g2)
        if lo in own_gates and hi not in own_gates and hi in partner_gates:
            out.append(
                {"own_gate": lo, "partner_gate": hi, "channel": f"{lo}-{hi}"}
            )
        if hi in own_gates and lo not in own_gates and lo in partner_gates:
            out.append(
                {"own_gate": hi, "partner_gate": lo, "channel": f"{lo}-{hi}"}
            )
    return sorted(out, key=lambda e: (e["own_gate"], e["channel"]))


def build_participants(hd_a, hd_b, gates_a, gates_b) -> dict[str, Any]:
    """``participants`` block: not evidence objects, no feature_id."""
    out: dict[str, Any] = {}
    for key, hd, own, partner in (
        ("person_a", hd_a, gates_a, gates_b),
        ("person_b", hd_b, gates_b, gates_a),
    ):
        out[key] = {
            "type": hd["htype"],
            "strategy": semantics.STRATEGY_BY_TYPE[hd["htype"]],
            "authority": hd["auth"],
            "split_bridges": compute_split_bridges(own, partner),
            "hanging_gates_completed": compute_hanging_gates_completed(
                own, partner
            ),
        }
    return out


def build_synastry(inp_a, inp_b):
    """Return the synastry block (western + human design)."""
    western = _import_western()
    human_design_fn, _channels, _gate_center = _import_hd_tables()
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

    # Each person's chart is computed once; HD gate activation is read from
    # human_design() output, never re-derived here.
    hd_a = human_design_fn(inp_a, pos_a["太陽"])
    hd_b = human_design_fn(inp_b, pos_b["太陽"])
    gates_a = hd_active_gates(hd_a["rows"])
    gates_b = hd_active_gates(hd_b["rows"])
    channel_connections = compute_hd_channel_connections(
        gates_a,
        gates_b,
        time_unknown_a=time_unknown_a,
        time_unknown_b=time_unknown_b,
        fast_gates_a=hd_fast_gates(hd_a["rows"]),
        fast_gates_b=hd_fast_gates(hd_b["rows"]),
    )
    center_states = compute_hd_center_states(
        set(hd_a["defined"]),
        set(hd_b["defined"]),
        merged_hd_channels(gates_a, gates_b),
        time_unknown_a=time_unknown_a,
        time_unknown_b=time_unknown_b,
    )
    participants = build_participants(hd_a, hd_b, gates_a, gates_b)

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
            "channel_connections": channel_connections,
            "center_states": center_states,
            "participants": participants,
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
