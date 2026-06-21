# AGENTS.md — Tool contract for `life-chart-engine`

This file is the machine-facing contract. It tells an AI agent (Hermes
orchestrator, Claude Code, or any agent framework) **how to call this tool and
what shape the result has.** Humans should read [`README.md`](./README.md) first.

The tool is a **stateless, deterministic, one-shot CLI**. Same input → same
output. No network, no side effects, no persisted state. Safe to call in
parallel and to sandbox read-only.

---

## 1. Identity

| | |
|---|---|
| **name** | `life-chart-engine` |
| **summary** | Compute Western natal chart + Human Design + Zi Wei Dou Shu (紫微斗數) from birth data. |
| **kind** | CLI, stdin-free, args-in / JSON-out |
| **deterministic** | yes |
| **side effects** | none |
| **schema_version** | `1.0` |

---

## 2. Invocation

```bash
life-chart --json \
  --name "<label>" --gender <男|女> \
  --date <YYYY-MM-DD> --time <HH:MM> \
  --tz <float> --lat <float> --lon <float> \
  [--target <YYYY-MM-DD>]

# Fallback if life-chart is not on PATH:
<VENV_PY> <REPO>/scripts/chart_engine.py --json \
  --name "<label>" --gender <男|女> \
  --date <YYYY-MM-DD> --time <HH:MM> \
  --tz <float> --lat <float> --lon <float> \
  [--target <YYYY-MM-DD>]
```

- `life-chart` = the installed wrapper created by `install.sh`, symlinked to
  `~/.local/bin/life-chart`.
- `<VENV_PY>` = the project venv's Python (CPython 3.12), created by `setup.sh`
  (default `<REPO>/.venv/bin/python`). Do **not** use the system `python3`.
- Pass `--json` for the structured contract below. Omit it for human Markdown.
- The process prints **exactly one JSON object to stdout** and nothing else.

Optional HTTP wrapper:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

- `GET /health` returns `200`.
- `POST /chart` accepts the same input fields as the CLI flags, with `tz`
  mapped to `tz_offset` internally, and returns the same `schema_version: "1.0"`
  JSON object.
- If `ENGINE_API_KEY` is set, callers must send `X-Engine-Key`.
- Hetzner Docker+Caddy deployment notes live in [`DEPLOY-HETZNER.md`](./DEPLOY-HETZNER.md).

---

## 3. Input contract

| flag | type | required | format / rule |
|------|------|:---:|---------------|
| `--date` | string | yes | Gregorian `YYYY-MM-DD`. Convert lunar dates before calling. |
| `--time` | string | yes | `HH:MM`, 24h, **local clock time** at birthplace. |
| `--tz` | float | yes | UTC offset of the birthplace **at the moment of birth, including DST**. Taiwan after 1980 = `8`. |
| `--lat` | float | yes | Latitude (city-level precision is enough). |
| `--lon` | float | yes | Longitude. |
| `--gender` | enum | for 紫微 | `男` or `女`. Only affects Zi Wei. |
| `--name` | string | no | Display label only. |
| `--target` | string | no | Zi Wei horoscope reference date `YYYY-MM-DD`. Pass today's date for current 大限/流年. |

**Caller responsibilities (the agent, not the engine):**

1. **Resolve place → lat/lon/tz yourself.** The engine does NOT geocode and does
   NOT look up time zones. You must convert the city name to coordinates and to
   the correct historical UTC offset (DST-aware).
2. **Confirm time certainty before calling.** If the user only has an approximate
   birth time, flag every time-dependent field (ascendant, houses, Human Design
   lines, Zi Wei hour pillar) as low-confidence in your downstream output.
3. **Never fabricate chart values.** Always call this tool; do not answer chart
   data from memory.

---

## 4. Output contract (`--json`)

On success, stdout is one JSON object:

