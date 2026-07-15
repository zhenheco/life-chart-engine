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
| **schema_version** | `1.1` |

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
- **Node.js ≥ 18 on PATH is a hard runtime requirement** (supported/tested on
  18 and 24 in CI) — 紫微斗數 runs via a Node sidecar. A missing or failing
  `node` fails the whole request loudly (`--json`: `{"ok": false}` exit `1`
  naming the requirement; Markdown: one stderr line, empty stdout; HTTP: `500`).
  This applies to `pip install life-chart-engine` installs too — install Node
  from https://nodejs.org or your package manager.
- Pass `--json` for the structured contract below. Omit it for human Markdown.
- The process prints **exactly one JSON object to stdout** and nothing else.

Optional HTTP wrapper (source checkout only — the PyPI wheel ships the CLI and
MCP entry points, not `server.py`; run `bash setup.sh` first to install
FastAPI/Uvicorn):

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

- `GET /health` returns `200`.
- `POST /chart` accepts the same input fields as the CLI flags, with `tz`
  mapped to `tz_offset` internally, and returns the same `schema_version: "1.1"`
  JSON object.
- If `ENGINE_API_KEY` is set, callers must send `X-Engine-Key` (wrong key → `401`).
- **Fail-closed:** if `ENGINE_API_KEY` is NOT set, the server refuses requests with
  `503` unless `ENGINE_ALLOW_OPEN=1` is set explicitly (local/dev only).
- HTTP input validation shares `scripts/validation.py` with the CLI. Out-of-range
  `tz`/`lat`/`lon`, non-finite values, and years outside 1900–2100 return `400`
  (deliberate hardening added in v1.1.0; previously such values could reach the
  engine as a `200` wrong chart or a `500`).
- Hetzner Docker+Caddy deployment notes live in [`DEPLOY-HETZNER.md`](./DEPLOY-HETZNER.md).

---

## 3. Input contract

| flag | type | required | format / rule |
|------|------|:---:|---------------|
| `--date` | string | **yes** | Gregorian `YYYY-M-D` (zero-padding optional, e.g. `1990-6-15`). Must be a real calendar date with year in the supported window **1900–2100**. Convert lunar dates before calling. |
| `--time` | string | **yes** | `H:M`, 24h, **local clock time** at birthplace (zero-padding optional, e.g. `8:30` or `8:5`). |
| `--tz` | float | **yes** | UTC offset of the birthplace **at the moment of birth, including DST**, in `[-12, 14]`, finite. Taiwan after 1980 = `8`. |
| `--lat` | float | **yes** | Latitude in `[-90, 90]`, finite (city-level precision is enough). |
| `--lon` | float | **yes** | Longitude in `[-180, 180]`, finite. |
| `--gender` | enum | **yes** | `男` or `女`. Affects Zi Wei; required so a wrong-gender chart can never be produced silently. |
| `--example` | flag | no | Compute the built-in example person (`範例`, 2000-01-01 12:00, UTC+8, Taipei 101). **Mutually exclusive with all six birth flags** (combining → exit `2`). May combine with `--name`, `--target`, `--ziwei-day-divide`, `--json`. |
| `--name` | string | no | Display label only. |
| `--target` | string | no | Zi Wei horoscope reference date `YYYY-M-D`, same 1900–2100 window. Pass today's date for current 大限/流年. |
| `--ziwei-day-divide` | enum | no | Late 子 hour rule: `forward` (default, 23:00-23:59 counts as next day) or `current` (counts as current day). |

