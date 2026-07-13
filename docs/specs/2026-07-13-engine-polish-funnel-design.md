# Engine Polish & Funnel Readiness — SPEC

> `/go` 唯一輸入。本 spec 只含公開安全內容（本 repo 為公開 MIT repo）；
> 商業／行銷細節一律在私有 workspace 文件（見 Further Notes），不進本 repo。
> rev 2：吸收 Codex＋Agent 交叉驗證 round 1 全部發現（5＋3 🔴、15＋10 🟡）。

---

## Problem Statement

- CLI 使用者漏帶任一出生 flag 時，引擎默默用內建範例人出盤並 exit 0——使用者（尤其是 AI agent）拿到「看似合理但完全錯誤」的盤面而不自知。這違背本引擎「寧可報錯、不出錯盤」的信任承諾。
- Agent 在 `--json` 模式餵入壞格式日期時會收到 raw Python traceback（`_parse_args` 的 `ValueError` 早於 try/except），違反「stdout 恰好一個 JSON object」的自家契約。
- Agent 作者照 `AGENTS.md` 寫 parser，卻遇到文件沒寫的實際欄位（紫微 horoscope 的 `stars`、`yearlyDecStar`），契約與現實 drift。
- 18 個翻譯 README 的 horoscope 物件描述停在舊版形狀（缺 `age`／小限），非英文讀者拿到過時文件。
- 想試用的人必須 git clone＋跑安裝腳本；沒有 `pip install`／`uvx` 一行試用路徑，沒有 PyPI 套件、沒有 CI badge、沒有 demo GIF——第一印象的試用成本與信任訊號都差。
- AI agent 生態要接這顆引擎只能自己包 CLI 或 HTTP；沒有 MCP server，Claude 等 MCP 客戶端無法原生呼叫。
- `webapp.py`（719 行、最大檔案）缺 HTTP 層功能測試——現有的只是靜態 DOM 字串 grep（`test_webapp_dom_safety.py`），表單→API→匯出流程零覆蓋。
- README 沒有任何指向 hosted web 版的入口，看完 repo 的非技術訪客沒有下一步。

## Solution

- 漏 flag、壞格式、非法組合一律在 argparse 層擋下：exit 2、usage 進 stderr、stdout 空。要範例盤改用顯式 `--example`。
- `AGENTS.md` 補齊實際輸出欄位（含欄位出現位置的不對稱）；18 個翻譯 README 同步 horoscope 形狀與新 flags 語意，並加防 drift 的 guard test。
- `pyproject.toml` 補上 `[project]`＋entry points（`life-chart` 與同名 alias `life-chart-engine`），套件可 `pip install`／`uvx` 一行執行；核心依賴只有 astronomy-engine；加 GitHub Actions trusted-publishing 發佈流程與 CI badge；vhs demo tape＋GIF。
- 新增 stdio MCP server（`compute_chart` tool，thin wrapper over `build_json()`），MCP 客戶端可原生取得確定性盤面；三面（CLI/HTTP/MCP）共用同一個 packaged 驗證模組。
- `webapp.py` 補 HTTP 層功能測試（API 與匯出端點；結果頁渲染屬 client-side JS，不以純 HTTP 斷言）。
- README（英文＋zh-TW＋zh-CN）加「Hosted version」段落連到官方 web 版。

## User Stories

