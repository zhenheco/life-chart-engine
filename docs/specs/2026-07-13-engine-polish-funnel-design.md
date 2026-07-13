# Engine Polish & Funnel Readiness — SPEC

> `/go` 唯一輸入。本 spec 只含公開安全內容（本 repo 為公開 MIT repo）；
> 商業／行銷細節一律在私有 workspace 文件（見 Further Notes），不進本 repo。

---

## Problem Statement

- CLI 使用者漏帶任一出生 flag 時，引擎默默用內建範例人出盤並 exit 0——使用者（尤其是 AI agent）拿到「看似合理但完全錯誤」的盤面而不自知。這違背本引擎「寧可報錯、不出錯盤」的信任承諾。
- Agent 在 `--json` 模式餵入壞格式日期時會收到 raw Python traceback，違反「stdout 恰好一個 JSON object」的自家契約，agent 端解析直接崩潰。
- Agent 作者照 `AGENTS.md` 寫 parser，卻遇到文件沒寫的實際欄位（紫微 horoscope 的 `stars`、`yearlyDecStar`），契約與現實 drift。
- 18 個翻譯 README 的 horoscope 物件描述停在舊版形狀（缺 `age`／小限），非英文讀者拿到過時文件。
- 想試用的人必須 git clone＋跑安裝腳本；沒有 `pip install`／`uvx` 一行試用路徑，沒有 PyPI 套件、沒有 CI badge、沒有 demo GIF——第一印象的試用成本與信任訊號都差。
- AI agent 生態要接這顆引擎只能自己包 CLI 或 HTTP；沒有 MCP server，Claude 等 MCP 客戶端無法原生呼叫。
- `webapp.py`（719 行、最大檔案）零功能測試，web UI 回歸沒有防護網。
- README 沒有任何指向 hosted web 版的入口，看完 repo 的非技術訪客沒有下一步。

## Solution

- 漏 flag 直接報錯（明確列出缺哪些）；要範例盤改用顯式 `--example`。壞格式日期／時間在 argparse 層擋下（exit 2，stdout 乾淨）。
- `AGENTS.md` 補齊實際輸出欄位；18 個翻譯 README 同步 horoscope 形狀，並加防 drift 的 guard test。
- `pyproject.toml` 補上 `[project]`＋entry point，套件可 `pip install`／`uvx` 一行執行；加 GitHub Actions trusted-publishing 發佈流程與 CI badge；vhs demo tape＋GIF。
- 新增 stdio MCP server（`compute_chart` tool，thin wrapper over `build_json()`），MCP 客戶端可原生取得確定性盤面。
- `webapp.py` 補功能測試（真 HTTP 請求打表單流程與匯出）。
- README（英文＋18 譯本）加「Hosted version」段落連到官方 web 版。

## User Stories

