# Engine Polish & Funnel Readiness — SPEC

> `/go` 唯一輸入。本 spec 只含公開安全內容（本 repo 為公開 MIT repo）；
> 商業／行銷細節一律在私有 workspace 文件（見 Further Notes），不進本 repo。
> rev 4.1：吸收 rounds 1–4 交叉驗證全部發現（round 4 Agent 判定 0 🔴 implementation-ready，
> 其 9 🟡 已摺入）。關鍵定案：支援年份窗＝保守驗證窗 1900–2100（三系統交集）；CI 佈線
> 各 slice 自帶；Markdown 錯誤時 stdout 全緩衝；golden fixtures 於 Linux（repo Docker 映像）
> 擷取、byte 斷言僅 Linux 跑。

---

## Problem Statement

- CLI 使用者漏帶任一出生 flag 時，引擎默默用內建範例人出盤並 exit 0——使用者（尤其是 AI agent）拿到「看似合理但完全錯誤」的盤面而不自知。這違背本引擎「寧可報錯、不出錯盤」的信任承諾。
- 同一信任缺口的變體：超出星曆／農曆資料可信範圍的年份（如 1700 年）也會默默出全盤（紫微 vendored 農曆表僅涵蓋 1900–2100，實測 1700/2199 無任何錯誤）。
- Agent 在 `--json` 模式餵入壞格式日期時會收到 raw Python traceback（`_parse_args` 的 `ValueError` 早於 try/except），違反「stdout 恰好一個 JSON object」的自家契約。
- HTTP 面（`server.py`）對越界值（tz=20、lat=95）與非有限值不做範圍檢查——越界值回 200 帶錯盤或 500。
- Agent 作者照 `AGENTS.md` 寫 parser，卻遇到文件沒寫的實際欄位（紫微 horoscope 的 `stars`、`yearlyDecStar`）；且 AGENTS.md 描述的「horoscope 失敗回 null」與實際 all-or-nothing 行為不符。
- 18 個翻譯 README 的 horoscope 物件描述停在舊版形狀（缺 `age`／小限）。
- 想試用的人必須 git clone＋跑安裝腳本；沒有 `pip install`／`uvx` 路徑、沒有 PyPI 套件、CI badge、demo GIF。
- 沒有 MCP server，Claude 等 MCP 客戶端無法原生呼叫。
- `webapp.py`（719 行）缺 HTTP 層功能測試（現有僅靜態 DOM grep）；空欄位會以空字串傳給 CLI，複製同一個範例人信任缺口。
- README 沒有任何指向 hosted web 版的入口。

## Solution

- 漏 flag、壞格式、越界、年份窗外、非法組合一律在 argparse 層擋下：exit 2、usage 進 stderr、stdout 空。要範例盤改用顯式 `--example`。HTTP 面同步 400 hardening。
- 支援年份窗＝**1900-01-01 … 2100-12-31**（出生日與 `--target` 同窗）：iztro 農曆表（1900–2100）⊂ astronomy-engine（1700–2200）的交集；HD design chart 往前 ~88–100 天採樣自 1900 年界內出發仍落在 astronomy-engine 範圍，無邊界破口。
- `AGENTS.md` 補齊實際欄位（含不對稱）＋錯誤傳輸矩陣＋fail-closed 認證行為＋horoscope 失敗語意修正；18 譯本同步＋guard test。
- `pyproject.toml` 補 `[project]`＋三個 entry points；核心依賴只有 astronomy-engine；trusted publishing；CI badge＋vhs demo；**CI 佈線由引入該需求的 slice 自帶**。
- 新增 stdio MCP server（`compute_chart`，thin wrapper over `build_json()`）；三面共用 `validation.py` 與 envelope serializer。
- `webapp.py` 補功能測試、空欄位友善錯誤、`LIFE_VENV`、macOS/Linux 瀏覽器探測。
- README（en/zh-TW/zh-CN）加「Hosted version」段連 https://life.aicycle.cc。

## User Stories

