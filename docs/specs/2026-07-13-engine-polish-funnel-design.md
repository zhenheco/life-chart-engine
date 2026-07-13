# Engine Polish & Funnel Readiness — SPEC

> `/go` 唯一輸入。本 spec 只含公開安全內容（本 repo 為公開 MIT repo）；
> 商業／行銷細節一律在私有 workspace 文件（見 Further Notes），不進本 repo。
> rev 3：吸收 round 1（8 🔴／25 🟡）與 round 2（5 🔴／18 🟡）交叉驗證全部發現。

---

## Problem Statement

- CLI 使用者漏帶任一出生 flag 時，引擎默默用內建範例人出盤並 exit 0——使用者（尤其是 AI agent）拿到「看似合理但完全錯誤」的盤面而不自知。這違背本引擎「寧可報錯、不出錯盤」的信任承諾。
- Agent 在 `--json` 模式餵入壞格式日期時會收到 raw Python traceback（`_parse_args` 的 `ValueError` 早於 try/except），違反「stdout 恰好一個 JSON object」的自家契約。
- HTTP 面（`server.py`）對越界值（tz=20、lat=95）與非有限值不做範圍檢查——越界值回 200 帶錯盤或 500，同一信任缺口的 HTTP 版本。
- Agent 作者照 `AGENTS.md` 寫 parser，卻遇到文件沒寫的實際欄位（紫微 horoscope 的 `stars`、`yearlyDecStar`），契約與現實 drift。
- 18 個翻譯 README 的 horoscope 物件描述停在舊版形狀（缺 `age`／小限），非英文讀者拿到過時文件。
- 想試用的人必須 git clone＋跑安裝腳本；沒有 `pip install`／`uvx` 一行試用路徑，沒有 PyPI 套件、沒有 CI badge、沒有 demo GIF——第一印象的試用成本與信任訊號都差。
- AI agent 生態要接這顆引擎只能自己包 CLI 或 HTTP；沒有 MCP server，Claude 等 MCP 客戶端無法原生呼叫。
- `webapp.py`（719 行、最大檔案）缺 HTTP 層功能測試——現有的只是靜態 DOM 字串 grep（`test_webapp_dom_safety.py`），表單→API→匯出流程零覆蓋；且空欄位會以空字串傳給 CLI，複製同一個範例人信任缺口。
- README 沒有任何指向 hosted web 版的入口，看完 repo 的非技術訪客沒有下一步。

## Solution

- 漏 flag、壞格式、非法組合一律在 argparse 層擋下：exit 2、usage 進 stderr、stdout 空。要範例盤改用顯式 `--example`。HTTP 面同步加嚴為 400（刻意的 hardening，非「行為不變」）。
- `AGENTS.md` 補齊實際輸出欄位（含欄位出現位置的不對稱）＋錯誤傳輸矩陣（CLI/HTTP/MCP）；18 個翻譯 README 同步，並加防 drift 的 guard test（語言無關的 literal markers）。
- `pyproject.toml` 補上 `[project]`＋entry points（`life-chart`、同名 alias `life-chart-engine`、`life-chart-mcp`），套件可 `pip install`／`uvx` 一行執行；核心依賴只有 astronomy-engine；發佈走 trusted publishing；CI badge＋vhs demo。
- 新增 stdio MCP server（`compute_chart` tool，thin wrapper over `build_json()`）；三面共用同一個 packaged 驗證模組與同一個 envelope serializer。
- `webapp.py` 補 HTTP 層功能測試與空欄位友善錯誤；支援 `LIFE_VENV`；瀏覽器探測補 macOS/Linux。
- README（英文＋zh-TW＋zh-CN）加「Hosted version」段落連到官方 web 版。

## User Stories