1. As a CLI user, I want omitting any of `--date/--time/--tz/--lat/--lon` to fail with a clear error listing the missing flags, so that I can never mistake the built-in example person's chart for my own.
2. As an AI agent, I want `--json` mode to emit either exactly one JSON object (ok or `{"ok": false, ...}`) on stdout or an argparse usage error with empty stdout — never a traceback — so that I can parse stdout unconditionally.
3. As a docs/demo author, I want an explicit `--example` flag that reproduces the historical example-person chart, so that existing tutorials keep a supported path.
4. As a CLI user passing `--json --date 1990-13-45`, I want an exit-2 usage error naming the bad flag, so that garbage input is rejected before any computation.
5. As an agent author, I want `AGENTS.md` to document every field the engine actually emits (including 紫微 horoscope `stars` and `yearlyDecStar`), so that my parser never meets undocumented fields.
6. As a non-English reader, I want all 18 translated READMEs to describe the same horoscope object shape (`{ decadal, yearly, age }`) as the English README, so that translated docs are trustworthy.
7. As a maintainer, I want a guard test that fails when a translated README's output-shape marker drifts from English, so that translation staleness is caught by CI, not by readers.
8. As a Python developer, I want `pip install life-chart-engine` (and `uvx life-chart-engine --help`) to give me a working `life-chart` console command, so that trying the engine costs one line.
9. As a packager, I want the wheel to include the Node sidecar files (`ziwei_iztro.cjs` + vendored `iztro.cjs`) as package data, so that 紫微 works from an installed package, not only from a git checkout.
10. As a pip user without Node installed, I want western + human_design to still compute and 紫微 to fail with a clear "Node.js >= 18 required for 紫微" message inside the JSON envelope, so that partial capability degrades loudly, not silently.
11. As a maintainer, I want a release-triggered GitHub Actions workflow using PyPI trusted publishing, so that publishing a version is a tagged release, not a laptop ritual.
12. As a repo visitor, I want a CI status badge and a terminal demo GIF at the top of the README, so that I can judge project health and output quality in ten seconds.
13. As an MCP client (e.g. Claude Desktop/Code), I want an MCP server exposing a `compute_chart` tool that returns the same JSON as `--json`, so that agents call charts natively instead of shelling out.
14. As an MCP client sending invalid input (missing field, bad date), I want a structured MCP tool error — not a crashed server — so that my session survives bad calls.
15. As an operator, I want the MCP server to stay offline/stateless (stdio only, no network), so that the engine's determinism promise holds in MCP mode.
16. As a maintainer, I want functional tests that boot `webapp.py` on an ephemeral port and drive the form → result → JSON/Markdown export flow, so that web UI regressions are caught.
17. As a maintainer, I want the PDF-export test to skip cleanly when no headless browser is present, so that CI stays green across environments.
18. As a curious non-technical visitor, I want a short "Hosted version" section in the README linking the official web product, so that I can see my chart without installing anything.
19. As a zh-TW/zh-CN reader, I want the hosted-version link present in the translated READMEs too, so that the main non-English audiences get the same next step.
20. As a CI consumer, I want all new tests wired into the existing qa-gate workflow, so that every PR runs the full guard suite.

## Modules

| Module | 職責（一句） | 公開介面（窄） | 新建/修改 |
|---|---|---|---|
| `scripts/chart_engine.py` arg 層 | 必填驗證、`--example`、date/time argparse type 驗證；計算核心不動 | CLI flags（`_parse_args`） | 修改 |
| `scripts/ziwei_iztro.py`（或等效呼叫點） | Node 缺席時回明確錯誤訊息進 envelope | 既有 sidecar 呼叫介面不變 | 修改 |
| `scripts/mcp_server.py` | stdio MCP server，單一 `compute_chart` tool wrap `build_json()` | MCP tool `compute_chart(input) -> chart JSON` | 新建 |
| `pyproject.toml` | `[project]`／`[build-system]`／entry points／package data | `life-chart = ...:main`（console script） | 修改 |
| `.github/workflows/publish.yml` | tag/release 觸發、PyPI trusted publishing | GitHub release 事件 | 新建 |
| `.github/workflows/qa-gate.yml` | 跑新增測試 | 既有 CI 介面 | 修改 |
| `AGENTS.md`＋`README*.md` | 契約補齊 drift、badge、demo GIF、hosted-version 段、18 譯本同步 | 文件 | 修改 |
| `docs/demo.tape` | vhs 腳本，可重現 demo GIF | `vhs docs/demo.tape` | 新建 |
| `tests/test_webapp.py` | webapp 功能測試（ephemeral port 真 HTTP） | pytest/stdlib test | 新建 |
| `tests/test_readme_sync.py` | 18 譯本輸出形狀 marker guard | pytest/stdlib test | 新建 |
| `tests/test_mcp_server.py` | MCP initialize→list→call→fixture 比對 | pytest/stdlib test | 新建 |
| `tests/test_packaging.py`（或 CI step） | wheel build＋entry point＋package data 煙測 | CI step | 新建 |

## Implementation Decisions