1. As a CLI user, I want omitting any of `--date/--time/--tz/--lat/--lon/--gender` to fail at the argparse layer (exit 2, usage on stderr, empty stdout) listing the missing flags, so that I can never mistake the built-in example person's chart for my own.
2. As an AI agent, I want `--json` mode to emit either exactly one JSON object on stdout (success, or `{"ok": false, ...}` for runtime errors, exit 1) or nothing on stdout for argument errors (exit 2), so that I can parse stdout unconditionally.
3. As a docs/demo author, I want an explicit `--example` flag that reproduces the historical example-person chart byte-for-byte, so that existing tutorials keep a supported path.
4. As a CLI user passing `--example` together with any birth flag, I want an exit-2 usage error, so that ambiguous input is rejected instead of guessed.
5. As a CLI user passing `--json --date 1990-13-45`, `--time 25:99`, `--target 2025-02-30`, or a non-leap-year `02-29`, I want an exit-2 usage error naming the bad flag, so that garbage input is rejected before any computation.
6. As an agent author, I want `AGENTS.md` to document every field the engine actually emits — including that `stars` appears only under `decadal`/`yearly` and `yearlyDecStar` only under `yearly` — so that my parser never meets undocumented fields and docs don't over-generalize.
7. As a non-English reader, I want all 18 translated READMEs to describe the same horoscope object shape (`{ decadal, yearly, age }`) and the same required-flags/`--example` semantics as the English README, so that translated docs are trustworthy.
8. As a maintainer, I want a guard test asserting the exact 18-file translation set carries canonical markers (horoscope shape AND flags semantics) in sync with English, so that translation staleness is caught by CI, not by readers.
9. As a Python developer, I want `pip install life-chart-engine`, `uvx life-chart-engine --example --json`, and `uvx --from life-chart-engine life-chart --example --json` to all work, so that trying the engine costs one line.
10. As a packager, I want the wheel to install import package `life_chart_engine` (not top-level `scripts`) and include the Node sidecar files (`ziwei_iztro.cjs` + vendored `iztro.cjs`) inside the package, so that 紫微 works from an installed package without namespace pollution.
11. As a pip user without Node installed, I want any chart request to fail loudly with `{"ok": false, "error": "...Node.js >= 18 required for 紫微斗數..."}` (exit 1) rather than a partial or silent result, so that the three-system triangulation promise is never quietly degraded. (Node is a documented hard runtime dependency; no partial envelopes — schema stays 1.1.)
12. As a maintainer, I want a release-triggered GitHub Actions workflow using PyPI trusted publishing plus a build/twine-check dry-run job, so that publishing a version is a tagged release, not a laptop ritual.
13. As a repo visitor, I want a CI status badge (backed by a workflow that actually runs on push to main) and a terminal demo GIF at the top of the README, so that I can judge project health and output quality in ten seconds.
14. As an MCP client (e.g. Claude Desktop/Code), I want an MCP server exposing a `compute_chart` tool whose result is a single text content containing the exact `--json` envelope, so that agents call charts natively instead of shelling out.
15. As an MCP client sending invalid input (missing field, bad date), I want a structured tool error (`isError: true` with a message) — not a crashed server — so that my session survives bad calls.
16. As an operator, I want the MCP server to stay offline/stateless (stdio only, no network), verified by an in-process no-network test, so that the engine's determinism promise holds in MCP mode.
17. As a maintainer, I want one packaged validation module shared by CLI, HTTP (`server.py`), and MCP — with server.py behavior unchanged and its 301-line test suite still green — so that input rules (tz/lat/lon ranges, finiteness, date formats) exist in exactly one place.
18. As a maintainer, I want functional tests that boot `webapp.py` on an ephemeral port and drive the chart API and JSON/Markdown export endpoints (asserting parity with CLI `--json`), so that web-UI regressions are caught. The client-side-rendered result page is out of HTTP-test reach and asserted only at API level.
19. As a maintainer, I want the PDF-export path covered by a mocked `%PDF` success test plus a real-browser test that skips cleanly when no headless browser is present (with Linux Chromium discovery added alongside the existing Windows paths), so that CI stays green across environments.
20. As a local developer using `LIFE_VENV`, I want `webapp.py` to respect the `LIFE_VENV` override (like the documented test flow does), so that webapp functional tests run outside CI too.
21. As a curious non-technical visitor, I want a short "Hosted version" section in README.md, README.zh-TW.md, and README.zh-CN.md linking the official web product, so that the main audiences get a next step. (Remaining 15 translations: follow-up, not this round.)
22. As a CI consumer, I want all new tests wired into qa-gate with explicit install steps for `build` and the `[mcp]` extra, so that every PR runs the full guard suite.

## Modules

