> 🌐 **English** · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**Deterministic native computation of three life-chart systems — Western natal astrology, 人類圖 (Human Design), and 紫微斗數 (Zi Wei Dou Shu) — from a single birth record.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` is a small, offline command-line tool. You give it one person's birth data — date, time, timezone, and place coordinates — and it computes three independent chart systems in one pass, then emits either a human-readable Markdown report or a structured JSON object for programs and AI agents to consume.

It is built for people who want **reproducible, verifiable** chart calculations rather than a black-box web app: practitioners, developers building self-awareness tools, and AI agents that need a pure compute step. Every number comes from real astronomical computation (Swiss Ephemeris) and a real 紫微斗數 library (iztro) — not from a remote service, not from cached lookups, and never over the network.

---

## What it computes

The engine runs three systems against the **same birth moment**, so their outputs can corroborate one another. Each system answers a different kind of question:

| System | What it is (plain English) | What the engine yields |
|--------|----------------------------|------------------------|
| **Western natal** (Tropical / Placidus) | Classical Western astrology — where the planets sat against the zodiac at your birth, divided into 12 houses. | Ascendant + Midheaven, 12 planets/points (太陽 → 南交點) with sign, degree, house and retrograde flag, all 12 house cusps, and every detected aspect (合相/六分/四分/三分/對分) sorted by tightness. |
| **人類圖 Human Design** | A modern synthesis of astrology, the I-Ching, and the chakra system. Describes how your energy is "wired" via gates, channels, and centers. | Type, Authority, Profile, Definition, Incarnation Cross, the 88°-earlier Design date, defined/open centers, defined channels, and per-planet gate.line activations for both the Personality and Design charts. |
| **紫微斗數 Zi Wei Dou Shu** | A traditional Chinese astrology system that maps fate onto a 12-palace board, populated by named stars. | 五行局 (Five Elements Class), 命主 (soul) / 身主 (body), the 時辰 hour index, and per-palace data — ganzhi, 命/身 flags, decadal age range, and major/minor/adjective stars (with brightness and 四化). Optionally a best-effort 大限/流年 horoscope. |

Type, Authority, and Definition in Human Design are **not hardcoded** — they are derived from the connectivity graph of the defined centers.

---

## Why native calculation

This engine does the real math instead of approximating or calling out to a service. That choice buys three properties that matter for any serious chart tool:

- **Deterministic.** The same birth input always produces the same output, byte-for-byte. There is no randomness, no model, no rounding drift between runs.
- **Reproducible.** Anyone with the repo and the same inputs can regenerate your exact chart. Calculations use Swiss Ephemeris (Moshier model) for the sky and iztro for 紫微斗數 — both deterministic.
- **Cross-verifiable.** Because three independent systems are computed from one birth moment, you can triangulate. **When all three systems point at the same signal, treat it as high confidence. When only one system shows a detail, treat it as a reference point, not a conclusion.** This is the engine's core design principle — it produces facts to cross-read, not a single verdict.

---

## Quick start

### One-line install (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

Installs into `~/.life-chart-engine` (override with `LIFE_CHART_DIR`). No `sudo`, no system-wide changes — it only clones the repo, builds an isolated CPython 3.12 venv, and uses the checked-in iztro Node bundle. Requires `git`, [`uv`](https://docs.astral.sh/uv/), and Node.js. Re-run any time to update to the latest version.

### From source

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### What `setup.sh` does

It runs under `set -euo pipefail` and performs five steps:

1. **Resolves the venv location** — `${LIFE_VENV:-<repo>/.venv}`. Set the `LIFE_VENV` env var to override; the default `.venv/` is git-ignored.
2. **Preflight: requires [`uv`](https://docs.astral.sh/uv/)** — if `uv` is not on `PATH` it exits `1` and prints the install hint:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Creates a CPython 3.12 venv** — `uv venv --python 3.12 "$VENV"` (see [Why CPython 3.12](#why-cpython-312-specifically)).
4. **Installs pinned dependencies** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Checks the Zi Wei Node sidecar bundle** — verifies Node.js is available and `vendor/iztro.cjs` exists.
6. **Runs a smoke test** — executes the engine once with fixed sample inputs (discarding stdout) and prints `OK — engine runs.` on success. It also prints usage hints for both modes.

### Manual `uv` steps (no `setup.sh`)

```bash
# 1. Create CPython 3.12 venv (default <repo>/.venv; override with LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Install pinned deps
uv pip install --python .venv/bin/python -r requirements.txt