- Schema: 無 DB。JSON 輸出形狀**不變**——`AGENTS.md` 只是補文件債（`stars`、`yearlyDecStar` 早已實際輸出），`schema_version` 維持 `"1.1"`，不 bump；文件明載這兩欄位為 1.1 既有欄位。
- API contract:
  - CLI：五個出生 flag 改必填（互斥替代：`--example` 出範例人）；`--date/--time/--target` 用 argparse `type=` 驗證器，壞格式 → exit 2、stderr usage、stdout 空；`--json` 執行期錯誤照舊 `{"ok": false}` envelope exit 1。`AGENTS.md`／README flags 表同步改（含明寫 breaking：舊「無 flag 默認範例人」行為移除，屬 CLI 行為修正非 JSON schema 變更）。
  - MCP：stdio transport；單一 tool `compute_chart`，輸入欄位與語意完全鏡射 `AGENTS.md` input flags（含 `ziwei_day_divide`／`target` 選填），輸出 = `build_json()` 原樣 JSON；輸入驗證鏡射 `server.py` `_engine_input` 的規則（重用或抽共用，不重寫第三份驗證邏輯）。
- 架構決策:
  - MCP server 是 `build_json()` 的 thin wrapper——**不得**複製任何計算邏輯（CLAUDE.md 既有鐵則）。依賴官方 `mcp` Python SDK，裝進 optional extra `life-chart-engine[mcp]`，核心安裝不因 MCP 加重。
  - 打包：PyPI 名稱 `life-chart-engine`（已確認 404 可用）；版本 `1.1.0`（對齊 schema 家族）；wheel 含 `.cjs` sidecar 為 package data；CPython `requires-python = ">=3.12,<3.13"`（py 3.13+ 無法跑的 native 依賴已移除，但 3.12 是唯一驗證環境——上限先鎖，放寬另開 issue 驗證）；Node ≥ 18 為 documented runtime dependency（僅紫微需要）。
  - 發佈：GitHub Actions trusted publishing（OIDC，無長效 token 進 repo/CI）；publish workflow 只在 release tag 觸發。
- 第三方/整合: 官方 `mcp` Python SDK（MIT）、vhs（僅開發機生成 GIF 用，非依賴）。無其他新依賴；**禁止**引入 AGPL／swisseph（既有 guard test 續用）。
- 安全/權限: 無 secrets、無網路（MCP stdio 亦然）；MCP/CLI 輸入驗證如上；publish.yml 用 OIDC trusted publishing 不存 token；GIF/tape 不含任何真人出生資料（用範例人）。
- 邊界/效能: 無 Node 環境 → 紫微欄位回明確錯誤（envelope 內 per-system error 或 `ok:false`，以「responses loud, not silent」為準，實作時與既有 `ziwei horoscope null` 慣例一致化並寫進 AGENTS.md）；webapp PDF 測試在無 headless browser 環境 skip；translations guard 用每檔一行 canonical marker 比對，避免 flaky 全文 diff。

## Testing Decisions

| Module | 要測? | 測什麼外部行為 | Prior art（既有同類測試） |
|---|---|---|---|
| CLI arg 層 | ✅ | 漏 flag → 非零 exit＋錯誤列缺項；`--example` 重現範例盤 byte-identical；壞 date/time → exit 2 stdout 空；`--json` 執行期錯誤 → envelope | `tests/test_engine_astronomy_contract.py`（exit code 段） |
| MCP server | ✅ | stdio initialize→tools/list→tools/call 回 fixture 相同 JSON；壞輸入回 tool error 不死 | `tests/test_server.py`（驗證規則）、`tests/test_json_output.py`（fixture 比對） |
| webapp | ✅ | ephemeral port 起服務：GET 表單 200、POST 出生資料 → 結果頁含三系統、JSON/MD 匯出內容正確；PDF 無瀏覽器則 skip | `tests/test_server.py`（HTTP 測試模式） |
| 打包 | ✅ | `python -m build` 成功；wheel 裝進乾淨 venv 後 `life-chart --example --json` 出合法 JSON；`.cjs` 在 package data 內 | `tests/test_wrapper.sh`（安裝面煙測） |
| README 譯本 sync | ✅ | 18 譯本的 horoscope 形狀 marker 與英文一致 | `tests/test_review_log.py`（文件 guard 先例） |
| publish.yml | ❌（CI workflow 用 dry-run job 自驗，不寫單元測試） | — | — |