| Module | 職責（一句） | 公開介面（窄） | 新建/修改 |
|---|---|---|---|
| `scripts/chart_engine.py` | argparse 層必填/格式/互斥驗證、`--example`、新增 `main(argv=None)` 供 entry point；`ziwei()` subprocess 呼叫點的 Node 缺席錯誤（FileNotFoundError → 明確 Node >= 18 訊息進 envelope）；計算核心不動 | CLI flags＋`main(argv=None)` | 修改 |
| `scripts/validation.py` | 唯一的輸入驗證模組（date/time/target 格式、tz∈[-12,14]、lat∈[-90,90]、lon∈[-180,180]、有限值檢查），丟 `ValueError` | `validate_input(dict) -> dict` | 新建 |
| `server.py` | 改為 thin wrapper 呼叫 `scripts/validation.py`；HTTP 行為不變（`test_server.py` 全綠護航） | 既有 HTTP 介面不變 | 修改 |
| `scripts/mcp_server.py` | stdio MCP server，單一 `compute_chart` tool wrap `build_json()`；驗證走 `validation.py` | MCP tool `compute_chart` | 新建 |
| `scripts/ziwei_iztro.cjs` | vendored bundle 解析順序改為 `__dirname/vendor/iztro.cjs`（wheel 內佈局）→ `__dirname/../vendor/iztro.cjs`（checkout 佈局） | stdin/stdout JSON 介面不變 | 修改 |
| `pyproject.toml` | `[project]`（core deps＝astronomy-engine only）、`[build-system]`（hatchling 建議）、兩個 console scripts、`[mcp]` extra、`scripts/`→`life_chart_engine` 佈局映射＋vendor force-include | `life-chart`＋`life-chart-engine` entry points | 修改 |
| `.github/workflows/publish.yml` | release 觸發、OIDC trusted publishing、build＋twine check dry-run job | GitHub release 事件 | 新建 |
| `.github/workflows/qa-gate.yml` | 加 `push: branches [main]` 觸發（badge 需要）、安裝 `build`＋`.[mcp]`、跑新測試；`qa_gate_workflow_test.py` 的 regex 斷言同步維護 | 既有 CI 介面 | 修改 |
| `webapp.py` | 支援 `LIFE_VENV` 覆寫 venv 路徑；`find_browser()` 加 Linux Chromium 探測 | 既有 HTTP 介面不變 | 修改 |
| `AGENTS.md`＋`README*.md` | 契約補 drift（含 stars/yearlyDecStar 不對稱）、flags/exit code 改版、badge、demo GIF、hosted-version 段（en/zh-TW/zh-CN）、18 譯本同步 | 文件 | 修改 |
| `docs/demo.tape`＋`docs/RELEASING.md` | vhs 腳本＋發佈步驟（含 PyPI pending publisher 註冊） | `vhs docs/demo.tape` | 新建 |
| `tests/test_webapp.py`、`tests/test_readme_sync.py`、`tests/test_mcp_server.py`、`tests/test_packaging.py` | 見 Testing Decisions | pytest | 新建 |
| `tests/test_engine_astronomy_contract.py` | 既有 `test_cli_exit_codes_fallback_and_deterministic_output` 改寫：fallback 斷言改 `--example`；新增缺 flag/壞格式/互斥案例 | pytest | 修改 |

## Implementation Decisions

- Schema: 無 DB。JSON 輸出形狀**不變**、`schema_version` 維持 `"1.1"`：(a) `AGENTS.md` 補文件債（`stars` 限 decadal/yearly、`yearlyDecStar` 限 yearly——早已實際輸出）；(b) 無 Node → 整包 `{"ok": false, "error": "...Node.js >= 18 required..."}` exit 1，**不做 per-system 部分結果**（部分盤違反三系統交叉驗證原則，且避免 additive schema 變更）；(c) `meta.version` 維持 `"1.0"` 不動（引擎內部版本字串，與 PyPI 套件版本語意不同），`AGENTS.md` 一句話明載兩者區別。
- API contract:
  - CLI：**單一錯誤通道**——所有參數層錯誤（漏 flag、壞 date/time/target 格式、`--example` 與任一出生 flag 併用、非法 tz/lat/lon 值）一律 argparse `parser.error()` 路徑：exit 2、usage 進 stderr、stdout 空（`--json` 亦然）。執行期錯誤照舊 `--json` → `{"ok": false}` envelope exit 1。`--gender` 改必填（影響紫微結果，不可默默預設）。`AGENTS.md`＋README flags 表與 exit code 段同步（明寫 breaking：舊「無 flag 默認範例人」移除；CLI 行為修正，非 JSON schema 變更）。
  - MCP：stdio transport；單一 tool `compute_chart`，輸入欄位鏡射 `AGENTS.md` input flags（含 `ziwei_day_divide`/`target` 選填）；**成功回傳＝單一 text content，內容為 `build_json()` 的原樣 JSON 字串**；驗證失敗回 `isError: true`＋訊息，server 不退出。
  - 驗證單一來源：新建 packaged `scripts/validation.py`（丟 `ValueError`；範圍：tz∈[-12,14]、lat∈[-90,90]、lon∈[-180,180]、有限值、date/time/target 格式與真實日曆日）；CLI argparse type 驗證器、`server.py` `_engine_input`、MCP 全部改走它。`server.py` 只做搬遷不改行為（`test_server.py` 既有 301 行全綠為驗收）；高緯度 Placidus 失敗維持既有 runtime `ok:false` 行為並以 parity test 固定三面一致。