> **Breaking change (v1.1.0):** the historical behaviour where omitted birth
> flags silently fell back to the example person has been **removed**. All six
> birth flags are now required (or pass `--example` explicitly); any missing
> flag, malformed value, out-of-range value, or out-of-window year exits `2`
> with usage on stderr and **empty stdout** — in `--json` mode too. This is a
> CLI behaviour fix, not a JSON schema change (`schema_version` stays `1.1`).

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
  "schema_version": "1.1",
  "input": {
    "name": "小明", "gender": "女",
    "date": "1990-06-15", "time": "08:30",
    "tz_offset": 8.0, "lat": 25.033, "lon": 121.5654,
    "target": "2025-01-01"
  },
  "western": {
    "system": "Tropical / Placidus / astronomy-engine",
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
    "horoscope": {
      // All-or-nothing: a sidecar/horoscope failure aborts the WHOLE request
      // (exit 1 / HTTP 500) — a partial or null horoscope is never emitted on
      // failure. When the request succeeds this object is always
      // { decadal, yearly, age }. `mutagen` (unchanged since 1.0) is a bare
      // star-name array in iztro's fixed 祿/權/科/忌 (化祿,化權,化科,化忌) order.
      // `mutagenTyped`, `decadal.ageRange`, and the `age` sub-object are the
      // schema_version 1.1 additions; `stars` and `yearlyDecStar` predate 1.1
      // (emitted since the iztro sidecar port) and are simply documented as of 1.1.
      "decadal": {
        "index": 9, "name": "大限",
        "heavenlyStem": "丁", "earthlyBranch": "亥",
        "ageRange": [33, 42],                       // 1.1: current 大限 age span
        "palaceNames": [ /* 12 strings */ ],
        "mutagen": ["太陰", "天同", "天機", "巨門"],   // 1.0-unchanged bare strings, 祿/權/科/忌 order
        "mutagenTyped": [ { "star": "太陰", "type": "祿" }, { "star": "天同", "type": "權" },
                          { "star": "天機", "type": "科" }, { "star": "巨門", "type": "忌" } ], // 1.1: typed view, same order
        "stars": [ [ /* per-palace horoscope-star name arrays, 12 entries */ ] ] // decadal/yearly ONLY (age has none); pre-1.1 field, documented as of 1.1
      },
      "yearly": {
        "index": 4, "name": "流年",
        "heavenlyStem": "甲", "earthlyBranch": "辰",
        "palaceNames": [ /* 12 strings */ ],
        "mutagen": ["廉貞", "破軍", "武曲", "太陽"],   // bare strings, 祿/權/科/忌 order
        "mutagenTyped": [ { "star": str, "type": "祿|權|科|忌" } /* …4, same order */ ], // 1.1
        "stars": [ [ /* 12 per-palace arrays */ ] ],       // decadal/yearly ONLY; pre-1.1, documented as of 1.1
        "yearlyDecStar": { /* 流年將前12神/歲前12神 star placements */ } // yearly ONLY; pre-1.1, documented as of 1.1
      },
      // 小限 (annual age-based minor limit); 1.1 addition, may be null
      "age": {
        "index": 4, "nominalAge": 26, "name": "小限",
        "heavenlyStem": "甲", "earthlyBranch": "辰",
        "palaceNames": [ /* 12 strings */ ],
        "mutagen": [ str /* …4, bare strings, 祿/權/科/忌 order */ ],
        "mutagenTyped": [ { "star": str, "type": "祿|權|科|忌" } /* …4, same order */ ] // 1.1
      }
    }
  },
  "meta": { "engine": "life-chart-engine", "version": "1.0", "ephemeris": "astronomy-engine" }
}
```

### Field notes

- `western.aspects` is **not capped** (Markdown mode shows top 10). Cap downstream
  if needed.
- `ziwei.horoscope` is **all-or-nothing**: on success it is always
  `{ decadal, yearly, age }`; a sidecar/horoscope failure fails the whole
  request loudly (never a partial/null horoscope in a `"ok": true` response).
  Field asymmetry: `stars` appears **only** under `decadal` and `yearly`
  (never `age`), and `yearlyDecStar` **only** under `yearly`. Each
  `mutagen` is a **bare star-name array** `[str, …4]` in iztro's fixed
  祿/權/科/忌 order — **unchanged since `schema_version` `1.0`**, so 1.0
  consumers reading `mutagen` as strings keep working. `schema_version` `1.1` is
  an **additive, backward-compatible** bump that adds, alongside the unchanged
  `mutagen`: `mutagenTyped` (a typed view `[{ "star", "type" }, …4]` in the same
  positional order) on `decadal`/`yearly`/`age`; `decadal.ageRange:
  [startAge, endAge]` for the current 大限; and the `age` sub-object — the 小限
  (annual age-based minor limit), which may be `null`.
- The positional 祿/權/科/忌 mapping in `mutagenTyped` is **invariant across all
  10 天干** — index 0 → 祿, 1 → 權, 2 → 科, 3 → 忌. (庚's four-化 *star set*
  differs by school, but the position→type mapping does not.)
- `*_stars` strings encode brightness and 四化, e.g. `紫微(廟)[祿]` =
  star(brightness)[mutagen].
- All ecliptic longitudes are degrees `[0,360)`. `deg`/`min` are the
  within-sign degree/minute.
- `meta.version` (`"1.0"`) is the **engine's internal version string** and is
  independent of both `schema_version` (`"1.1"`) and the PyPI package version
  (`1.1.0`); consumers should branch on `schema_version` only.

---

## 5. Exit codes & errors

| exit | meaning | stdout |
|:---:|---|---|
| `0` | success | the JSON object with `"ok": true` |
| `1` | runtime error (with `--json`) | `{ "ok": false, "error": "<message>", "schema_version": "1.1" }` |
| `2` | argument/validation error (argparse) | **empty** (usage text goes to stderr) — includes missing required flags, malformed dates/times, out-of-range `tz`/`lat`/`lon`, years outside 1900–2100, and illegal `--example` combinations |

Agents should branch on `ok` (and on exit code) before reading chart fields.

**Error transport matrix** — the *validation decision* is identical on every
surface (same shared validator); only the carrier differs:

| failure class | CLI | HTTP `/chart` | MCP `compute_chart` |
|---|---|---|---|
| validation error (missing/malformed/out-of-range/out-of-window input) | exit `2`, empty stdout, usage on stderr | `400` + `detail` naming the field | `isError: true` + field-named message |
| runtime error (Node sidecar failure, high-latitude Placidus, timeout) | exit `1` (`--json`: one `{"ok": false}` envelope; Markdown: message on stderr, empty stdout) | `500` + `{"ok": false, ...}` envelope | `isError: true` + message |

---

## 6. MCP surface (`compute_chart`)

Install the optional extra and register the stdio server:

```bash
pip install 'life-chart-engine[mcp]'   # pins mcp==1.28.1
```

Claude Desktop / Claude Code config:

```jsonc
{
  "mcpServers": {
    "life-chart-engine": { "command": "life-chart-mcp" }
  }
}
```

- One tool: `compute_chart`. Inputs mirror the HTTP `/chart` body exactly —
  required `date`, `time`, `tz`, `lat`, `lon`, `gender`; optional `name`,
  `target`, `ziwei_day_divide`. Validation is the same shared
  `scripts/validation.py` (same ranges, same 1900–2100 window).
- Success: a **single text content** whose bytes equal the CLI `--json` stdout
  minus the trailing newline (shared serializer). Parse it as the §4 envelope.
- Failures (validation or runtime) return `isError: true` with a message; the
  server stays alive. stdio only — no network is opened by the server itself.
- No-network proof boundary: the Python socket guard covers the Python
  process; the Node sidecar child is proven statically (its two `.cjs`
  sources contain no network primitives — enforced by a repo test).

---

## 7. Hermes / orchestrator integration

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

## 8. Minimal example

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