## Vertical Slices

### Slice 1 — CLI 信任修補（必填驗證＋--example＋--json 契約）
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #1, #2, #3, #4
- **Acceptance criteria**:
  - [ ] 漏任一出生 flag：exit ≠ 0，stderr 明列缺哪些 flags；`--json` 模式 stdout 為空或單一 `{"ok": false}`（二擇一，實作定案後寫進 AGENTS.md）
  - [ ] `--example` 單獨使用可出盤，輸出與現行預設範例人 byte-identical
  - [ ] `--date garbage`／`--time 25:99` → exit 2、stdout 空、stderr 有 usage
  - [ ] 全部既有測試綠；新行為有 contract test 覆蓋
  - [ ] `AGENTS.md`＋`README.md` flags 表與 exit code 段同步更新

### Slice 2 — 契約補齊與 18 譯本同步（含 guard test）
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #5, #6, #7
- **Acceptance criteria**:
  - [ ] `AGENTS.md` schema 段含 `stars`、`yearlyDecStar` 的形狀與語意說明；`schema_version` 仍為 1.1
  - [ ] 18 個翻譯 README 的 horoscope 物件描述為 `{ decadal, yearly, age }`（含小限說明），Slice 1 的 flags 變更同步反映
  - [ ] 新增 `tests/test_readme_sync.py`：任何譯本 marker 與英文 drift → 測試紅
  - [ ] CI 跑新 guard test

### Slice 3 — 打包與發佈（PyPI-ready）
- **Type**: AFK
- **Blocked by**: Slice 1
- **User stories**: #8, #9, #10, #11
- **Acceptance criteria**:
  - [ ] `pyproject.toml` 有 `[project]`（name `life-chart-engine`、version `1.1.0`、requires-python `>=3.12,<3.13`、依賴表）＋`[build-system]`＋`[project.scripts] life-chart`＋`[project.optional-dependencies] mcp`
  - [ ] wheel 含 `.cjs` package data；乾淨 venv 安裝後 `life-chart --example --json` 輸出合法 JSON（自動化測試驗證）
  - [ ] 無 Node 環境時 western/human_design 正常、紫微回明確 "Node.js >= 18 required" 錯誤（測試以 PATH 遮蔽模擬）
  - [ ] `.github/workflows/publish.yml`：release 觸發、OIDC trusted publishing、含 build＋twine check dry-run job
  - [ ] `install.sh`／`bin/life-chart` 既有路徑不受影響（wrapper 測試綠）

### Slice 4 — MCP server
- **Type**: AFK
- **Blocked by**: Slice 3
- **User stories**: #13, #14, #15
- **Acceptance criteria**:
  - [ ] `life-chart-mcp`（entry point）或 `python -m` 可啟動 stdio MCP server
  - [ ] MCP client 走 initialize → tools/list（見 `compute_chart`）→ tools/call，回傳 JSON 與 `--json` fixture 一致
  - [ ] 壞輸入（缺欄位、壞日期）→ 結構化 tool error，server 不退出
  - [ ] 無網路呼叫（既有 no-network guard 模式套用到 MCP 測試）
  - [ ] `AGENTS.md`＋`README.md` 增 MCP 使用段（Claude Desktop/Code 設定範例）

### Slice 5 — webapp 功能測試
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #16, #17
- **Acceptance criteria**:
  - [ ] `tests/test_webapp.py`：ephemeral port 啟動、GET 200、POST 完整出生資料 → 結果頁含三系統段落、JSON 匯出可解析且與 CLI `--json` 一致、Markdown 匯出含標題段
  - [ ] PDF 匯出測試偵測無 headless browser 時 skip（不紅）
  - [ ] CI 納入且綠