- 架構決策:
  - MCP server 是 `build_json()` 的 thin wrapper——**不得**複製任何計算邏輯。依賴官方 `mcp` Python SDK（pin 版本、最小 API 面），裝進 optional extra `life-chart-engine[mcp]`。
  - 打包佈局（公開後難回頭，此處定案）：repo 目錄結構**不動**（`scripts/` 留在原地，所有文件路徑不變）；wheel 安裝的 import package 名為 **`life_chart_engine`**，由 build backend 的路徑映射達成（hatchling `[tool.hatch.build.targets.wheel.sources]` 建議；等效 setuptools package-dir 亦可）；`scripts/` 加 `__init__.py`、內部 import 改相對形式，使 checkout（`scripts.*`）與 wheel（`life_chart_engine.*`）兩種載入都成立；`vendor/iztro.cjs` 以 force-include 進 wheel 的 `life_chart_engine/vendor/iztro.cjs`，`ziwei_iztro.cjs` 依上表順序解析。core dependencies＝`astronomy-engine` only；fastapi/uvicorn/httpx/sentry-sdk 留在 `requirements.txt`（HTTP 部署面，不進 wheel 依賴）。版本 `1.1.0`；`requires-python = ">=3.12,<3.13"`（3.12 為唯一驗證環境；放寬另開 issue）。Node ≥ 18 為 documented **hard** runtime dependency。
  - 發佈：GitHub Actions trusted publishing（OIDC，無長效 token）；publish workflow 只在 release tag 觸發；`docs/RELEASING.md` 寫明 PyPI pending publisher 註冊步驟。
  - CI：`qa-gate.yml` 加 `push: branches: [main]`（badge 才有 default-branch run）；install 步驟明列 `pip install build` 與 `pip install -e ".[mcp]"`；`.github/scripts/qa_gate_workflow_test.py` 的既有 regex 斷言同步更新維持綠。
- 第三方/整合: 官方 `mcp` Python SDK（MIT）、hatchling（build backend）、vhs（僅開發機生成 GIF，非依賴）。**禁止**引入 AGPL／swisseph（guard test 續用）。
- 安全/權限: 無 secrets、無網路（MCP stdio 亦然，以 in-process socket guard 驗證）；輸入驗證單一來源如上；publish.yml 用 OIDC 不存 token；GIF/tape 只用 `--example` 範例人，不含真人出生資料。
- 邊界/效能: Node 缺席/舊版/sidecar 崩潰/timeout 都收斂到同一條 loud-error 路徑（錯誤訊息固定含 "Node.js >= 18"；不做版本探測承諾，訊息以「需求宣告＋實際失敗原因」組成）；測試以 PATH 遮蔽/假 node 腳本注入模擬；webapp PDF 無瀏覽器則 skip；translations guard 用每檔 canonical marker 比對（horoscope 形狀＋flags 語意各一），斷言恰好 18 檔集合，避免 flaky 全文 diff。

## Testing Decisions