1. As a CLI user, I want omitting any of `--date/--time/--tz/--lat/--lon/--gender` to fail at the argparse layer (exit 2, usage on stderr, empty stdout) listing the missing flags, so that I can never mistake the built-in example person's chart for my own.
2. As an AI agent, I want `--json` mode to emit either exactly one JSON object on stdout (success, or `{"ok": false, ...}` for runtime errors, exit 1) or nothing on stdout for argument errors (exit 2), so that I can parse stdout unconditionally.
3. As a docs/demo author, I want an explicit `--example` flag that reproduces the historical example-person chart byte-for-byte against golden fixtures captured from the pre-change CLI **inside the repo's Docker image (Linux, same platform family as CI)**, both JSON and Markdown modes — byte-identity asserted on Linux only (`skipif` on other platforms, which fall back to the suite's existing tolerance comparisons) — so that existing tutorials keep a supported path without cross-platform libm flakes.
4. As a CLI user, I want `--example` to be mutually exclusive with birth flags (exit 2) but combinable with non-birth flags (`--target`, `--name`, `--ziwei-day-divide`, `--json`), so that demo semantics are unambiguous.
5. As a CLI user passing a malformed or out-of-window value (`--date 1990-13-45`／非閏年 02-29／`--time 25:99`／`--target 2500-01-01`／出生或 target 年份在 1900–2100 之外／tz、lat、lon 越界或非有限），I want an exit-2 usage error naming the bad flag, so that garbage or unverifiable input is rejected before any computation. Unpadded but valid forms (`1990-6-15`, `8:30`, and single-digit minutes like `8:5` — int-parse semantics) stay accepted and are normalized, matching current CLI/HTTP behavior.
6. As an agent author, I want `AGENTS.md` to document every field the engine actually emits — `stars` only under `decadal`/`yearly`, `yearlyDecStar` only under `yearly` — and to correct the stale "horoscope becomes null on failure" statement to the actual all-or-nothing loud failure, so that the contract matches reality.
7. As a non-English reader, I want all 18 translated READMEs to describe the same horoscope object shape (`{ decadal, yearly, age }`) and the same required-flags/`--example` semantics as the English README, so that translated docs are trustworthy.
8. As a maintainer, I want a guard test asserting the exact 18-file translation set each contains the pinned language-independent literals, so that translation staleness is caught by CI.
9. As a Python developer, I want `pip install life-chart-engine`, `uvx life-chart-engine --example --json`, and `uvx --from life-chart-engine life-chart --example --json` to all work (both forms verified post-publication), so that trying the engine costs one line — with the README install section presenting `uvx` as the primary path and noting the CPython 3.12 requirement next to the bare `pip install` line (system 3.13/3.14 users are rejected by requires-python; uv auto-provisions 3.12).
10. As a packager, I want the wheel to install import package `life_chart_engine` (not top-level `scripts`) and include the Node sidecar files inside the package, so that 紫微 works from an installed package without namespace pollution.
11. As a caller without a working Node, I want every surface to fail loudly with no partial chart anywhere: `--json` → `{"ok": false, "error": ...Node.js >= 18...}` exit 1 with only that envelope on stdout; Markdown mode → **stdout fully buffered and suppressed on failure**（不留已印出的 western/HD 段落）, one clean stderr line, exit 1; HTTP → 500 with the same message; MCP → `isError: true`. (Node ≥ 18 is the documented supported/tested runtime — CI runs an 18/24 matrix; no active version probing.)
12. As a maintainer, I want a release-triggered publish workflow (`on: release: types: [published]`, separate build-artifact job → OIDC publish job with `permissions: id-token: write`), with the build＋`twine check` dry-run running in `qa-gate.yml` on every PR and a static workflow contract test, so that publishing is safe and drafts can't double-fire.
13. As a repo visitor, I want a CI status badge (workflow runs on push to main) and a terminal demo GIF at the top of the README, so that I can judge health and output in ten seconds.
14. As an MCP client, I want a `compute_chart` tool whose **inputSchema is pinned to the HTTP `/chart` body fields**（date/time/tz/lat/lon/gender 必填＋name/target/ziwei_day_divide 選填）and whose result is a single text content equal to the shared envelope serializer's output (CLI `--json` stdout minus trailing newline), so that agents call charts natively with a stable schema.
15. As an MCP client sending invalid input, I want a structured tool error (`isError: true`) — not a crashed server — so that my session survives bad calls.
16. As an operator, I want the MCP server offline/stateless (stdio only), verified by an in-process Python socket guard **plus a static no-network assertion over `scripts/ziwei_iztro.cjs` and `vendor/iztro.cjs`**（該 guard 的邊界文件化：Python socket patch 管不到 Node 子行程，故以 sidecar 原始碼靜態斷言補上）, so that the determinism promise holds in MCP mode.
17. As a maintainer, I want one packaged validation module shared by CLI/HTTP/MCP, where `test_server.py`-covered behavior stays unchanged and the new rejections (range/non-finite/year-window) are a deliberate documented HTTP 400 hardening with exact status/detail tests, so that input rules exist in exactly one place.
18. As a maintainer, I want webapp functional tests via an in-process server factory (actual bound port) driving `/api/chart` — parity with CLI `--json` defined as **parsed-JSON semantic equality**（webapp 現行 compact 重序列化維持，HTTP 介面不變）— and the Markdown export endpoint, so that web-UI regressions are caught at API level.
19. As a webapp user submitting an empty form field, I want a clean `ok:false` error message (not raw argparse usage text), so that the web UI doesn't leak internals.
20. As a maintainer, I want the PDF-export path covered by a mocked `%PDF` test plus a real-browser test that **must run against the discovered headless browser when one exists**（asserting `%PDF` bytes）and skips only when none is discovered — with discovery extended to macOS and Linux — so that the real path is actually exercised on dev machines.
21. As a local developer, I want `webapp.py` to respect `LIFE_VENV` (a venv **directory**; `bin/python` on Unix, `Scripts\python.exe` on Windows), with the in-process factory **raising a clear startup error when the resolved executable is missing**, so that misconfiguration fails loudly at boot, not per-request.
22. As a curious non-technical visitor, I want a short "Hosted version" section in README.md, README.zh-TW.md, and README.zh-CN.md linking **https://life.aicycle.cc** and wording it as a separate maintained hosted product built on this engine（並同步修正現有 README 中「不存在 hosted endpoint/SaaS」的句子，避免自相矛盾）, so that the main audiences get an honest next step.
23. As a CI consumer, I want every new test wired into qa-gate **by the slice that introduces it**（含該 slice 的 install 步驟與 `qa_gate_workflow_test.py` regex 同步），so that CI is green after every slice merges in DAG order.

## Modules

| Module | 職責（一句） | 公開介面（窄） | 新建/修改 |
|---|---|---|---|
| `scripts/chart_engine.py` | argparse 驗證、`--example`、`main(argv=None)`；Markdown 輸出改全緩衝（錯誤時 stdout 無部分盤）；`ziwei()` Node 失敗 → loud error；輸出走 serializer | CLI flags＋`main(argv=None)`＋`to_json_text(envelope)` | 修改 |
| `scripts/validation.py` | 唯一輸入驗證：**raw schema**（date "YYYY-M-D" 可未補零、time "H:M"（時、分皆可未補零，int-parse 語意）、tz/lat/lon 數值、gender 男/女、選填 name/target/ziwei_day_divide）→ **normalized schema**（正規化整數 tuple／浮點；錯誤丟 `ValueError` 帶欄位名；**name/target 的預設值自持於本模組**（值不變：範例/2025-01-01 語意照舊），server 不再回讀 `chart_engine.INPUT`，避免循環 import）；範圍：tz∈[-12,14]、lat∈[-90,90]、lon∈[-180,180]、有限值、真實日曆日、**出生日與 target 年份窗 1900–2100** | `validate_input(raw: dict) -> normalized dict` | 新建 |
| `server.py` | `_engine_input` 改走 `validation.py`；`test_server.py` 既有覆蓋行為不變；越界/非有限/窗外 → 400（hardening） | 既有 HTTP 介面＋新 400 案例 | 修改 |
| `scripts/mcp_server.py` | stdio MCP server，`compute_chart`（inputSchema＝/chart body 欄位）wrap `build_json()` | console script `life-chart-mcp`（無 extra → 安裝提示，非 raw ImportError） | 新建 |
| `scripts/ziwei_iztro.cjs` | vendored bundle 解析順序 `__dirname/vendor/` → `__dirname/../vendor/` | stdin/stdout JSON 不變 | 修改 |
| `pyproject.toml` | `[project]`（deps＝astronomy-engine only）、hatchling sources 映射＋vendor force-include、entry points ×3、`[mcp]` extra（`mcp` 以 `==` 精確 pin，版本記入 RELEASING.md） | entry points ×3 | 修改 |
| `.github/workflows/qa-gate.yml` | 各 slice 自帶佈線：Slice 4 加 `pip install build twine==<pin>`＋build/`twine check` dry-run step；Slice 5 加 Node 18/24 matrix；Slice 6 加 `pip install -e ".[mcp]"`；Slice 8 加 `push: branches [main]`；每次同步 `qa_gate_workflow_test.py` regex | 既有 CI 介面 | 修改（多 slice） |
| `.github/workflows/publish.yml` | `on: release: types: [published]`；build-artifact job → OIDC publish job（`id-token: write`、artifact 傳遞）；靜態契約測試 | GitHub release 事件 | 新建 |
| `webapp.py` | `LIFE_VENV`（目錄語意；缺 executable → factory 啟動即錯）；in-process `create_server()` factory（回報實際 bound port；對外 HTTP 介面不變）；`find_browser()` 補 macOS＋Linux；空欄位/exit-2 → 友善 `ok:false` | 既有 HTTP 介面不變 | 修改 |
| `AGENTS.md`＋`README*.md` | 契約補 drift＋錯誤傳輸矩陣＋fail-closed 認證（ENGINE_API_KEY／ENGINE_ALLOW_OPEN／503）＋horoscope 失敗語意修正＋年份窗與 per-system 範圍＋Node 支援聲明＋`~/.local/bin` 共存註記；badge、demo、hosted 段（en/zh-TW/zh-CN，含矛盾句修正）；18 譯本同步 | 文件 | 修改 |
| `docs/demo.tape`＋`docs/RELEASING.md` | vhs 腳本＋發佈步驟（pending publisher、mcp pin 版本記錄、`~/.local/bin` 共存） | `vhs docs/demo.tape` | 新建 |
| `tests/`（新檔 ×4＋既有 ×2） | 見 Testing Decisions；`test_mcp_server.py` 以 `pytest.importorskip("mcp")` 保護本地無 extra 環境 | pytest／bash | 新建＋修改 |

## Implementation Decisions

- Schema: 無 DB。JSON 輸出形狀不變、`schema_version` 維持 `"1.1"`；`meta.version` 維持 `"1.0"`（區別文件化）。無 Node／sidecar 失敗 → 整包 loud error，不做 per-system 部分結果。
- **支援年份窗＝1900-01-01 … 2100-12-31（出生日與 target 同窗）**：依據＝**保守驗證窗**：iztro 文件宣稱支援範圍 1900–2100（vendored bundle 為 lunar-typescript 演算法實作、無硬表界，故窗外會默默出盤而無任何錯誤——round-3/4 實測 1600/1700/2199 皆如此，必須在驗證層擋）∩ astronomy-engine 精度聲明 1700–2200；AGENTS.md/README 措辭寫「文件宣稱支援範圍／保守驗證窗」，不寫「農曆表界」（bundle 內無此表，勿載入不可驗證的機制宣稱）；HD design chart 前推 ~88–100 天與速度取樣 ±0.5 天自窗界出發仍在 astronomy-engine 範圍內，無邊界破口。窗界端點測試四件組（1899-12-31 拒／1900-01-01 收／2100-12-31 收／2101-01-01 拒）＋target 同組。`AGENTS.md`／README known limitations 記 per-system 範圍。
- **Envelope serializer 單一來源**：`to_json_text(envelope)`；CLI `--json` stdout＝serializer＋trailing newline；MCP text content＝serializer（無 newline）；webapp `/api/chart` 維持現行 compact 重序列化（parity＝parsed-JSON 語意等價，非 byte）。
- API contract:
  - CLI：單一錯誤通道（argparse `parser.error()`：exit 2、stderr usage、stdout 空）；**未補零格式維持接受並正規化**（`1990-6-15`、`8:30`——與現行 CLI/HTTP 行為一致，不引入 exact-format 拒絕）；執行期錯誤：`--json` → envelope exit 1；**Markdown → 全緩衝、失敗時 stdout 空**、stderr 一行（Node 案例含 "Node.js >= 18"）、exit 1。`--gender` 必填。
  - HTTP：`test_server.py` 既有覆蓋行為不變；400 hardening（NaN/±inf/越界/年份窗外）；**Node 失敗 → 500＋含 "Node.js >= 18" 的 error envelope（有測試）**；AGENTS.md 補 fail-closed 認證行為（`ENGINE_API_KEY` 未設＋`ENGINE_ALLOW_OPEN≠1` → 503）。
  - MCP：stdio；`compute_chart` inputSchema pin＝/chart body 欄位（必填 date/time/tz/lat/lon/gender；選填 name/target/ziwei_day_divide），tools/list 測試斷言欄位名與必填性；成功＝單一 text content（serializer）；驗證失敗與 runtime 失敗＝`isError: true`，server 續存。
  - **錯誤傳輸矩陣**（寫進 AGENTS.md＋parity test）：驗證錯 → CLI exit 2／HTTP 400／MCP isError；runtime 錯（Node、高緯度、timeout）→ CLI exit 1／HTTP 500／MCP isError。parity＝「驗證決策」一致（同輸入三面同判），載體各異。
- 架構決策:
  - MCP thin wrapper over `build_json()`；`mcp` SDK pin＝**`mcp==1.28.1`**（2026-07-14 PyPI 現行穩定版；pyproject 與 `docs/RELEASING.md` 同值）；`life-chart-mcp` 常駐 scripts，無 extra 時給安裝提示。
  - 打包佈局（定案）：repo 目錄不動；wheel import package＝`life_chart_engine`（hatchling sources 映射）；`scripts/__init__.py`＋相對 import；vendor force-include；core deps＝astronomy-engine only；版本 1.1.0；requires-python `>=3.12,<3.13`。Node ≥ 18 supported/tested（**CI node 18/24 matrix 佐證**）；`~/.local/bin/life-chart` 與 install.sh symlink 共存註記。
  - 發佈：`publish.yml` `on: release: types: [published]`；兩 job（build artifact → OIDC publish，`permissions: id-token: write`，artifact upload/download 傳遞）；PR 側 build＋`twine check`（twine 以固定版本裝進 qa-gate）在 qa-gate 跑；publish.yml 有靜態契約測試（斷言 trigger types、permissions、job 結構）。
  - **CI 佈線歸屬**：引入新測試/工具需求的 slice 自帶 qa-gate 修改＋`qa_gate_workflow_test.py` regex 同步（見 Modules 表），確保 DAG 順序下每個 slice 合併後 CI 皆綠；`test_mcp_server.py` 用 `importorskip` 防本地無 extra 紅燈。
- 第三方/整合: `mcp` SDK（MIT，`mcp==1.28.1`）、hatchling、twine（CI 固定版本）、vhs（開發機）。禁止 AGPL／swisseph。
- 安全/權限: 無 secrets；no-network 雙層證明——Python in-process socket guard＋sidecar 原始碼靜態斷言（`ziwei_iztro.cjs`＋`vendor/iztro.cjs` 無 `require('http`/`require('net`/`fetch(`/`XMLHttpRequest`），並文件化 Python guard 管不到 Node 子行程的邊界；OIDC 不存 token；GIF/tape 只用 `--example`。
- 邊界/效能: Node 缺席/失敗/timeout 收斂單一 loud-error 路徑（PATH 遮蔽/假 node 注入）；PDF：發現瀏覽器時必跑真瀏覽器 `%PDF` 測試，僅無瀏覽器 skip；translations guard 用 pinned literal＋恰好 18 檔。

## Testing Decisions

| Module | 要測? | 測什麼外部行為 | Prior art |
|---|---|---|---|
| CLI arg 層 | ✅ | 先擷取 golden fixtures；漏 flag／壞格式（未補零合法形式仍收）／年份窗四件組（出生＋target）／`--example`×出生 flag／越界 → exit 2 stdout 空；`--example` 與 golden byte-identical（JSON＋Markdown）；`--json` runtime → envelope exit 1；**Markdown runtime → stdout 空**（無部分盤）＋stderr 一行；`test_wrapper.sh` 補 `--gender` | `tests/test_engine_astronomy_contract.py`、`tests/test_wrapper.sh` |
| `scripts/validation.py` | ✅ | raw→normalized 對照表（未補零正規化、tz/lat/lon 邊界與越界、NaN/±inf、真實日曆日、1900–2100 四件組×出生/target）；三面「驗證決策」parity | `tests/test_server.py` |
| server.py | ✅ | 既有斷言全綠（不改弱）；400 hardening（含年份窗）＋detail；**Node 失敗 → 500＋"Node.js >= 18" envelope** | `tests/test_server.py` |
| MCP server | ✅ | in-process initialize→tools/list（**斷言 inputSchema 欄位名＋必填性**）→tools/call＝serializer byte 等價；壞輸入/runtime → isError、續存；socket guard＋sidecar 靜態 no-network 斷言；installed-wheel checkout 外 `life-chart-mcp` 冒煙＋無 extra 安裝提示；`importorskip("mcp")` | `tests/test_server.py`、no-network guard |
| Node 缺席路徑 | ✅ | PATH 遮蔽／假 node／timeout → `--json` envelope、Markdown stdout 空＋stderr、HTTP 500，訊息一致含 "Node.js >= 18" | `tests/test_ziwei_iztro.py` |
| webapp | ✅ | in-process factory（實際 bound port；`LIFE_VENV` 缺 executable → 啟動即錯）；GET `/` 200；POST `/api/chart` parsed-JSON 語意等價 CLI `--json`＋content-type；MD 匯出；空欄位 → 友善 `ok:false`；PDF：mocked `%PDF`＋發現瀏覽器必跑真測試（僅無瀏覽器 skip） | `tests/test_server.py`、`tests/test_webapp_dom_safety.py` |
| 打包 | ✅ | `python -m build`；乾淨 venv＋checkout 外兩 entry points `--example --json`；import package 名；vendor 在 wheel；`.cjs` 雙路徑解析 | `tests/test_wrapper.sh` |
| README 譯本 sync | ✅ | 恰好 18 檔＋pinned literals | `tests/test_review_log.py` |
| workflows 靜態契約 | ✅ | qa-gate：install 步驟（build、twine==pin、`.[mcp]`）＋node matrix＋push trigger regex；publish.yml：`types: [published]`＋`id-token: write`＋兩 job 結構 | `.github/scripts/qa_gate_workflow_test.py` |

## Vertical Slices

### Slice 1 — CLI 信任修補（golden fixtures→單一錯誤通道＋--example＋main()）
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #1, #2, #3, #4, #5
- **Acceptance criteria**:
  - [ ] 第一個 commit 先擷取 pre-change golden fixtures（無 flag JSON＋Markdown stdout 各一）
  - [ ] 漏任一必填 flag（date/time/tz/lat/lon/gender）→ exit 2、stderr 列缺項、stdout 空（含 `--json`）
  - [ ] 壞格式/越界/**1900–2100 窗外（出生＋target 各四件組）** → exit 2、stdout 空；未補零合法形式（`1990-6-15`、`8:30`）仍接受並正規化
  - [ ] `--example` 與出生 flags 互斥（exit 2）；與 `--target/--name/--ziwei-day-divide/--json` 可併用；預設下與 golden byte-identical（兩模式）
  - [ ] `main(argv=None)`＋`to_json_text(envelope)`；**Markdown 輸出全緩衝**（本 slice 先落緩衝結構，錯誤路徑 Slice 5 驗收）
  - [ ] 驗證邏輯在新建 `scripts/validation.py`（raw→normalized 兩 schema 如 Modules 表）
  - [ ] 既有 `test_cli_exit_codes_fallback_and_deterministic_output` 改寫為 `--example`；`tests/test_wrapper.sh` 補 `--gender`；全部測試綠
  - [ ] `AGENTS.md`＋`README.md` flags 表、exit code 段、年份窗、breaking 說明同步

### Slice 2 — 驗證單一來源＋HTTP 400 hardening＋parity
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #17
- **Acceptance criteria**:
  - [ ] `server.py` `_engine_input` 改走 `validation.py`；`tests/test_server.py` 既有斷言全綠（不改弱）
  - [ ] 400 hardening 測試：NaN、±inf、tz=20、lat=95、lon=200、年份窗外（出生＋target）→ 400＋detail
  - [ ] `validation.py` raw→normalized 對照＋邊界值表測試
  - [ ] CLI/HTTP「驗證決策 parity」測試；`AGENTS.md` 記載 hardening＋錯誤傳輸矩陣＋**fail-closed 認證行為（ENGINE_API_KEY／ENGINE_ALLOW_OPEN／503）**

### Slice 3 — 契約補齊與 18 譯本同步（含 guard test）
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #6, #7, #8
- **Acceptance criteria**:
  - [ ] `AGENTS.md`：`stars`（限 decadal/yearly）、`yearlyDecStar`（限 yearly）＋**「horoscope 失敗回 null」句改為 all-or-nothing loud failure**；schema_version 1.1；`meta.version` 區別一句話
  - [ ] 18 譯本：horoscope `{ decadal, yearly, age }`＋必填 flags/`--example` 語意同步
  - [ ] `tests/test_readme_sync.py`：恰好 18 檔＋pinned 語言無關 literals
  - [ ] 本 slice 無新 CI 需求（pytest 自動蒐集）；CI 綠

### Slice 4 — 打包（wheel／entry points／依賴切分）＋自帶 CI 佈線
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #9, #10, #23
- **Acceptance criteria**:
  - [ ] `pyproject.toml`：`[project]`（deps＝astronomy-engine only、1.1.0、requires-python `>=3.12,<3.13`）＋hatchling sources 映射＋console scripts `life-chart`/`life-chart-engine`（**`life-chart-mcp` entry point 隨 Slice 6 一併落 pyproject**，避免 dangling 指向未建模組）＋`[mcp]` extra（**`mcp==1.28.1`**——2026-07-14 PyPI 現行穩定版；同一版本值寫入 pyproject 與 docs/RELEASING.md）
  - [ ] wheel import package `life_chart_engine`；`scripts/__init__.py`＋相對 import；checkout 與 wheel 雙載入
  - [ ] vendor force-include；`.cjs` 雙路徑解析有測試
  - [ ] 乾淨 venv＋checkout 外：兩 entry points `--example --json` 合法 JSON（自動化）
  - [ ] **qa-gate 佈線（本 slice 自帶）**：`pip install build twine==<pin>`＋build＋`twine check` dry-run step；`qa_gate_workflow_test.py` regex 同步；CI 綠
  - [ ] `install.sh`／`bin/life-chart`／Dockerfile 不受影響；README/RELEASING 加 `~/.local/bin` 共存註記（RELEASING 檔 Slice 9 建，README 註記此處落）

### Slice 5 — 無 Node 的 loud-error 契約（CLI＋HTTP）＋Node matrix
- **Type**: AFK
- **Blocked by**: Slice 4
- **User stories**: #11, #23
- **Acceptance criteria**:
  - [ ] 無 node（PATH 遮蔽）：`--json` → 整包 envelope exit 1；**Markdown → stdout 空**（緩衝丟棄）＋stderr 一行含 "Node.js >= 18"、無 traceback
  - [ ] 假 node 非零退出／timeout 收斂同路徑（注入式測試）
  - [ ] **HTTP `/chart`（open 模式）Node 失敗 → 500＋含 "Node.js >= 18" 的 envelope（測試）**
  - [ ] **qa-gate node-version matrix [18, 24]（本 slice 自帶＋regex 同步）**；CI 綠
  - [ ] `AGENTS.md`＋README 明載 Node ≥ 18 supported/tested（pip 情境含安裝指引）

### Slice 6 — MCP server＋自帶 CI 佈線
- **Type**: AFK
- **Blocked by**: Slice 4
- **User stories**: #14, #15, #16, #23
- **Acceptance criteria**:
  - [ ] `life-chart-mcp` entry point 於本 slice 落入 pyproject；`[mcp]` extra 安裝後可啟動；無 extra → 安裝提示（非 raw ImportError）
  - [ ] in-process 測試：initialize → tools/list（**斷言 compute_chart inputSchema 欄位名＋必填性＝/chart body**）→ tools/call 回單一 text content＝serializer 輸出（byte 級）
  - [ ] 壞輸入／runtime 錯誤 → `isError: true`；同 session 再次成功呼叫
  - [ ] no-network：in-process guard 改 patch `socket.create_connection`＋`socket.getaddrinfo`（不可整段 patch `socket.socket`——asyncio event loop 自身的 `socketpair` self-pipe 會被誤殺），且僅包 tools/call 計算路徑＋**sidecar 靜態斷言（兩個 .cjs 無網路原語）**；邊界說明入 AGENTS.md
  - [ ] installed-wheel＋checkout 外 `life-chart-mcp` 冒煙
  - [ ] **qa-gate 佈線（本 slice 自帶）**：`pip install -e ".[mcp]"` step＋regex 同步；`test_mcp_server.py` 用 `importorskip("mcp")`；CI 綠
  - [ ] `AGENTS.md`＋`README.md` 增 MCP 使用段（Claude Desktop/Code 設定範例）

### Slice 7 — webapp 修補與功能測試
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #18, #19, #20, #21
- **Acceptance criteria**:
  - [ ] `webapp.py`：in-process `create_server()` factory（回報實際 bound port）；`LIFE_VENV` 目錄語意＋缺 executable → factory 啟動即錯（清楚訊息）；`find_browser()` 補 macOS＋Linux；空欄位/exit-2 → 友善 `ok:false`；對外 HTTP 介面不變
  - [ ] `tests/test_webapp.py`：GET `/` 200；POST `/api/chart` parsed-JSON 語意等價 CLI＋content-type；MD 匯出；空 `--date` → 友善錯誤
  - [ ] PDF：mocked `%PDF`＋**發現瀏覽器時必跑真瀏覽器測試斷言 `%PDF` bytes**（僅無瀏覽器 skip）
  - [ ] 本地（macOS、LIFE_VENV）與 CI 皆綠

### Slice 8 — README 門面＋badge＋demo＋hosted
- **Type**: AFK
- **Blocked by**: Slice 1, Slice 4, Slice 6
- **User stories**: #13, #22, #23
- **Acceptance criteria**:
  - [ ] qa-gate 加 `push: branches: [main]`（badge 需 default-branch run）；`concurrency.cancel-in-progress` 改僅 PR 生效（`${{ github.event_name == 'pull_request' }}`，避免連續 merge 把 main run 取消成非綠 badge）；regex 同步；CI 綠
  - [ ] README 安裝段：uvx 列首選路徑、`pip install` 旁註明 CPython 3.12 需求
  - [ ] README.md 頂部 CI badge（qa-gate、default branch）
  - [ ] `docs/demo.tape` 入 repo；GIF 生成嵌入 README（vhs；受阻列 HITL follow-up，不阻塞其餘 AC）
  - [ ] 「Hosted version」段落進 README.md、README.zh-TW.md、README.zh-CN.md：**連結 https://life.aicycle.cc**、措辭為「基於本引擎的獨立 hosted 產品」、不含價格；**同步修正三檔中「不存在 hosted endpoint／SaaS」的既有句子**；其餘 15 譯本列 follow-up
- **註**：GIF 為本 slice 唯一 best-effort 項。

### Slice 9 — 發佈流程（publish workflow＋RELEASING）
- **Type**: AFK
- **Blocked by**: Slice 4
- **User stories**: #12
- **Acceptance criteria**:
  - [ ] `.github/workflows/publish.yml`：`on: release: types: [published]`；build-artifact job（build＋twine check＋upload artifact）→ publish job（download artifact、`permissions: id-token: write`、OIDC trusted publishing）
  - [ ] publish.yml 靜態契約測試（trigger types、permissions、兩 job 結構）**檔案落 `tests/`**（qa-gate pytest 僅蒐集 `.github/scripts/qa_gate_workflow_test.py` 與 `tests/`，放 `.github/scripts/` 不會被跑）
  - [ ] `docs/RELEASING.md`：版本 bump→tag→release→pending publisher 註冊；記錄 `mcp` pin 版本；`~/.local/bin` 共存注意

### Slice 10 — PyPI 首發（HITL）
- **Type**: HITL
- **Blocked by**: Slice 5, Slice 6, Slice 9
- **User stories**: #9, #12
- **Acceptance criteria**:
  - [ ] 使用者照 `docs/RELEASING.md` 完成 PyPI pending publisher 註冊
  - [ ] 打 v1.1.0 release → publish workflow 綠 → 乾淨機器實跑 `uvx life-chart-engine --example --json` **與** `uvx --from life-chart-engine life-chart --example --json` 皆成功

## Out of Scope

- 引擎不加 geocoding／時區查找。
- 不加 Chiron/小行星、不開放紫微流派選擇。
- 不引入 AGPL/swisseph。
- 不做 per-system 部分結果／partial envelope（任何模式，含 Markdown）。
- 1900–2100 窗外的計算支援（窗外一律驗證錯誤；擴窗需對權威農曆源驗證邊緣 fixtures，另開 issue）。
- 不在本 repo 放 hosted 產品的價格、漏斗、行銷、分析內容。
- life-web 程式變更不在本 spec slices 內（並行工作線，見 Further Notes）。
- 廣告投放執行、社群發文執行。
- py3.13+、其餘 15 譯本 hosted 段、Node 版本主動探測、Linux golden fixtures（byte-identity guard 目前 `golden_platform.txt`=darwin，Linux CI 上不執行）（follow-up）。

## Further Notes

- **公私分離鐵則**：本 repo 公開；商業／行銷內容一律在私有 workspace，不進本 repo。
- **並行工作線**：hosted 產品側工作於私有 workspace 追蹤，不由本 repo 的 /go 執行。
- **server.py 註記**：變更＝驗證搬遷＋刻意 400 hardening＋Node-500 測試；Hetzner 部署不受影響。
- **發佈順序約束**：HN/Reddit「一行安裝」宣稱以 Slice 10 完成為前提。
- 已知風險：`mcp` SDK 演進快（== pin＋最小 API 面）；hatchling sources 映射一次性定案；vhs GIF best-effort；年份窗擴充需權威農曆源比對（未排程）。