### Slice 6 — README 門面（badge＋demo＋hosted CTA）
- **Type**: AFK
- **Blocked by**: Slice 1（demo 內容用新 flags）
- **User stories**: #12, #18, #19
- **Acceptance criteria**:
  - [ ] README.md 頂部有 qa-gate CI badge（真實 workflow 連結）
  - [ ] `docs/demo.tape`（vhs 腳本，用 `--example`）入 repo；GIF 已生成則嵌入 README，無法生成則留 tape＋TODO 註記（不阻塞 slice）
  - [ ] README.md 有「Hosted version」短段連到 https://life.aicycle.cc（陳述為 maintained hosted web version，不含價格）
  - [ ] zh-TW、zh-CN 譯本含同段；其餘譯本由 Slice 2 的 marker 機制不強制（記為 follow-up）

### Slice 7 — PyPI 首發（HITL）
- **Type**: HITL
- **Blocked by**: Slice 3, Slice 4
- **User stories**: #8, #11
- **Acceptance criteria**:
  - [ ] 使用者在 PyPI 完成 pending publisher 註冊（文件化步驟已寫入 docs/RELEASING.md）
  - [ ] 打 v1.1.0 release → publish workflow 綠 → `uvx life-chart-engine --example --json` 在乾淨機器可跑（真實驗證，非假設）

## Out of Scope

- 引擎不加 geocoding／時區查找（呼叫端責任，既有契約）。
- 不加 Chiron/小行星、不開放紫微流派選擇（已知限制，維持）。
- 不引入 AGPL/swisseph 任何依賴。
- 不在本 repo 放任何 hosted 產品的價格、漏斗、行銷、分析內容（hosted CTA 僅一段中性連結）。
- life-web（hosted 產品）的程式變更不在本 spec 的 slices 內（另一 repo 的並行工作線，見 Further Notes）。
- 廣告投放執行、社群發文執行（排程與素材屬私有 workspace 工作線）。
- py3.13+ 支援驗證（放寬 requires-python 另開 issue）。

## Further Notes

- **公私分離鐵則**：本 repo 公開。任何含商業數字、漏斗、廣告策略的內容禁止 commit 進來；本 spec 僅保留中性的 hosted-version 連結。私有行銷工作線（策略書、preads 市調、內容日曆）位於 workspace `Life/marketing/`（不在任何 git repo）。
- **並行工作線（不由 /go 執行，另行以同等 TDD＋cross-review 紀律處理）**：
  1. life-web 量測層：Meta Pixel ID 佈署、`ViewContent`/`InitiateCheckout`/`Purchase` 事件、server-side CAPI（webhook 端 Purchase＋event_id 去重）、尊重既有 consent gating。
  2. life-web 真卡驗證：一筆真實 NT$399 購買走通 checkout→broker→Stripe→webhook→解鎖，驗畢退款；需使用者出卡（HITL）。
  3. 行銷：launch 素材全面更新（授權已由 AGPL 改 MIT、Swiss Ephemeris 已換 astronomy-engine——現有素材所有相關敘述皆需改寫）＋渠道排程（HN/Reddit/X/Threads/FB/IG）＋廣告 go/no-go 依 preads 評核（發佈執行 attended）。
- **發佈順序約束**：HN/Reddit 發文宣稱的「一行安裝」以 Slice 7（PyPI 首發）完成為前提；行銷日曆錨定在本 spec ship 之後。
- **Deploy 注意**：本 repo 的 Hetzner HTTP 服務（`DEPLOY-HETZNER.md`）不受本 spec 影響（`server.py` 未動）；如 CI 檔案變更，qa-gate 必須維持既有測試矩陣（py3.12/node24）。
- 已知風險：`mcp` SDK 版本演進快，pin 版本＋最小 API 面（單 tool、stdio）降低破裂面；vhs GIF 生成依賴開發機工具，slice 明訂不阻塞。