| Module | 要測? | 測什麼外部行為 | Prior art（既有同類測試） |
|---|---|---|---|
| CLI arg 層 | ✅ | 漏 flag／壞 date、time、target（含 2025-02-30、非閏年 02-29、25:99）／`--example`＋出生 flag 併用／非法 tz/lat/lon → 一律 exit 2、stdout 空、stderr usage；`--example` 輸出與現行範例人 byte-identical；`--json` 執行期錯誤 → envelope exit 1。**既有 `test_cli_exit_codes_fallback_and_deterministic_output` 改寫為 `--example` 斷言** | `tests/test_engine_astronomy_contract.py` |
| `scripts/validation.py` | ✅ | 邊界值表（tz/lat/lon 邊界與越界、NaN/inf、格式）；CLI/HTTP/MCP 三面 parity（同一壞輸入 → 三面一致拒絕） | `tests/test_server.py` 驗證段 |
| MCP server | ✅ | **in-process**（SDK memory streams）initialize → tools/list（見 `compute_chart`）→ tools/call 回單一 text content＝`--json` fixture 逐字節一致；壞輸入 → `isError: true`、連線續存；socket guard 在 in-process 模式下有效 | `tests/test_server.py`、`tests/test_json_output.py`、no-network guard（`test_engine_astronomy_contract.py`） |
| Node 缺席路徑 | ✅ | PATH 遮蔽 → `{"ok": false}` 含 "Node.js >= 18"；假 node（退出非 0）／timeout 收斂同路徑 | `tests/test_ziwei_iztro.py` |
| webapp | ✅ | ephemeral port：GET `/` 200；POST chart API 回 JSON 與 CLI `--json` 同輸入一致；JSON/MD 匯出端點內容正確；PDF：mocked `%PDF` 成功案例＋無瀏覽器 skip；`LIFE_VENV` 覆寫下可跑 | `tests/test_server.py`（HTTP 模式）、`tests/test_webapp_dom_safety.py` |
| 打包 | ✅ | `python -m build` 成功；wheel 裝進乾淨 venv：`life-chart --example --json` 與 `life-chart-engine --example --json` 皆出合法 JSON；import package 名為 `life_chart_engine`（無頂層 `scripts`）；`life_chart_engine/vendor/iztro.cjs` 在 wheel 內；**在 checkout 目錄外執行**（防 cwd 遮蔽） | `tests/test_wrapper.sh` |
| README 譯本 sync | ✅ | 18 檔集合斷言＋每檔兩個 canonical marker（horoscope 形狀、flags/`--example` 語意）與英文一致 | `tests/test_review_log.py` |
| publish.yml | ❌（workflow 內建 build＋twine check dry-run job 自驗；不寫單元測試） | — | — |

## Vertical Slices

### Slice 1 — CLI 信任修補（單一錯誤通道＋--example＋main()）
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #1, #2, #3, #4, #5
- **Acceptance criteria**:
  - [ ] 漏任一必填 flag（date/time/tz/lat/lon/gender）→ exit 2、stderr 明列缺項、stdout 空（含 `--json` 模式）
  - [ ] 壞格式 `--date`/`--time`/`--target`（含 2025-02-30、非閏年 02-29、25:99）與非法 tz/lat/lon 值 → exit 2、stdout 空
  - [ ] `--example` 單獨使用出盤，與現行預設範例人 byte-identical；`--example`＋任一出生 flag → exit 2
  - [ ] 新增 `main(argv=None)`；`python scripts/chart_engine.py` 既有呼叫路徑不變
  - [ ] 驗證邏輯living in 新建 `scripts/validation.py`（丟 ValueError；argparse 端接為 type/後置檢查）
  - [ ] 既有 `test_cli_exit_codes_fallback_and_deterministic_output` 改寫為 `--example` 斷言後，全部測試綠
  - [ ] `AGENTS.md`＋`README.md` flags 表、exit code 段、breaking 說明同步更新

### Slice 2 — server.py 驗證搬遷＋三面 parity
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #17
- **Acceptance criteria**:
  - [ ] `server.py` `_engine_input` 改走 `scripts/validation.py`；HTTP 行為不變，`tests/test_server.py` 既有斷言全綠（不改弱任何斷言）
  - [ ] `validation.py` 邊界值測試表（tz/lat/lon 邊界、NaN/inf、格式、真實日曆日）
  - [ ] CLI 與 HTTP 對同一組壞輸入的拒絕行為 parity test（MCP 面在 Slice 5 補齊三面）