1. As a CLI user, I want omitting any of `--date/--time/--tz/--lat/--lon/--gender` to fail at the argparse layer (exit 2, usage on stderr, empty stdout) listing the missing flags, so that I can never mistake the built-in example person's chart for my own.
2. As an AI agent, I want `--json` mode to emit either exactly one JSON object on stdout (success, or `{"ok": false, ...}` for runtime errors, exit 1) or nothing on stdout for argument errors (exit 2), so that I can parse stdout unconditionally.
3. As a docs/demo author, I want an explicit `--example` flag that reproduces the historical example-person chart byte-for-byte (against golden fixtures captured from the pre-change CLI, both JSON and Markdown modes), so that existing tutorials keep a supported path.
4. As a CLI user, I want `--example` to be mutually exclusive with birth flags (`--date/--time/--tz/--lat/--lon/--gender` → exit 2) but combinable with non-birth flags (`--target`, `--name`, `--ziwei-day-divide`, `--json`), so that demo semantics are unambiguous. (The byte-identical guarantee of #3 applies to `--example` with defaults.)
5. As a CLI user passing `--json --date 1990-13-45`, `--time 25:99`, `--target 2025-02-30`, a non-leap-year `02-29`, or a birth year outside the supported window, I want an exit-2 usage error naming the bad flag, so that garbage input is rejected before any computation.
6. As an agent author, I want `AGENTS.md` to document every field the engine actually emits — including that `stars` appears only under `decadal`/`yearly` and `yearlyDecStar` only under `yearly` — so that my parser never meets undocumented fields and docs don't over-generalize.
7. As a non-English reader, I want all 18 translated READMEs to describe the same horoscope object shape (`{ decadal, yearly, age }`) and the same required-flags/`--example` semantics as the English README, so that translated docs are trustworthy.
8. As a maintainer, I want a guard test asserting the exact 18-file translation set each contains the pinned language-independent literals (code-span `{ decadal, yearly, age }`；`--example` token；required-flags code block), so that translation staleness is caught by CI, not by readers.
9. As a Python developer, I want `pip install life-chart-engine`, `uvx life-chart-engine --example --json`, and `uvx --from life-chart-engine life-chart --example --json` to all work (both forms verified post-publication), so that trying the engine costs one line.
10. As a packager, I want the wheel to install import package `life_chart_engine` (not top-level `scripts`) and include the Node sidecar files (`ziwei_iztro.cjs` + vendored `iztro.cjs`) inside the package, so that 紫微 works from an installed package without namespace pollution.
11. As a `--json`/HTTP/MCP caller without a working Node, I want the request to fail loudly (`{"ok": false, "error": "...Node.js >= 18 supported..."}` exit 1／HTTP 500／`isError: true`) rather than a partial or silent result; in Markdown CLI mode I want a clean stderr message containing "Node.js >= 18" with exit 1 and no traceback. (Node ≥ 18 is the documented **supported/tested** runtime — missing/failing node triggers the loud error; no active version probing is promised.)
12. As a maintainer, I want a release-triggered GitHub Actions publish workflow using PyPI trusted publishing, with the build＋`twine check` dry-run running in `qa-gate.yml` on every PR, so that publishing is a tagged release and packaging breakage is caught pre-merge.
13. As a repo visitor, I want a CI status badge (backed by a workflow that actually runs on push to main) and a terminal demo GIF at the top of the README, so that I can judge project health and output quality in ten seconds.
14. As an MCP client (e.g. Claude Desktop/Code), I want an MCP server exposing a `compute_chart` tool whose result is a single text content equal to the shared envelope serializer's output (byte-identical to CLI `--json` stdout minus the trailing newline), so that agents call charts natively instead of shelling out.
15. As an MCP client sending invalid input (missing field, bad date), I want a structured tool error (`isError: true` with a message) — not a crashed server — so that my session survives bad calls.
16. As an operator, I want the MCP server to stay offline/stateless (stdio only, no network), verified by an in-process no-network test, so that the engine's determinism promise holds in MCP mode.
17. As a maintainer, I want one packaged validation module shared by CLI, HTTP (`server.py`), and MCP, where `test_server.py`-covered behavior stays unchanged and the new out-of-range/non-finite rejections are a **deliberate, documented HTTP 400 hardening** (with exact status/detail tests for NaN、±inf、邊界值、越界值), so that input rules exist in exactly one place.
18. As a maintainer, I want functional tests that boot `webapp.py` in-process on an ephemeral port (server factory reporting the actual bound port) and drive `/api/chart` (which doubles as the JSON export surface — assert content-type and body parity with CLI `--json`) and the Markdown export endpoint, so that web-UI regressions are caught. The client-side-rendered result page is asserted only at API level.
19. As a webapp user submitting an empty form field, I want a clean `ok:false` error message (not raw argparse usage text) after the CLI turns strict, so that the web UI doesn't regress into leaking internals.
20. As a maintainer, I want the PDF-export path covered by a mocked `%PDF` success test plus a real-browser test that skips cleanly when no headless browser is present — with browser discovery extended to macOS (Chrome/Edge app paths) and Linux (chromium/google-chrome) alongside the existing Windows paths — so that CI and dev machines both behave.
21. As a local developer, I want `webapp.py` to respect `LIFE_VENV` (a venv **directory**; resolved to `bin/python` on Unix, `Scripts\python.exe` on Windows) with tests covering override-before-import and a missing-executable error, so that webapp functional tests run outside CI too.
22. As a curious non-technical visitor, I want a short "Hosted version" section in README.md, README.zh-TW.md, and README.zh-CN.md linking the official web product, so that the main audiences get a next step. (Remaining 15 translations: follow-up, not this round.)
23. As a CI consumer, I want all new tests wired into qa-gate with explicit install steps for `build` and the `[mcp]` extra, so that every PR runs the full guard suite.

## Modules

| Module | 職責（一句） | 公開介面（窄） | 新建/修改 |
|---|---|---|---|
| `scripts/chart_engine.py` | argparse 層必填/格式/互斥驗證、`--example`、新增 `main(argv=None)`；`ziwei()` subprocess 呼叫點 Node 失敗 → loud error（`--json`/Markdown 兩模式各自定義）；輸出走共用 envelope serializer | CLI flags＋`main(argv=None)`＋`to_json_text(envelope)` | 修改 |
| `scripts/validation.py` | 唯一輸入驗證模組：date/time/target 格式與真實日曆日、支援年份窗（見 Implementation Decisions）、tz∈[-12,14]、lat∈[-90,90]、lon∈[-180,180]、有限值；丟 `ValueError` | `validate_input(dict) -> dict` | 新建 |
| `server.py` | `_engine_input` 改走 `validation.py`；`test_server.py` 既有覆蓋行為不變；越界/非有限 → 400（刻意 hardening，文件化） | 既有 HTTP 介面＋新 400 案例 | 修改 |
| `scripts/mcp_server.py` | stdio MCP server，單一 `compute_chart` tool wrap `build_json()`；驗證走 `validation.py`；回傳走共用 serializer | console script `life-chart-mcp`（無 `[mcp]` extra 時給「pip install 'life-chart-engine[mcp]'」友善錯誤，不吐 raw ImportError） | 新建 |
| `scripts/ziwei_iztro.cjs` | vendored bundle 解析順序 `__dirname/vendor/iztro.cjs` → `__dirname/../vendor/iztro.cjs` | stdin/stdout JSON 介面不變 | 修改 |
| `pyproject.toml` | `[project]`（core deps＝astronomy-engine only）、hatchling sources 映射 `scripts/`→`life_chart_engine`＋vendor force-include、三個 console scripts、`[mcp]` extra | entry points ×3 | 修改 |
| `.github/workflows/publish.yml` | **僅** release 觸發、OIDC trusted publishing（upload job） | GitHub release 事件 | 新建 |
| `.github/workflows/qa-gate.yml` | 加 `push: branches [main]`；install `build`＋`.[mcp]`；跑新測試＋build/`twine check` dry-run step；`qa_gate_workflow_test.py` regex 同步 | 既有 CI 介面 | 修改 |
| `webapp.py` | `LIFE_VENV`（目錄語意）支援；`find_browser()` 補 macOS＋Linux 路徑；空欄位/CLI exit-2 → 友善 `ok:false` 訊息 | 既有 HTTP 介面不變 | 修改 |
| `AGENTS.md`＋`README*.md` | 契約補 drift＋錯誤傳輸矩陣＋HTTP 400 hardening 記載＋Node 支援聲明＋`~/.local/bin` 共存註記；badge、demo GIF、hosted-version 段（en/zh-TW/zh-CN）、18 譯本同步 | 文件 | 修改 |
| `docs/demo.tape`＋`docs/RELEASING.md` | vhs 腳本＋發佈步驟（PyPI pending publisher、`~/.local/bin/life-chart` 與 install.sh symlink 共存注意） | `vhs docs/demo.tape` | 新建 |
| `tests/test_webapp.py`、`tests/test_readme_sync.py`、`tests/test_mcp_server.py`、`tests/test_packaging.py` | 見 Testing Decisions | pytest | 新建 |
| `tests/test_engine_astronomy_contract.py`＋`tests/test_wrapper.sh` | 前者：fallback 斷言改 `--example`＋新錯誤案例；後者：**wrapper 煙測補 `--gender`**（Dockerfile/setup.sh 呼叫已帶，無需改） | pytest／bash | 修改 |

## Implementation Decisions

- Schema: 無 DB。JSON 輸出形狀**不變**、`schema_version` 維持 `"1.1"`：(a) `AGENTS.md` 補文件債（`stars` 限 decadal/yearly、`yearlyDecStar` 限 yearly）；(b) 無 Node → 整包 loud error，**不做 per-system 部分結果**；(c) `meta.version` 維持 `"1.0"`（引擎內部版本字串，與 PyPI 套件版本語意不同，`AGENTS.md` 一句話明載）。
- **Envelope serializer 單一來源**：新增 `to_json_text(envelope)`（集中定義 indent/ensure_ascii 等序列化參數）；CLI `--json` stdout＝serializer 輸出＋trailing newline；MCP text content＝serializer 輸出（無 trailing newline）；測試以此定義斷言 byte 等價。
- API contract:
  - CLI：**單一錯誤通道**——所有參數層錯誤（漏 flag、壞格式、越界值、支援年份窗外、`--example`×出生 flag）一律 argparse `parser.error()`：exit 2、usage 進 stderr、stdout 空。執行期錯誤：`--json` → envelope exit 1；Markdown 模式 → stderr 一行乾淨訊息（Node 案例含 "Node.js >= 18"）、exit 1、無 traceback。`--gender` 必填。`--example` 可與 `--target/--name/--ziwei-day-divide/--json` 併用。
  - HTTP：`test_server.py` 既有覆蓋行為不變；**新增 400 hardening**（NaN/±inf/tz、lat、lon 越界/年份窗外），`AGENTS.md` HTTP 段記載（hosted caller 送 geocode 後合法值，不受影響——部署註記）。
  - MCP：stdio；單一 tool `compute_chart`；成功＝單一 text content（serializer 輸出）；驗證失敗＝`isError: true`＋訊息；runtime 失敗（Node、高緯度）＝`isError: true`＋訊息，server 續存。
  - **錯誤傳輸矩陣**（寫進 `AGENTS.md`，並以 parity test 固定「驗證決策」三面一致——同一輸入，三面同判合法/非法；錯誤的載體各異）：驗證錯 → CLI exit 2／HTTP 400／MCP isError；runtime 錯（Node、高緯度 Placidus、sidecar timeout）→ CLI exit 1（`--json` envelope / Markdown stderr）／HTTP 500（既有語意）／MCP isError。
  - 驗證單一來源：`scripts/validation.py`；**支援年份窗＝1700–2200**（astronomy-engine 精度聲明範圍；窗外→驗證錯誤而非靜默降精度，README 已知限制段同步）。
- 架構決策:
  - MCP thin wrapper over `build_json()`，官方 `mcp` SDK（pin 版本）進 `[mcp]` extra；console script `life-chart-mcp` 常駐 `[project.scripts]`，import 失敗時輸出安裝提示（非 raw ImportError）。
  - 打包佈局（定案不回頭）：repo 目錄不動；wheel import package＝`life_chart_engine`（hatchling `sources` 映射；等效 setuptools 亦可）；`scripts/__init__.py`＋相對 import，checkout（`scripts.*`）與 wheel（`life_chart_engine.*`）雙載入成立；`vendor/iztro.cjs` force-include 至 `life_chart_engine/vendor/`；`.cjs` 解析順序如 Modules 表。core deps＝`astronomy-engine` only；fastapi/uvicorn/httpx/sentry-sdk 留 `requirements.txt`。版本 `1.1.0`；`requires-python ">=3.12,<3.13"`。**Node ≥ 18 為 documented supported/tested runtime**（不做主動版本探測；missing/failing → loud error 引用支援版本）。`~/.local/bin/life-chart` 與 install.sh symlink 目標相同——README/RELEASING 一行共存註記（uvx/pipx 不受影響）。
  - 發佈：`publish.yml` 僅 release 觸發（OIDC upload）；build＋`twine check` dry-run 移入 `qa-gate.yml` 隨 PR 跑。
  - CI：`qa-gate.yml` 加 `push: branches: [main]`；install 步驟明列 `pip install build` 與 `pip install -e ".[mcp]"`；`.github/scripts/qa_gate_workflow_test.py` regex 斷言同步更新維持綠。
- 第三方/整合: 官方 `mcp` SDK（MIT）、hatchling、vhs（開發機工具）。**禁止** AGPL／swisseph（guard test 續用）。
- 安全/權限: 無 secrets、無網路（in-process socket guard 驗 MCP）；輸入驗證單一來源；OIDC 不存 token；GIF/tape 只用 `--example`。
- 邊界/效能: Node 缺席/失敗/timeout 收斂單一 loud-error 路徑（PATH 遮蔽/假 node 注入測試）；webapp PDF 無瀏覽器 skip＋mocked `%PDF` 正案例；translations guard 用 pinned 語言無關 literal（`{ decadal, yearly, age }` code-span、`--example` token、必填 flags code block），斷言恰好 18 檔。

## Testing Decisions

| Module | 要測? | 測什麼外部行為 | Prior art |
|---|---|---|---|
| CLI arg 層 | ✅ | **第一步先擷取 pre-change golden fixtures（無 flag 的 JSON＋Markdown stdout）**；漏 flag／壞 date、time、target（2025-02-30、非閏 02-29、25:99）／年份窗外／`--example`×出生 flag／越界 tz、lat、lon → exit 2、stdout 空；`--example`（含 `--json` 與 Markdown）與 golden byte-identical；`--json` 執行期錯誤 → envelope exit 1；Markdown 執行期錯誤 → stderr 乾淨訊息 exit 1；**`tests/test_wrapper.sh` 補 `--gender`** | `tests/test_engine_astronomy_contract.py`、`tests/test_wrapper.sh` |
| `scripts/validation.py` | ✅ | 邊界值表（tz/lat/lon 邊界與越界、NaN/±inf、格式、真實日曆日、1700–2200 年份窗）；**驗證決策 parity**：同一批輸入 CLI/HTTP/MCP 三面同判（載體各異：exit2/400/isError） | `tests/test_server.py` 驗證段 |
| server.py 400 hardening | ✅ | NaN、±inf、tz=20、lat=95、lon=200、年份窗外 → 400＋detail 斷言；`test_server.py` 既有斷言全綠不改弱 | `tests/test_server.py` |
| MCP server | ✅ | in-process（SDK memory streams）initialize→tools/list→tools/call 回單一 text content＝serializer 輸出（＝CLI stdout 去尾 newline）；壞輸入→isError 連線續存（同 session 再成功呼叫一次）；socket guard 生效；**installed-wheel、checkout 外**跑 `life-chart-mcp`（含 `[mcp]`）＋無 extra 時友善錯誤 | `tests/test_server.py`、`tests/test_json_output.py`、no-network guard |
| Node 缺席路徑 | ✅ | PATH 遮蔽→`--json` envelope 含 "Node.js >= 18" exit 1／Markdown stderr 同訊息 exit 1 無 traceback；假 node 非零退出/timeout 收斂同路徑 | `tests/test_ziwei_iztro.py` |
| webapp | ✅ | in-process server factory（實際 bound port）；GET `/` 200；POST `/api/chart`（＝JSON 匯出面）content-type＋body 與 CLI `--json` 一致；MD 匯出端點內容正確；**空欄位 → 友善 `ok:false`（非 usage 原文）**；PDF mocked `%PDF`＋無瀏覽器 skip；`LIFE_VENV` 目錄語意（override-before-import＋missing-executable 案例） | `tests/test_server.py`、`tests/test_webapp_dom_safety.py` |
| 打包 | ✅ | `python -m build` 成功；乾淨 venv＋checkout 外：`life-chart`／`life-chart-engine` 跑 `--example --json` 合法 JSON；import package＝`life_chart_engine`（無頂層 `scripts`）；`life_chart_engine/vendor/iztro.cjs` 在 wheel 內；`.cjs` 雙路徑解析測試 | `tests/test_wrapper.sh` |
| README 譯本 sync | ✅ | 18 檔集合斷言＋每檔 pinned literals（`{ decadal, yearly, age }`、`--example`、必填 flags block）與英文同步 | `tests/test_review_log.py` |
| qa-gate dry-run | ✅（CI step） | build＋`twine check` 隨 PR 跑 | `.github/workflows/qa-gate.yml` |

## Vertical Slices

### Slice 1 — CLI 信任修補（golden fixtures→單一錯誤通道＋--example＋main()）
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #1, #2, #3, #4, #5
- **Acceptance criteria**:
  - [ ] **第一個 commit 先擷取 pre-change golden fixtures**（無 flag JSON＋Markdown stdout 各一）
  - [ ] 漏任一必填 flag（date/time/tz/lat/lon/gender）→ exit 2、stderr 列缺項、stdout 空（含 `--json`）
  - [ ] 壞格式/越界/年份窗外（含 2025-02-30、非閏 02-29、25:99、tz=20、lat=95、lon=200、1600 年）→ exit 2、stdout 空
  - [ ] `--example` 與出生 flags 互斥（exit 2）；與 `--target/--name/--ziwei-day-divide/--json` 可併用；預設下輸出與 golden byte-identical（JSON＋Markdown 兩模式）
  - [ ] 新增 `main(argv=None)`＋`to_json_text(envelope)` serializer；`python scripts/chart_engine.py` 呼叫路徑不變
  - [ ] 驗證邏輯在新建 `scripts/validation.py`
  - [ ] 既有 `test_cli_exit_codes_fallback_and_deterministic_output` 改寫為 `--example`；**`tests/test_wrapper.sh` 補 `--gender`**；全部測試綠
  - [ ] `AGENTS.md`＋`README.md` flags 表、exit code 段、breaking 說明同步

### Slice 2 — 驗證單一來源＋HTTP 400 hardening＋parity
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #17
- **Acceptance criteria**:
  - [ ] `server.py` `_engine_input` 改走 `validation.py`；`tests/test_server.py` 既有斷言全綠（不改弱）
  - [ ] 新增 400 hardening 測試：NaN、±inf、tz=20、lat=95、lon=200、年份窗外 → 400＋detail
  - [ ] `validation.py` 邊界值表測試（含 1700–2200 年份窗）
  - [ ] CLI/HTTP「驗證決策 parity」測試（同輸入同判；MCP 面 Slice 6 補齊）；`AGENTS.md` 記載 HTTP hardening＋錯誤傳輸矩陣

### Slice 3 — 契約補齊與 18 譯本同步（含 guard test）
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #6, #7, #8
- **Acceptance criteria**:
  - [ ] `AGENTS.md`：`stars`（限 decadal/yearly）、`yearlyDecStar`（限 yearly）形狀語意＋不對稱說明；schema_version 1.1；`meta.version` 區別一句話
  - [ ] 18 譯本：horoscope `{ decadal, yearly, age }`＋必填 flags/`--example` 語意同步
  - [ ] `tests/test_readme_sync.py`：恰好 18 檔集合＋每檔 pinned 語言無關 literals（`{ decadal, yearly, age }` code-span、`--example` token、必填 flags code block）
  - [ ] CI 跑新 guard test

### Slice 4 — 打包（wheel／entry points／依賴切分）
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #9, #10
- **Acceptance criteria**:
  - [ ] `pyproject.toml`：`[project]`（deps＝astronomy-engine only、version 1.1.0、requires-python `>=3.12,<3.13`）＋hatchling sources 映射＋console scripts `life-chart`/`life-chart-engine`＋`[mcp]` extra
  - [ ] wheel import package `life_chart_engine`；`scripts/__init__.py`＋相對 import；checkout 與 wheel 雙載入
  - [ ] `vendor/iztro.cjs` force-include；`.cjs` 雙路徑解析有測試
  - [ ] 乾淨 venv＋checkout 外：兩個 entry point `--example --json` 合法 JSON（自動化）
  - [ ] `install.sh`／`bin/life-chart`／Dockerfile 不受影響（wrapper 測試綠，已含 Slice 1 的 `--gender` 修正）；README/RELEASING 加 `~/.local/bin` 共存註記

### Slice 5 — 無 Node 的 loud-error 契約
- **Type**: AFK
- **Blocked by**: Slice 4
- **User stories**: #11
- **Acceptance criteria**:
  - [ ] 無 node（PATH 遮蔽）：`--json` → 整包 `{"ok": false, "error": ...含 "Node.js >= 18"...}` exit 1；Markdown → stderr 一行含 "Node.js >= 18"、exit 1、無 traceback
  - [ ] 假 node 非零退出／timeout 收斂同路徑（注入式測試）
  - [ ] `AGENTS.md`＋README 明載 Node ≥ 18 為 supported/tested runtime（pip 安裝情境含安裝指引；不承諾版本探測）

### Slice 6 — MCP server
- **Type**: AFK
- **Blocked by**: Slice 4
- **User stories**: #14, #15, #16
- **Acceptance criteria**:
  - [ ] `[mcp]` extra 安裝後 `life-chart-mcp` 可啟動 stdio server；未裝 extra 時輸出「pip install 'life-chart-engine[mcp]'」提示（非 raw ImportError）
  - [ ] in-process（memory streams）測試：initialize → tools/list 見 `compute_chart` → tools/call 回單一 text content＝serializer 輸出（＝CLI `--json` stdout 去尾 newline，byte 級斷言）
  - [ ] 壞輸入 → `isError: true`；同 session 再次成功呼叫（server 續存）；runtime 錯誤（Node 缺席）亦 isError 不退出
  - [ ] no-network guard in-process 生效；三面 parity 補齊 MCP 面
  - [ ] installed-wheel＋checkout 外實跑 `life-chart-mcp` 冒煙
  - [ ] `AGENTS.md`＋`README.md` 增 MCP 使用段（Claude Desktop/Code 設定範例）

### Slice 7 — webapp 修補與功能測試
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #18, #19, #20, #21
- **Acceptance criteria**:
  - [ ] `webapp.py`：`LIFE_VENV` 目錄語意（Unix `bin/python`／Windows `Scripts\python.exe`）；`find_browser()` 補 macOS（Chrome/Edge app 路徑）＋Linux（chromium/google-chrome）；空欄位/CLI exit-2 → 友善 `ok:false` 訊息（不露 usage 原文）
  - [ ] `tests/test_webapp.py`：in-process factory（回報實際 bound port）；GET `/` 200；POST `/api/chart` content-type＋body 與 CLI `--json` 一致（明確視 `/api/chart` 為 JSON 匯出面）；MD 匯出正確；空 `--date` 案例斷言友善錯誤
  - [ ] PDF：mocked `%PDF` 成功案例＋無瀏覽器 skip；`LIFE_VENV` override-before-import＋missing-executable 測試
  - [ ] 本地（macOS、LIFE_VENV）與 CI 皆綠

### Slice 8 — README 門面＋CI badge＋demo
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #13, #22, #23
- **Acceptance criteria**:
  - [ ] `qa-gate.yml`：加 `push: branches: [main]`＋install `build`/`.[mcp]`＋build＋`twine check` dry-run step；`qa_gate_workflow_test.py` regex 同步維持綠
  - [ ] README.md 頂部 CI badge（qa-gate、default branch）
  - [ ] `docs/demo.tape` 入 repo；GIF 生成並嵌入 README（開發機 vhs；受阻則列 HITL follow-up，不阻塞其餘 AC）
  - [ ] 「Hosted version」中性段落進 README.md、README.zh-TW.md、README.zh-CN.md；其餘 15 譯本列 follow-up
- **註**：GIF 為本 slice 唯一 best-effort 項。

### Slice 9 — 發佈流程（publish workflow＋RELEASING）
- **Type**: AFK
- **Blocked by**: Slice 4, Slice 8
- **User stories**: #12
- **Acceptance criteria**:
  - [ ] `.github/workflows/publish.yml`：**僅** release 觸發、OIDC trusted publishing upload（PR 側 dry-run 已在 qa-gate，Slice 8）
  - [ ] `docs/RELEASING.md`：版本 bump→tag→release→PyPI pending publisher 註冊步驟完整可照做（含 `~/.local/bin` 共存注意）

### Slice 10 — PyPI 首發（HITL）
- **Type**: HITL
- **Blocked by**: Slice 5, Slice 6, Slice 9
- **User stories**: #9, #12
- **Acceptance criteria**:
  - [ ] 使用者照 `docs/RELEASING.md` 完成 PyPI pending publisher 註冊
  - [ ] 打 v1.1.0 release → publish workflow 綠 → 乾淨機器實跑 `uvx life-chart-engine --example --json` **與** `uvx --from life-chart-engine life-chart --example --json` 皆成功（真實驗證）

## Out of Scope

- 引擎不加 geocoding／時區查找（呼叫端責任，既有契約）。
- 不加 Chiron/小行星、不開放紫微流派選擇（已知限制，維持）。
- 不引入 AGPL/swisseph 任何依賴。
- 不做 per-system 部分結果／partial envelope（違反三系統交叉驗證原則）。
- 1700–2200 支援年份窗外的計算支援（窗外一律驗證錯誤；擴窗需精度驗證，另開 issue）。
- 不在本 repo 放任何 hosted 產品的價格、漏斗、行銷、分析內容（hosted CTA 僅一段中性連結）。
- life-web（hosted 產品）的程式變更不在本 spec 的 slices 內（另一 repo 的並行工作線，見 Further Notes）。
- 廣告投放執行、社群發文執行（排程與素材屬私有 workspace 工作線）。
- py3.13+ 支援驗證、其餘 15 譯本 hosted-version 段、Node 版本主動探測（各自 follow-up）。

## Further Notes

- **公私分離鐵則**：本 repo 公開。任何含商業數字、漏斗、廣告策略的內容禁止 commit 進來；私有行銷工作線位於 workspace `Life/marketing/`（不在任何 git repo）。
- **並行工作線（不由 /go 執行，另行以同等 TDD＋cross-review 紀律處理）**：
  1. life-web 量測層：Meta Pixel ID 佈署、`ViewContent`/`InitiateCheckout`/`Purchase` 事件、server-side CAPI（webhook Purchase＋event_id 去重）、尊重既有 consent gating。
  2. life-web 真卡驗證：一筆真實 NT$399 走通 checkout→broker→Stripe→webhook→解鎖，驗畢退款；需使用者出卡（HITL）。
  3. 行銷：launch 素材更新（MIT／astronomy-engine 事實修正）＋渠道排程＋廣告 go/no-go 依 preads 評核（發佈執行 attended）。
- **server.py 註記**：變更＝驗證搬遷＋刻意 400 hardening（`test_server.py` 既有斷言全綠＋新 400 測試為證）；hosted caller 送 geocode 後合法值不受影響；Hetzner 部署（`DEPLOY-HETZNER.md`）無其他變更。
- **發佈順序約束**：HN/Reddit 發文宣稱的「一行安裝」以 Slice 10 完成為前提。
- 已知風險：`mcp` SDK 演進快（pin 版本＋最小 API 面）；hatchling sources 映射為一次性佈局決策（已定案）；vhs GIF 為 Slice 8 唯一 best-effort 項。