# 3. (Optional) smoke test
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Python direct dependencies are pinned in `requirements.txt`:

```
pyswisseph==2.10.3.2
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei uses the checked-in `vendor/iztro.cjs` bundle. Maintainers regenerate it with `scripts/build-iztro-bundle.sh`, which uses `npm ci` from the committed `vendor/package-lock.json`:

```
iztro@2.5.8
esbuild@0.28.1
```

---

## Why CPython 3.12 specifically

The engine currently runs on the verified **CPython 3.12** runtime. The reason is stated identically in `requirements.txt` and `setup.sh`:

> CPython 3.12 remains locked for this change. The old Python Zi Wei native dependency constraint is gone, so this can be revisited after checking the remaining dependencies and deployment image.

In short: 3.12 is still the tested runtime for this release. The Zi Wei dependency no longer forces that lock, so a Python-version bump is a follow-up compatibility check rather than part of this refactor.

---

## Usage

The engine has two modes, selected by the presence of the `--json` flag.

### Human mode (Markdown)

Omit `--json` to get a readable console report. After `install.sh`, the short command is:

```bash
life-chart \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

If `life-chart` is not on your `PATH`, use:

```bash
~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Trimmed real sample (aspects are capped at top-10 in Markdown mode):

```
### Sample｜女｜1990-06-15 08:30 (UTC+8)

【西洋星盤 Tropical/Placidus】
上升 獅子 08°29' ｜ 天頂 金牛 04°22'
  太陽   雙子 23°40'  11宮
  月亮   雙魚 09°00'  8宮
  ...
  主要相位: 北交點-南交點對分(0.0°)；北交點-上升對分(0.4°)；南交點-上升合相(0.4°)；木星-冥王星三分(0.4°)；月亮-天王星六分(0.8°)…

【人類圖 Human Design】
類型 投射者 ｜ 權威 自我投射型權威 ｜ 角色 1/3 ｜ 定義 一分人(單一定義)
輪迴交叉 右角度交叉（12/11 | 36/6）
定義中心 G,喉 ｜ 開放中心 情緒,意志,根,脾,薦骨,邏輯,頭
設計日期 1990-03-16
通道 ['13-33']

【紫微斗數 iztro】
五行局 土五局 ｜ 命主 祿存 ｜ 身主 火星
  命宮   戊寅  (5-14): 七殺(廟)｜天廚 蜚廉
  父母   己卯  (115-124): 天同(平)[忌]｜地劫 天喜 咸池 恩光 天德
  ...
```

### Agent mode (JSON)

Add `--json` to get one JSON object on stdout and nothing else — ideal for programs and AI agents:

```bash
life-chart --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

If `life-chart` is not on your `PATH`, use:

```bash
~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Trimmed real sample (arrays truncated to 1–2 entries; values verbatim):

```json
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
    "ascendant": { "lon": 128.483, "sign": "獅子", "deg": 8, "min": 29, "label": "獅子 08°29'" },
    "midheaven": { "lon": 34.3665, "sign": "金牛", "deg": 4, "min": 22, "label": "金牛 04°22'" },
    "planets": [
      { "name": "太陽", "retrograde": false, "house": 11, "lon": 83.6719, "sign": "雙子", "deg": 23, "min": 40, "label": "雙子 23°40'" }
    ],
    "houses": [
      { "house": 1, "lon": 128.483, "label": "獅子 08°29'" }
    ],
    "aspects": [
      { "a": "北交點", "b": "南交點", "type": "對分", "orb": 0.0 },
      { "a": "木星", "b": "冥王星", "type": "三分", "orb": 0.3744 }
    ]
  },
  "human_design": {
    "type": "投射者",
    "authority": "自我投射型權威",
    "profile": "1/3",
    "definition": "一分人(單一定義)",
    "incarnation_cross": "右角度交叉（12/11 | 36/6）",
    "design_date": "1990-03-16",
    "defined_centers": ["G", "喉"],
    "open_centers": ["情緒", "意志", "根", "脾", "薦骨", "邏輯", "頭"],
    "channels": ["13-33"],
    "gates": [
      { "planet": "☉", "personality": { "gate": 12, "line": 1 }, "design": { "gate": 36, "line": 3 } }
    ]
  },
  "ziwei": {
    "five_elements_class": "土五局",
    "soul": "祿存",
    "body": "火星",
    "hour_index": 4,
    "palaces": [
      {
        "name": "命宮", "ganzhi": "戊寅", "flags": "", "decadal_range": "5-14",
        "major_stars": ["七殺(廟)"], "minor_stars": [], "adjective_stars": ["天廚", "蜚廉"]
      }
    ],
    "horoscope": { "decadal": { "...": "best-effort, may be null" } }
  },
  "meta": { "engine": "life-chart-engine", "version": "1.0", "ephemeris": "Moshier" }
}
```

---

### HTTP service

The optional FastAPI wrapper exposes the same JSON contract over HTTP:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

- `GET /health` returns `{"ok": true}`.
- `POST /chart` accepts JSON keys matching the CLI flags: `date`, `time`, `tz`,
  `lat`, `lon`, `gender`, optional `name`, optional `target`.
- If `ENGINE_API_KEY` is set, requests to `/chart` must include
  `X-Engine-Key: <value>` or they return `401`.

For Hetzner Docker+Caddy deployment, see **[DEPLOY-HETZNER.md](./DEPLOY-HETZNER.md)**.

---

## Windows quick start

The Unix `install.sh` / `setup.sh` assume a POSIX layout (`.venv/bin/python`) and pin
CPython 3.12. On Windows, `pyswisseph==2.10.3.2` has **no 3.12 wheel**, so a 3.12 venv
tries to compile it from C and fails unless MSVC Build Tools are installed. The bundled
`setup.ps1` avoids this by using **CPython 3.11**, where every native dep
(`pyswisseph` / `pythonmonkey` / `pydantic-core`) ships a wheel — no compiler needed.
`py-iztro` behaves identically on 3.11.

```powershell
# prerequisites: git, and uv
irm https://astral.sh/uv/install.ps1 | iex      # if uv is not installed