### Slice 3 — 契約補齊與 18 譯本同步（含 guard test）
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #6, #7, #8
- **Acceptance criteria**:
  - [ ] `AGENTS.md` schema 段含 `stars`（限 decadal/yearly）、`yearlyDecStar`（限 yearly）的形狀、語意與不對稱說明；`schema_version` 仍為 1.1；`meta.version`＝"1.0" 與套件版本的區別一句話明載
  - [ ] 18 個翻譯 README：horoscope 物件描述 `{ decadal, yearly, age }`（含小限）＋ Slice 1 的必填 flags/`--example` 語意同步
  - [ ] `tests/test_readme_sync.py`：斷言恰好 18 檔集合、每檔兩個 canonical marker 與英文同步，drift → 紅
  - [ ] CI 跑新 guard test

### Slice 4 — 打包（wheel／entry points／依賴切分）
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #9, #10
- **Acceptance criteria**:
  - [ ] `pyproject.toml`：`[project]`（name `life-chart-engine`、version `1.1.0`、requires-python `>=3.12,<3.13`、dependencies＝`astronomy-engine` only）＋`[build-system]`＋console scripts `life-chart` 與 `life-chart-engine`（同 `main`）＋`[project.optional-dependencies] mcp`
  - [ ] wheel import package 名 `life_chart_engine`（repo 目錄 `scripts/` 不改名，靠 build 映射）；`scripts/__init__.py`＋相對 import；checkout 與 wheel 兩種載入都可跑
  - [ ] `vendor/iztro.cjs` force-include 至 `life_chart_engine/vendor/`；`ziwei_iztro.cjs` 解析順序（packaged → checkout）有測試
  - [ ] 乾淨 venv＋checkout 目錄外：兩個 entry point 跑 `--example --json` 皆合法 JSON（自動化測試）
  - [ ] `install.sh`／`bin/life-chart`／Dockerfile 既有路徑不受影響（wrapper 測試綠）

### Slice 5 — 無 Node 的 loud-error 契約
- **Type**: AFK
- **Blocked by**: Slice 4
- **User stories**: #11
- **Acceptance criteria**:
  - [ ] 無 node（PATH 遮蔽）→ 整包 `{"ok": false, "error": ...含 "Node.js >= 18"...}` exit 1；不輸出部分盤面
  - [ ] 假 node 非零退出／timeout 收斂到同一 loud-error 路徑（注入式測試）
  - [ ] `AGENTS.md`＋README 明載 Node ≥ 18 為硬性 runtime 依賴（含 pip 安裝情境）

### Slice 6 — MCP server
- **Type**: AFK
- **Blocked by**: Slice 4
- **User stories**: #14, #15, #16
- **Acceptance criteria**:
  - [ ] `[mcp]` extra 安裝後可啟動 stdio MCP server（entry point 或 `python -m`）
  - [ ] in-process（SDK memory streams）測試：initialize → tools/list 見 `compute_chart` → tools/call 回單一 text content，內容與 `--json` fixture 一致
  - [ ] 壞輸入（缺欄位、壞日期）→ `isError: true`＋訊息，server 續存（同 session 再次成功呼叫）
  - [ ] no-network guard 在 in-process 模式生效；驗證走 `validation.py`（三面 parity test 補齊 MCP 面）
  - [ ] `AGENTS.md`＋`README.md` 增 MCP 使用段（Claude Desktop/Code 設定範例）

### Slice 7 — webapp 修補與功能測試
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #18, #19, #20
- **Acceptance criteria**:
  - [ ] `webapp.py` 支援 `LIFE_VENV` 覆寫；`find_browser()` 加 Linux Chromium 常見路徑
  - [ ] `tests/test_webapp.py`：ephemeral port 起服務；GET `/` 200；POST chart API 與 CLI `--json` 同輸入輸出一致；JSON/MD 匯出端點內容正確（結果頁為 client-side render，不做 HTML 內容斷言）
  - [ ] PDF：mocked `%PDF` 成功案例＋無 headless browser 時 skip（不紅）
  - [ ] 本地 `LIFE_VENV` 環境與 CI 皆綠

### Slice 8 — README 門面＋CI badge＋demo
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #13, #21, #22
- **Acceptance criteria**:
  - [ ] `qa-gate.yml` 加 `push: branches: [main]` 觸發＋新測試 install 步驟（`build`、`.[mcp]`）；`qa_gate_workflow_test.py` regex 斷言同步維持綠
  - [ ] README.md 頂部 CI badge（指向 qa-gate、default branch）
  - [ ] `docs/demo.tape`（vhs，`--example`）入 repo；GIF 生成並嵌入 README（開發機 `brew install vhs` 生成；若該步驟受阻改列 HITL follow-up，不阻塞其餘 AC）
  - [ ] 「Hosted version」中性段落（連 https://life.aicycle.cc，不含價格）進 README.md、README.zh-TW.md、README.zh-CN.md；其餘 15 譯本列 follow-up