```jsonc
{
  "ok": true,
  "schema_version": "1.0",
  "input": {
    "name": "小明", "gender": "女",
    "date": "1990-06-15", "time": "08:30",
    "tz_offset": 8.0, "lat": 25.033, "lon": 121.5654,
    "target": "2025-01-01"
  },
  "western": {
    "system": "Tropical / Placidus / Moshier",
    "ascendant": { "lon": 123.4, "sign": "獅子", "deg": 3, "min": 25, "label": "獅子 03°25'" },
    "midheaven": { "lon": 33.1,  "sign": "金牛", "deg": 3, "min": 6,  "label": "金牛 03°06'" },
    "planets": [
      { "name": "太陽", "lon": 84.1, "sign": "雙子", "deg": 24, "min": 6,
        "label": "雙子 24°06'", "retrograde": false, "house": 11 }
      // order: 太陽,月亮,水星,金星,火星,木星,土星,天王星,海王星,冥王星,北交點,南交點
    ],
    "houses": [ { "house": 1, "lon": 123.4, "label": "獅子 03°25'" } /* …12 */ ],
    "aspects": [ { "a": "太陽", "b": "月亮", "type": "三分", "orb": 1.2 } ]
    // aspects: ALL detected, sorted by orb ascending (consumer may cap)
  },
  "human_design": {
    "type": "顯示生產者",
    "authority": "情緒型權威",
    "profile": "1/3",
    "definition": "二分人",
    "incarnation_cross": "右角度交叉（…）",
    "design_date": "1990-03-17",
    "defined_centers": ["薦骨", "情緒"],
    "open_centers": ["頭", "邏輯"],
    "channels": ["20-34", "1-8"],
    "gates": [
      { "planet": "☉",
        "personality": { "gate": 25, "line": 3 },
        "design":      { "gate": 51, "line": 2 } }
      // one per planet, order: ☉ ⊕ ☊ ☋ ☾ ☿ ♀ ♂ ♃ ♄ ♅ ♆ ♇
    ]
  },
  "ziwei": {
    "five_elements_class": "水二局",
    "soul": "貪狼",
    "body": "天相",
    "hour_index": 4,
    "palaces": [
      { "name": "命宮", "ganzhi": "甲子", "flags": "命身",
        "decadal_range": "4-13",
        "major_stars": ["紫微(廟)[祿]"],
        "minor_stars": ["左輔"],
        "adjective_stars": ["天廚"] }
      // 12 palaces
    ],
    "horoscope": { "decadal": { /* best-effort */ }, "yearly": { /* best-effort */ } }
  },
  "meta": { "engine": "life-chart-engine", "version": "1.0", "ephemeris": "Moshier" }
}
```

### Field notes

- `western.aspects` is **not capped** (Markdown mode shows top 10). Cap downstream
  if needed.
- `ziwei.horoscope` is serialized **best-effort** from py-iztro objects. If
  serialization fails it is `null` rather than crashing the run — treat it as
  optional.
- `*_stars` strings encode brightness and 四化, e.g. `紫微(廟)[祿]` =
  star(brightness)[mutagen].
- All ecliptic longitudes are degrees `[0,360)`. `deg`/`min` are the
  within-sign degree/minute.

---

## 5. Exit codes & errors

| exit | meaning | stdout |
|:---:|---|---|
| `0` | success | the JSON object with `"ok": true` |
| `1` | runtime error (with `--json`) | `{ "ok": false, "error": "<message>", "schema_version": "1.0" }` |
| `2` | argument error (argparse) | usage text on stderr |

Agents should branch on `ok` (and on exit code) before reading chart fields.

---

## 6. Hermes / orchestrator integration

This tool fits the **CLI + JSON** agent pattern directly:

- **Discovery** — this `AGENTS.md` is the manifest. The command, input flags, and
  output schema above are the full contract.
- **Dispatch** — invoke the `--json` command (Section 2) as a subprocess in the
  repo's workdir, using the venv Python from `setup.sh`.
- **Result handoff** — parse stdout as JSON; gate on `ok`; pass the structured
  object to the next step. No cleanup needed (stateless).
- **For a `[HERMES_ORCHESTRATED_TASK]`** the orchestrator should treat this as a
  pure compute step: provide resolved `lat/lon/tz`, capture the JSON, and return
  it as structured output without expanding scope.

> Want an HTTP or MCP front-end instead of raw CLI? Both are thin wrappers over
> the same `build_json(inp)` path — add them without touching the calculation
> core.

---

## 7. Minimal example

```bash
life-chart --json \
  --name "小明" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0330 --lon 121.5654 --target 2025-01-01

# Fallback if life-chart is not on PATH:
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0330 --lon 121.5654 --target 2025-01-01
```

A full captured sample lives in [`examples/sample-output.json`](./examples/sample-output.json).