git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
./setup.ps1            # CPython 3.11 venv + pinned deps (no compiler)
./life-chart.ps1 --help
```

`life-chart.ps1` is the Windows equivalent of the `life-chart` wrapper (the venv lives at
`.venv\Scripts\python.exe`, not `.venv/bin/python`). For the Markdown report, set
`$env:PYTHONUTF8 = "1"` so the console doesn't choke on the `℞` retrograde glyph under
legacy code pages — `setup.ps1` / the launchers already do this.

---

## Local web UI (optional)

`webapp.py` is a small, **dependency-free** (Python stdlib only) browser form for people
who'd rather not type CLI flags. It is **localhost-only** (`127.0.0.1`) — birth data never
leaves the machine — and is a thin front-end that subprocesses the same engine, distinct
from the production FastAPI `server.py`.

```bash
python webapp.py            # or ./start-web.ps1 on Windows → http://127.0.0.1:8765
```

It renders all three systems on one page and adds three conveniences:

- **Export** — one-click **JSON / Markdown / PDF**. Markdown is the engine's native report;
  PDF is printed via headless Edge/Chrome (full CJK fonts, no extra Python deps).
- **Boundary comparison (±30 min)** — recomputes the entered time at −30/−15/0/+15/+30
  minutes and highlights which fields change, making birth-time sensitivity visible at a
  glance (紫微 flips across 2-hour 時辰 boundaries; Western/HD stay stable).
- **City quick-fill** for a few common coordinates (with a reminder to verify historical DST).

---

## CLI flags reference

There are **no `required=True` flags** — argparse never errors on a missing one. Omitting `--date`/`--time`/`--tz`/`--lat`/`--lon` silently falls back to a built-in example person (`範例`, born `2000-01-01 12:00`, UTC+8, Taipei 101). So for a correct chart, supply them all.

| Flag | Type | Required for correct use? | Default | Format / rule |
|------|------|---------------------------|---------|---------------|
| `--name` | string | No (cosmetic) | `"範例"` | Free text; echoed into output only. |
| `--gender` | string | Only for 紫微 | `"女"` | Must be exactly `男` or `女` (argparse `choices`; anything else → exit `2`). |
| `--date` | string | **Yes** | falls back to `2000-01-01` | `YYYY-MM-DD`, split on `-`. No zero-pad requirement. |
| `--time` | string | **Yes** | falls back to `12:00` | `HH:MM`, 24-hour local clock time, split on `:`. |
| `--tz` | float | **Yes** | falls back to `8.0` | UTC offset including DST (Taiwan = `8`). Written to input key `tz_offset`. |
| `--lat` | float | **Yes** | falls back to `25.0330` | Latitude in decimal degrees (Western houses/Asc/MC). |
| `--lon` | float | **Yes** | falls back to `121.5654` | Longitude in decimal degrees. |
| `--target` | string | No | `"2025-01-01"` | `YYYY-MM-DD`; 紫微 luck-period reference date (運限參考日). |
| `--json` | flag | No | `False` (Markdown) | Presence → JSON mode; absence → Markdown. Takes no value. |

> The engine does **not** geocode places or look up time zones. The caller must convert place → `lat`/`lon`/`tz` themselves — and timezone/DST is the most common source of error, so verify the UTC offset that applied at the birth place and birth date.

---

## Output reference

The `--json` envelope has seven top-level keys, in this order:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Block | Summary |
|-------|---------|
| `ok` | `true` on success (`false` in the error envelope). |
| `schema_version` | `"1.0"`. |
| `input` | Echo of normalized inputs: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (note `tz_offset`, not `tz`). |
| `western` | `system` string, `ascendant`/`midheaven` position objects, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (object or `null`). |
| `meta` | `{ engine, version, ephemeris }` — all literals (`ephemeris: "Moshier"`). |

For the full field contract — every key, type, and the agent invocation protocol — see **[AGENTS.md](./AGENTS.md)**.

### Field quirks worth knowing

- **`aspects` are NOT capped in JSON.** The JSON path returns *every* detected aspect, sorted ascending by orb (tightest first). The 10-item cap exists only in the Markdown report.
- **`ziwei.horoscope` is best-effort and may be `null`.** It is wrapped in `try/except`; on any exception it serializes as `null`. When present it is `{ decadal, yearly }`. (Those sub-objects expose extra internal structure — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star`, etc. — beyond the documented placeholder.)
- **Star strings encode brightness + 四化.** Format is `name(brightness)[mutagen]`, with each part optional — e.g. `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, or plain `天機`. `adjective_stars` are plain names only (no brightness/mutagen).

---

## Accuracy tiers

Not every output carries the same confidence. Read each tier accordingly:

| Tier | What it covers | Confidence |
|------|----------------|------------|
| **Highest** | Planetary longitudes, signs, retrograde, plus 紫微 star placement / 命宮·身宮 / 五行局 — pure ephemeris and calendar math. | Astronomically/calendrically exact. |
| **High, time-dependent** | Ascendant, Midheaven, all 12 house cusps, the house each planet falls in, Human Design lines, and the 紫微 時辰 index. | Exact *given* an accurate birth time; sensitive to minutes. |
| **Verified** | 紫微斗數 star brightness — aligned to iztro's outputs. | Verified against the library. |
| **Flag boundary ±0.3°** | Any planet / gate / line sitting within ±0.3° of a boundary. | Treat as provisional and note the impact — ±0.3° can flip it across the line. |

---

## Known limitations

- **No Chiron / minor bodies.** The build uses the Moshier ephemeris (`swe.FLG_MOSEPH`, no data files), which does not provide Chiron or other minor bodies. Only the 10 classical planets plus the lunar nodes are computed.
- **紫微斗數 uses one default school.** iztro is called with fixed options (`bySolar(..., True, 'zh-TW')`); the star-placement school and 四化 are whatever iztro defaults to. If you normally use 飛星 or another school, the main structure is unchanged but some details may differ.
- **Approximate birth time degrades the time-dependent tier.** If the birth time is uncertain, the Ascendant/MC/house assignments, Human Design lines, and 時辰 — and anything derived from them — become unreliable. In that case, **treat the time-dependent fields as provisional** and consider **event-based rectification** (matching known life events to chart timing) before relying on them.

---

## Use it from an AI agent / Hermes

The intended integration model is **self-install**, not SaaS.

A user copies this repo's URL, and **their own** agent or CLI (Claude Code, Hermes, a script, etc.) clones it and runs it **locally on the user's machine**. The compute happens on the user's side. There is no hosted endpoint to call, no account, and **no SaaS integration required** — the engine is a stateless, deterministic, offline subprocess.

Because the publisher does not operate it as a network service, no §13 obligation falls on the publisher for someone else's self-install. (Separately, §13 only obligates an operator who runs a *modified* network-reachable version — not unmodified local use.)

For agents, the contract is simple: dispatch the installed `life-chart --json` wrapper when available, or fall back to the venv Python command in the repo workdir, parse stdout as JSON, branch on `ok` (and the exit code), then hand off the structured object. No cleanup needed — it is stateless. The full CLI + JSON contract lives in **[AGENTS.md](./AGENTS.md)**.

### Copy-paste setup for your AI agent

Paste this block straight into Claude Code, ChatGPT, or any coding agent — it tells the agent how to install and call the tool:

```text
Set up and use "life-chart-engine" — a CLI that computes a Western natal chart +
Human Design + Zi Wei Dou Shu (紫微斗數) from birth data.