- **註**：GIF 需 repo 外工具（vhs），列為本 slice 唯一 best-effort 項，其餘 AC 為硬性。

### Slice 9 — 發佈流程（publish workflow＋RELEASING）
- **Type**: AFK
- **Blocked by**: Slice 4
- **User stories**: #12
- **Acceptance criteria**:
  - [ ] `.github/workflows/publish.yml`：release 觸發、OIDC trusted publishing、PR 上跑 build＋`twine check` dry-run job
  - [ ] `docs/RELEASING.md`：版本 bump→tag→release→PyPI pending publisher 註冊步驟完整可照做

### Slice 10 — PyPI 首發（HITL）
- **Type**: HITL
- **Blocked by**: Slice 5, Slice 6, Slice 9
- **User stories**: #9, #12
- **Acceptance criteria**:
  - [ ] 使用者照 `docs/RELEASING.md` 完成 PyPI pending publisher 註冊
  - [ ] 打 v1.1.0 release → publish workflow 綠 → 乾淨機器 `uvx life-chart-engine --example --json` 實跑成功（真實驗證，非假設）

## Out of Scope

- 引擎不加 geocoding／時區查找（呼叫端責任，既有契約）。
- 不加 Chiron/小行星、不開放紫微流派選擇（已知限制，維持）。
- 不引入 AGPL/swisseph 任何依賴。
- 不做 per-system 部分結果／partial envelope（違反三系統交叉驗證原則；本輪維持 all-or-nothing）。
- 不在本 repo 放任何 hosted 產品的價格、漏斗、行銷、分析內容（hosted CTA 僅一段中性連結）。
- life-web（hosted 產品）的程式變更不在本 spec 的 slices 內（另一 repo 的並行工作線，見 Further Notes）。
- 廣告投放執行、社群發文執行（排程與素材屬私有 workspace 工作線）。
- py3.13+ 支援驗證、其餘 15 譯本的 hosted-version 段（各自另開 follow-up issue）。

## Further Notes

- **公私分離鐵則**：本 repo 公開。任何含商業數字、漏斗、廣告策略的內容禁止 commit 進來；私有行銷工作線（策略書、preads 市調、內容日曆）位於 workspace `Life/marketing/`（不在任何 git repo）。
- **並行工作線（不由 /go 執行，另行以同等 TDD＋cross-review 紀律處理）**：
  1. life-web 量測層：Meta Pixel ID 佈署、`ViewContent`/`InitiateCheckout`/`Purchase` 事件、server-side CAPI（webhook 端 Purchase＋event_id 去重）、尊重既有 consent gating。
  2. life-web 真卡驗證：一筆真實 NT$399 購買走通 checkout→broker→Stripe→webhook→解鎖，驗畢退款；需使用者出卡（HITL）。
  3. 行銷：launch 素材全面更新（授權已由 AGPL 改 MIT、Swiss Ephemeris 已換 astronomy-engine——現有素材所有相關敘述皆需改寫）＋渠道排程（HN/Reddit/X/Threads/FB/IG）＋廣告 go/no-go 依 preads 評核（發佈執行 attended）。
- **server.py 註記**：本 spec 對 `server.py` 的變更僅限驗證邏輯搬遷至 `scripts/validation.py`（行為不變、`test_server.py` 全綠為證）；Hetzner 部署（`DEPLOY-HETZNER.md`）不受影響。
- **發佈順序約束**：HN/Reddit 發文宣稱的「一行安裝」以 Slice 10（PyPI 首發）完成為前提；行銷日曆錨定在本 spec ship 之後。
- 已知風險：`mcp` SDK 版本演進快，pin 版本＋最小 API 面降低破裂面；hatchling sources 映射屬一次性佈局決策（已在 Implementation Decisions 定案，公開後不再改 import 名）；vhs GIF 為 Slice 8 唯一 best-effort 項。