1. Install (needs `git`, `uv`, and Node.js; if uv is missing: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Compute a chart and read stdout as JSON:
   life-chart --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>
   If life-chart is not on your PATH, use:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. Rules:
   - YOU resolve the birth city to --lat/--lon and the correct historical UTC
     offset (DST-aware). The tool does not geocode.
   - Confirm whether the birth time is exact before trusting the ascendant,
     houses, Human Design lines, or the Zi Wei hour pillar.
   - Never fabricate chart values — always call the tool.
   - Full output schema, exit codes, and the agent contract: ~/.life-chart-engine/AGENTS.md
```

---

## Licensing

This repository is licensed under **[AGPL-3.0](./LICENSE)**.

**AGPL-3.0 in plain English.** It is the GNU GPL-3.0 (a strong copyleft license: if you distribute the software, you must release your complete corresponding source under the same license) **plus one extra clause, Section 13**. §13 closes the "SaaS loophole": beyond the GPL's *distribution* trigger, it adds that if you *modify* the program and let users interact with your modified version over a network, you must offer those remote users your corresponding source. (Running an unmodified upstream as a network service does not by itself trigger §13.) AGPL is reciprocal but not boundlessly viral — it only reaches code that is a derivative of, or linked with, the AGPL code.

**Why this repo is AGPL.** The engine links **Swiss Ephemeris** (via `pyswisseph`) for planetary positions and house cusps. Astrodienst **dual-licenses** Swiss Ephemeris as **AGPL-3.0 OR a commercial license**, and its code cannot be relicensed as anything more permissive. Because AGPL is copyleft and this project links it, the whole combined work must be AGPL. (`iztro` is MIT and imposes no copyleft; Swiss Ephemeris is the only component forcing AGPL here.)

**What it means in practice.**

| You do | AGPL obligation |
|--------|-----------------|
| **Self-install** (run it locally for yourself) | §13 is *not* triggered — there are no remote users to serve, and you already have the source. Clean. |
| **Run a *modified* version as a network service** | §13 *is* triggered — you must offer those remote users the complete corresponding source of your deployed version, under AGPL, including your modifications. Note: §13's source-offer duty is conditioned on modification — running the unmodified upstream as a network service does not by itself trigger §13, though the source is already public anyway. |

**Your three options** if the network-source obligation does not fit your use case:

1. **Keep AGPL** — publish your complete corresponding source (including modifications) to anyone who uses it, including over a network per §13. Free, no negotiation.
2. **Buy a Swiss Ephemeris commercial license from [Astrodienst](https://www.astro.com/swisseph/)** — this lifts the AGPL obligation for the Swiss Ephemeris portion, letting you relicense your own code and ship/host a closed build. (This is Astrodienst's dual-licensing model.)
3. **Swap the ephemeris** — replace `pyswisseph` with a permissively licensed astronomy source (for example **Skyfield (MIT)** plus the public-domain **JPL DE440** ephemeris — illustrative alternatives, not the only option). With Swiss Ephemeris gone, the remaining stack (iztro MIT, plus the MPL-2.0/MIT/Apache deps) no longer forces AGPL and the whole repo could be MIT. This is real engineering effort: you must reimplement everything currently sourced from Swiss Ephemeris — planetary longitudes, retrograde flags, Asc/MC, Placidus house cusps, and the inputs to the Human Design 88° design solver.

See **[CREDITS.md](./CREDITS.md)** for full attribution and per-dependency licenses.

---

## FAQ

**Can I enter a lunar date?**
No. Inputs are a Gregorian solar date (`--date YYYY-MM-DD`) and clock time (`--time HH:MM`). If you only have a lunar date, convert it first. 紫微斗數 is computed via iztro's solar entry point (`bySolar`).

**My birth time is only approximate — is that a problem?**
The planetary positions are fine, but the Ascendant, Midheaven, house cusps, the house each planet sits in, Human Design lines, and the 時辰 are all time-sensitive. Treat those as provisional and consider event-based rectification before relying on them.

**Where's Chiron / asteroids / minor bodies?**
Not included. The Moshier ephemeris used here does not provide them; only the 10 classical planets and the lunar nodes are computed.

**Which 紫微斗數 school does it use?**
The default school as implemented by iztro (`bySolar(..., True, 'zh-TW')`). The school is not user-selectable.

**Does it phone home / use the network?**
No. The engine is fully offline — no telemetry, no network calls, no side effects. It is a stateless, deterministic one-shot subprocess.

**Can I use it inside a closed-source product?**
Under AGPL-3.0, yes for private/local use. Distributing a build triggers the GPL conveying/source obligations, and network-serving a *modified* build triggers AGPL §13 — either way you must offer corresponding source. To go fully closed-source, either buy a Swiss Ephemeris commercial license from Astrodienst or swap the ephemeris to Skyfield + JPL DE440 (see [Licensing](#licensing)).

---

## Disclaimer

`life-chart-engine` is an **interpretive self-awareness framework, not prediction or fatalism**. The outputs are structured reference points for reflection — they do not foretell events and do not determine outcomes. Use them as calibration, with your own lived experience as the final authority. Nothing here is medical, legal, psychological, or financial advice. For decisions in those domains, consult a qualified professional.

---

## Credits & License

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG, dual-licensed AGPL-3.0 / commercial (<https://www.astro.com/swisseph/>).
- **iztro** — MIT, for 紫微斗數.
- Full attribution: **[CREDITS.md](./CREDITS.md)**.
- **License:** [AGPL-3.0](./LICENSE).
- **Agent / JSON contract:** [AGENTS.md](./AGENTS.md).
