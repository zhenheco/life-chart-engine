# 引擎 synastry 合盤運算（E1–E5） — SPEC

> 上游來源：`zhenheco/life-web` 的 `docs/specs/2026-08-05-synastry-real-computation--8844a06f0a-design.md`
> 的 §Implementation Decisions、§證據語意規則、§Vertical Slices E1–E5。消費端已驗證的 candidate
> `c5a0df1b92e947ee27c3cf4b22fccaeea8776857` 就是照那份契約寫的，凡本 spec 未明文偏離之處一律以其為準。
>
> **本 spec 對上游有五處刻意偏離**（皆為上游的內部矛盾或引擎側才看得見的缺漏，見 §Further Notes「與上游的偏離」）：
> 角度點 `salience` 的 `planet_weight`、`sort_keys`、CLI 時間未知、HD `data_confidence` 的窮盡切分、
> `dominance` 的產生規則。消費端不讀 `salience` 的算式、也不重算它，故這些偏離不影響已驗證的 candidate。

---

## Problem Statement

使用者買了「合盤」產品，但引擎目前只會算單人盤。它沒有任何雙人模式：兩個人的盤算出來之後，
沒有任何一段程式碼會去看「A 的水星和 B 的土星差幾度」「A 的火星落在 B 的第幾宮」
「兩人的人類圖閘門有沒有接成一條完整通道」。

於是消費端只能拿兩張互不相干的單人盤，自己憑印象湊出一段關係描述。
那份描述沒有可驗證的來源、同樣兩個人問兩次可能得到不同答案，也無從說明「這句話是根據哪一個具體接觸講的」。
使用者付了錢，拿到的是看起來很有信心、實際上無法追溯的內容。

同時，消費端（life-web）已經完成並驗證了整條依賴此契約的路徑，正等這個引擎能力上線；
在引擎具備 `/synastry` 之前，消費端一上線就會讓**既有付費合盤客戶**拿到 502/503。

## Solution

引擎新增一個合盤模式：一次收兩個人的出生資料，回傳**關係層級**的事實，而不是兩張單人盤。

消費端會拿到：兩人之間的西洋跨盤相位、雙向落宮、雙向角度點接觸、人類圖四種連結與合併後中心狀態；
每一筆事實都附帶可比較的語意欄位，讓消費端能排序、篩選、交叉比對，並在輸出中標明依據。
任一方出生時間未知時，時間相依的項目明確標成 `unavailable`，而不是悄悄用一個猜測值算下去。

## User Stories

1. As a consumer product, I want to POST two people's birth data to one endpoint and get relationship-level facts back, so that I never have to re-implement chart mathematics on my side.
2. As a consumer product, I want every element of every synastry evidence array to be one uniformly shaped Evidence object, so that one validator can check both the Western and the Human Design side.
3. As a consumer product, I want each Evidence to carry a `feature_id` that is unique within a response and identical across runs for identical input, so that I can cite the exact fact a sentence was derived from.
4. As a consumer product, I want `salience` computed by the engine, so that ranking the strongest contacts does not depend on my re-deriving orb weights.
5. As a consumer product, I want `dimensions` mapped to a fixed theme ontology in a defined order, so that Western and Human Design evidence about the same life area can be compared and diffed.
6. As a consumer product, I want `ease_or_tension` on every directional Evidence, so that I can detect when two independent systems agree or disagree.
7. As a consumer product, I want `participates_in_convergence` filled in by the engine, so that non-directional evidence (house overlay, centre states) never votes in that comparison.
8. As a consumer product, I want house overlay delivered as two separate arrays with defined direction semantics, so that a genuinely asymmetric relationship is not flattened into a false symmetry.
9. As a consumer product, I want each Human Design channel classified into exactly one of five outcomes and appearing at most once, so that my downstream copy never has to resolve a double classification.
10. As a consumer product, I want merged-chart centre states with the channels that caused them, so that I can explain *why* a centre became defined together.
11. As a consumer product, I want to omit birth time (or send `null` / `"unknown"`) on either side, so that a user who does not know their birth hour still gets the time-independent half of the reading.
12. As a consumer product, I want time-dependent items listed by fixed token in `synastry.unavailable` while their arrays remain present and empty, so that my parser never has to branch on a missing key.
13. As a consumer product, I want the engine to report exactly two completeness states (`full` / `partial`), so that I own the third ("unusable") judgement myself and the engine never has to describe its own unparsable output.
14. As a consumer product, I want an empty `aspects` array to be served with HTTP 200 and `partial`, so that a determinate result is never turned into a permanent 503 for that user.
15. As a consumer product, I want the response top level to keep `western` / `human_design` / `ziwei` keys and a `1.x` `schema_version`, so that my existing type guard passes unchanged.
16. As a consumer product, I want 紫微 explicitly reported as `not_computed` with a fixed methodology note, so that its absence reads as a deliberate boundary rather than a bug.
17. As a consumer product, I want every error response to carry a fixed machine-parsable `error` token and a documented retryable/not-retryable split, so that I can decide whether to retry without parsing human prose.
18. As an existing single-chart caller, I want `/chart` and the CLI's single-person output to stay byte-identical apart from the `schema_version` value, so that this feature cannot silently change my existing charts.
19. As an existing single-chart caller, I want the single-person output to contain no `synastry` key at all, so that my parser sees no new optional branch.
20. As an operator, I want `/health` to report `schema_version`, so that I can verify from outside which contract a deployed instance actually serves.
21. As an operator, I want the same `X-Engine-Key` auth and the same fail-closed behaviour on the new endpoint, so that it cannot become an open compute endpoint.
22. As a CLI user, I want the CLI to reproduce any HTTP synastry result offline including the time-unknown case, so that determinism is verifiable without the server.
23. As a CLI user, I want partially supplied `-b` flags to fail loudly naming what is missing, so that I never get a one-person chart when I asked for two.
24. As a maintainer, I want the same two-person input to produce byte-identical output across runs on both the CLI and HTTP, so that determinism remains testable rather than aspirational.
25. As a maintainer, I want the theme ontology asserted against a checked-in fixture in this repo, so that engine and consumer cannot drift apart unnoticed.
26. As a maintainer, I want no compatibility-score or fortune-scoring field anywhere in the schema, so that the product cannot later grow a "relationship score" through the back door.
27. As a maintainer, I want the existing golden-byte regression kept green with its regeneration scope and provenance recorded, so that a passing suite never depends on a fixture nobody re-derived.
28. As a maintainer, I want every output array's sort order pinned, so that "deterministic" is a property I can assert rather than an accident of iteration.
29. As a consumer product, I want each participant's Human Design type, strategy, authority, split bridges and completed hanging gates, so that I can describe what each person brings to the pair without calling a second endpoint.
30. As a maintainer, I want the no-swisseph and no-network guards extended to the new modules, so that the licensing and determinism posture cannot regress through a file the old scan never looked at.

## Modules

| Module | 職責（一句） | 公開介面（窄） | 新建/修改 |
|---|---|---|---|
| `scripts/synastry.py` | 由兩份已驗證輸入算出完整 synastry 區塊（唯一的關係運算入口） | `build_synastry(inp_a, inp_b) -> dict` | 新建 |
| `scripts/semantics.py` | `semantics-v1` 規則本體：theme 表、slug 表、orb 判定順序、權重、`salience`、`data_confidence`、`feature_id` 組成、type→strategy | `THEMES_V1`, `SLUGS`, `evidence(...)`, `orb_weight(orb, max_orb)`, `resolve_max_orb(a, b, aspect)`, `feature_id(method, **parts)`, `STRATEGY_BY_TYPE` | 新建 |
| `scripts/chart_engine.py` | 既有單人計算核心；新增雙人分派與 `schema_version` 1.2 | `build_json(inp)`（形狀不變）、`build_synastry_json(inp_a, inp_b)` | 修改 |
| `scripts/validation.py` | 既有輸入驗證；新增「時間未知」與 B 側欄位 | `validate_input(raw, *, allow_unknown_time=False)` | 修改 |
| `server.py` | HTTP surface；新增 `POST /synastry`、`/health` 加 `schema_version` | `POST /synastry` | 修改 |
| `scripts/mcp_server.py` | **明確排除於 synastry 之外**：維持單盤工具，僅更新 docstring 內的版本字面值 | 不變 | 修改（僅字面值） |
| `webapp.py` | **明確排除於 synastry 之外**：本地單盤 UI，不新增合盤畫面 | 不變 | 不動 |

設計約束：`build_synastry` 只呼叫既有的 `western()` / `human_design()`，**不得**複製任何相位或閘門計算；
每人的單盤計算在一次請求內只跑一次，供相位、overlay 與人類圖三個模組共用。

## Implementation Decisions

- **Schema**：無資料庫。
- **`schema_version` 釘 `"1.2"`，必須留在 `1.x` family**。消費端以 `sv.startsWith("1.")` 判定並拒絕 `2.x`。
- **序列化：不啟用 `sort_keys`。** 上游要求 `sort_keys=True`，但引擎現行輸出的鍵序是插入序
  （`ok, schema_version, input, western, human_design, ziwei, meta`），開啟排序會改動整份 byte stream，
  與 User story #18 直接互斥，也會炸掉既有的 `test_example_matches_pre_change_golden_bytes`。
  CPython 3.7+ 的 dict 保序，插入序**本身就是決定性的**。
  **浮點格式維持現行 `json.dumps` 預設 repr**；只有 `salience` 與 `data_confidence` 在**計算時**已 `round(..., 3)`。
- **golden fixture 的處置**：`tests/fixtures/golden_example.json` 含 `schema_version "1.1"`，
  故 1.2 bump 必然使 byte 對照變紅 → **只重新產生 `golden_example.json`，其 diff 僅限該一行**。
  `tests/fixtures/golden_example.md` 是 Markdown 路徑的輸出，`chart_engine.run()` **不印 schema_version**，
  該檔內也不含此字串 → **必須零 diff、保持 byte 相同**。
  `tests/fixtures/GOLDEN_PROVENANCE.md` 記錄本次再生的日期、原因與 diff 範圍。
- **單人輸出回歸 oracle**：parse 後與 `examples/sample-output.json` deep-equal，**僅排除 `schema_version`**。
  該檔不得重新產生（git diff 僅允許 `schema_version` 一行）。
- **單人模式不輸出 `synastry` 鍵**；雙人模式才輸出。
- **`1.1` 字面值的處理範圍**：
  - **執行期必改**：`scripts/chart_engine.py`（成功與 `ok:false` 兩個 envelope）、`server.py`（500 envelope）。
    「無殘留」斷言只掃這兩個檔。
  - **測試必改**：`tests/test_engine_astronomy_contract.py` 的 **live 斷言**（現為 `assert got["schema_version"] == "1.1"`）
    改為 `"1.2"`；同檔中對 **fixture** 的斷言（`assert data["engine_schema_version"] == "1.1"`）
    與模擬 envelope 的常數**維持 `1.1` 不變**（它們描述的是未變動的基線資料）。
  - **文件必改**：`AGENTS.md`（§1 identity、§4 output reference）、`README.md`（Output reference）、
    `scripts/mcp_server.py` docstring、18 份翻譯 README 中敘述**當前** `schema_version` 之處
    （`tests/test_readme_sync.py` 保持綠）。
  - **不得改動**：各 README 的版本歷史敘述、`docs/specs/2026-07-13-engine-polish-funnel-design.md`、
    `tests/fixtures/ephemeris_baseline.json`。

### API contract — `POST /synastry`

Body `{ "person_a": {...}, "person_b": {...} }`，每人欄位同 `/chart`，但 `time` 為 optional。
每人的 `name`／`target`／`ziwei_day_divide` **接受但忽略**（照常通過 `validate_input` 的既有驗證，
不影響輸出；`target` 與 `ziwei_day_divide` 在不算紫微時無意義）。

Response 頂層形狀固定：

```json
{
  "ok": true,
  "schema_version": "1.2",
  "western":      { "person_a": {}, "person_b": {} },
  "human_design": { "person_a": {}, "person_b": {} },
  "ziwei":        { "person_a": {}, "person_b": {},
                    "status": "not_computed",
                    "methodology_note": "紫微斗數沒有本引擎採用的合盤方法；兩人盤各自獨立計算，不做關係層級推論。" },
  "synastry":     { "western": { "aspects": [], "a_planets_in_b_houses": [], "b_planets_in_a_houses": [],
                                 "angle_contacts_a_to_b": [], "angle_contacts_b_to_a": [] },
                    "human_design": { "channel_connections": [], "center_states": [],
                                      "participants": { "person_a": {}, "person_b": {} } },
                    "unavailable": [] },
  "evidence_completeness": "full"
}
```

- `person_a` / `person_b` 在 `western` / `human_design` / `ziwei` 中固定為**空物件**，
  只為讓消費端檢查三鍵存在的型別守衛通過；個人盤資料不由此 endpoint 提供。
- `ziwei.methodology_note` 為上列**固定字串**，不隨輸入變化。
- 成功回應含頂層 `ok: true`（與 `/chart` 一致，AGENTS.md §5 要求 agent 依 `ok` 分支）。
- **`unavailable` 非空時各陣列仍存在且為 `[]`**，鍵永不消失。
- **`/synastry` 不呼叫紫微 Node sidecar**，故該路徑**沒有 per-request 的 Node 依賴**；
  `node` 不存在時 `/synastry` 仍正常運作（Node ≥ 18 仍是 `/chart` 與 CLI 單盤的硬性需求）。

**`participants.person_x` 的形狀**（**非 evidence 物件**）：

```json
{ "type": "生產者", "strategy": "等待回應", "authority": "薦骨型權威",
  "split_bridges": [ { "channel": "20-34", "centers": ["喉", "薦骨"] } ],
  "hanging_gates_completed": [ { "own_gate": 20, "partner_gate": 34, "channel": "20-34" } ] }
```

- `split_bridges`：**該人自身盤**中，其定義中心被切分為 ≥2 個連通分量時，
  合併後新形成、且**連接原本不同分量**的通道清單。元素為 `{channel, centers}`；
  `centers` 依 `lo` 閘門所屬中心、`hi` 閘門所屬中心的順序。若該人自身為單一定義或無定義 → `[]`。
- `hanging_gates_completed`：**該人自身的懸掛閘門**（自己持有一端、自己另一端未持有）中，
  被**對方**補上另一端而形成完整通道者。元素為 `{own_gate, partner_gate, channel}`，
  `own_gate` 為該人持有的閘門。故 `person_a` 這格裝的是「A 的懸掛閘門被 B 補足」的清單。
- `authority` 值域即引擎現行 `human_design()` 的中文字面值：
  `情緒型權威`／`薦骨型權威`／`直覺型(脾)權威`／`意志力(心)權威`／`自我投射型權威`／`無內在權威(心智投射/月亮)`。

### evidence schema（canonical 定義在此節）

```json
{
  "feature_id": "w-syn-a-mercury-square-b-saturn",
  "system": "western",
  "method": "synastry_aspect",
  "method_version": "western-synastry-v1",
  "subject": "A",
  "object": "B",
  "raw_fact": { "planet_a": "Mercury", "aspect": "square", "planet_b": "Saturn",
                "exact_angle": 90, "actual_angle": 89.3, "orb": 0.7 },
  "dimensions": ["communication", "commitment_stability", "autonomy_boundary"],
  "salience": 0.882,
  "ease_or_tension": "tension",
  "method_consensus": "core",
  "data_confidence": 0.95,
  "participates_in_convergence": true
}
```

此範例是**規則的產物，不是獨立來源**：`dimensions` ＝ 水星列的 `{communication}` 接上土星列的
`{commitment_stability, autonomy_boundary}`（各自依**行星→theme 表的列內順序**）；
`orb_weight = 1 - (0.7/5)² = 0.9804`，`planet_weight = max(0.9, 0.8) = 0.9`，
故 `salience = round(0.9804 × 0.9, 3) = 0.882`；兩側時間已知，`data_confidence = 0.95`。

- `system` ∈ `western|human_design`；`ease_or_tension` ∈ `ease|tension|mixed`；
  `method_consensus` ∈ `core|named_school|experimental`（本次一律 `core`）。
- **`raw_fact` 中的名稱一律使用下方 §值域與 slug 表的「raw_fact 值」欄**（英文），
  不使用引擎內部中文名。
- **`method` 值域固定五個**：

  | `method` | `method_version` | `subject` / `object` | `raw_fact` 欄位 | `feature_id` 模板 |
  |---|---|---|---|---|
  | `synastry_aspect` | `western-synastry-v1` | `"A"` / `"B"` | `planet_a`(str), `aspect`(str), `planet_b`(str), `exact_angle`(int), `actual_angle`(float), `orb`(float) | `w-syn-a-<planet_a>-<aspect>-b-<planet_b>` |
  | `house_overlay` | `western-synastry-v1` | **visitor / owner**（`subject` ＝ 行星所有人 ＝ visitor；`object` ＝ 宮位所有人 ＝ owner） | `planet`(str), `house_number`(int 1–12), `house_system`(`"placidus"`) | `w-ovl-<visitor>-<planet>-in-<owner>-h<house_number>` |
  | `angle_contact` | `western-synastry-v1` | `"A"` / `"B"` | `planet`(str), `angle`(`"asc"\|"desc"\|"mc"\|"ic"`), `aspect`(str), `exact_angle`(int), `actual_angle`(float), `orb`(float) | `w-ang-<subject>-<planet>-<aspect>-<object>-<angle>` |
  | `hd_channel_connection` | `human-design-synastry-v1` | 見 §人類圖連結判定 | `channel`(`"<lo>-<hi>"`), `link_type`(str), `a_gates`(int[]), `b_gates`(int[]), `centers`(str[2]), `full_channel_owner`(`"A"\|"B"\|null`) | `hd-chan-<lo>-<hi>-<link_type>` |
  | `hd_center_state` | `human-design-synastry-v1` | `null` / `null` | `center`(str), `state`(enum), `causing_channels`(str[]) | `hd-ctr-<center_slug>-<state_slug>` |

  模板中的 `<subject>`／`<object>`／`<visitor>`／`<owner>` 一律小寫為 `a`／`b`。
  `<link_type>` 的四個值本身即為合法 slug（`electromagnetic`／`dominance`／`compromise`／`companionship`）。
  結果須符合 `^[a-z]+-[a-z0-9-]+$`（**不含底線**，故 `state` 在 feature_id 中使用下表的 `state_slug`）。
  **同一個 response 內所有 `feature_id` 互異**（含雙向 overlay 與雙向角度點）。
- **不設 `interpretive_valence`**。
- `salience` / `data_confidence` 為 `0.0–1.0` float，一律 `round(..., 3)`。

### 值域與 slug 表

引擎內部使用中文名；`raw_fact` 使用英文值；`feature_id` 使用 slug。三者一一對應：

| 引擎內部名 | raw_fact 值 | slug |
|---|---|---|
| 太陽 | `Sun` | `sun` |
| 月亮 | `Moon` | `moon` |
| 水星 | `Mercury` | `mercury` |
| 金星 | `Venus` | `venus` |
| 火星 | `Mars` | `mars` |
| 木星 | `Jupiter` | `jupiter` |
| 土星 | `Saturn` | `saturn` |
| 天王星 | `Uranus` | `uranus` |
| 海王星 | `Neptune` | `neptune` |
| 冥王星 | `Pluto` | `pluto` |
| 北交點 | `North Node` | `north-node` |
| 上升 | `Ascendant` | `asc` |
| 下降 | `Descendant` | `desc` |
| 天頂 | `Midheaven` | `mc` |
| 天底 | `Imum Coeli` | `ic` |
| 合相 | `conjunction` | `conjunction` |
| 六合 | `sextile` | `sextile` |
| 四分 | `square` | `square` |
| 三分 | `trine` | `trine` |
| 對分 | `opposition` | `opposition` |
| 頭 | `Head` | `head` |
| 邏輯 | `Ajna` | `ajna` |
| 喉 | `Throat` | `throat` |
| G | `G` | `g` |
| 意志 | `Heart` | `heart` |
| 情緒 | `Solar Plexus` | `solar-plexus` |
| 薦骨 | `Sacral` | `sacral` |
| 脾 | `Spleen` | `spleen` |
| 根 | `Root` | `root` |

`state` 與 `state_slug`：`a_defined`→`a-defined`；`b_defined`→`b-defined`；`both_defined`→`both-defined`；
`defined_by_merge`→`defined-by-merge`；`undefined`→`undefined`。
（`raw_fact.state` 保留底線形式供消費端 switch；只有 `feature_id` 用連字號形式。）
`angle` 欄位的值即上表角度點的 slug（`asc`／`desc`／`mc`／`ic`）。

### `dimensions` 的順序與去重

`dimensions` **不依 `themes-v1` 的宣告順序排序**，而是依**來源表的列內順序**串接後去重：

- **`synastry_aspect`**：A 側行星那一列的 theme（依該列順序）→ B 側行星那一列的 theme。
- **`house_overlay`**：該行星那一列的 theme。
- **`angle_contact`**：行星那一列的 theme → 角度點那一列的 theme。
- **`hd_channel_connection`**：連結類型那一列的 theme → `lo` 閘門所屬中心那一列的 theme
  → `hi` 閘門所屬中心那一列的 theme。（HD 的三個來源沒有 A/B 側之分，故以此固定順序取代 A 先 B 後。）
- **`hd_center_state`**：該中心那一列的 theme。

重複者只保留**首次出現**。此規則對同一輸入完全決定性，且與上方 canonical 範例
`["communication","commitment_stability","autonomy_boundary"]` 一致。

### 陣列排序（每個外部可見陣列都必須有 total order）

| 陣列 | 排序鍵 |
|---|---|
| `aspects` | `salience` desc → `feature_id` asc |
| `a_planets_in_b_houses`, `b_planets_in_a_houses` | `salience` desc → `feature_id` asc |
| `angle_contacts_a_to_b`, `angle_contacts_b_to_a` | `salience` desc → `feature_id` asc |
| `channel_connections` | `salience` desc → `feature_id` asc |
| `center_states` | 依 §中心 → theme 表的列順序（頭→邏輯→喉→G→意志→情緒→薦骨→脾→根） |
| `raw_fact.a_gates`, `raw_fact.b_gates` | 閘門編號 asc |
| `raw_fact.centers` | `lo` 閘門所屬中心、`hi` 閘門所屬中心（固定兩元素，非排序） |
| `causing_channels` | `"<lo>-<hi>"` 字串 asc |
| `unavailable` | 固定 token 順序：`house_overlay`, `angle_contacts`, `hd_lines` |
| `split_bridges` | `channel` 字串 asc |
| `hanging_gates_completed` | `own_gate` 編號 asc |

`feature_id` 全域唯一，故每組排序鍵皆構成 total order。

### 主題 ontology `themes-v1`

10 個固定 ID：`communication`、`emotion_regulation`、`decision_power`、`action_tempo`、
`intimacy_attraction`、`autonomy_boundary`、`commitment_stability`、`money_division`、
`conflict_repair`、`timing_context`。

此 ontology 是**產品自訂的二次轉譯**，不是任何命理傳統原生的分類（見 ADR-0001）。
本 repo 以 `tests/fixtures/themes-v1.json` 作為 checked-in 對照清單，格式為
`{"themes": [<10 個 ID，依上列順序>]}`；`scripts/semantics.py` 的 `THEMES_V1` 必須與之逐字相同。
該檔的來源是消費端的同名常數；任一方變更即為對方的破壞性變更。

**注意**：此宣告順序只用於 `themes-v1.json` 的比對，**不用於 `dimensions` 的排序**（見上一節）。

- **西洋：行星 → theme**（列內順序即 `dimensions` 的串接順序）：

  | 行星 | themes |
  |---|---|
  | 太陽 | `decision_power`, `commitment_stability` |
  | 月亮 | `emotion_regulation`, `intimacy_attraction` |
  | 水星 | `communication` |
  | 金星 | `intimacy_attraction`, `money_division` |
  | 火星 | `action_tempo`, `conflict_repair` |
  | 木星 | `money_division`, `commitment_stability` |
  | 土星 | `commitment_stability`, `autonomy_boundary` |
  | 天王星 | `autonomy_boundary` |
  | 海王星 | `emotion_regulation` |
  | 冥王星 | `decision_power`, `conflict_repair` |
  | 北交點 | `timing_context` |
  | 角度點（ASC/DSC/MC/IC） | `timing_context`, `autonomy_boundary` |

- **人類圖：連結類型 → theme**：`electromagnetic` = `intimacy_attraction`, `conflict_repair`；
  `dominance` = `decision_power`, `autonomy_boundary`；`compromise` = `autonomy_boundary`, `conflict_repair`；
  `companionship` = `commitment_stability`, `action_tempo`。
- **人類圖：中心 → theme**（**列順序即 `center_states` 的排序基準**）：

  | 引擎內部名 | 英文 | themes |
  |---|---|---|
  | 頭 | Head | `communication`, `decision_power` |
  | 邏輯 | Ajna | `communication`, `decision_power` |
  | 喉 | Throat | `communication`, `action_tempo` |
  | G | G (Identity) | `commitment_stability`, `autonomy_boundary` |
  | 意志 | Heart / Ego | `money_division`, `decision_power` |
  | 情緒 | Solar Plexus | `emotion_regulation`, `conflict_repair` |
  | 薦骨 | Sacral | `action_tempo`, `intimacy_attraction` |
  | 脾 | Spleen | `timing_context`, `autonomy_boundary` |
  | 根 | Root | `action_tempo`, `emotion_regulation` |

### 西洋計算規則

- **相位 → `ease_or_tension`**：三分 120° = `ease`；六合 60° = `ease`；四分 90° = `tension`；
  對分 180° = `tension`；合相 0° = `mixed`。合相判 `mixed` 是因為它本質中性。
  **角度點接觸沿用同一張表**。house overlay 不適用（固定 `mixed`）。
- **參與 `aspects[]` 的天體集合固定 11 個**：太陽、月亮、水星、金星、火星、木星、土星、天王星、海王星、
  冥王星、**北交點**。**南交點不參與**。**角度點不進 `aspects[]`**。
- **house overlay 的天體集合**：與 `aspects[]` **相同的 11 個**。
- **角度點接觸的天體集合**：同上 11 個對 4 個角度點。**角度點對角度點不產生 evidence**。
- **「外行星」＝天王星、海王星、冥王星**；木星與土星**參與**。**不計算 Chiron**。
- **orb 判定順序**（覆蓋規則）：
  1. 任一端為**角度點或北交點** → 用該天體的 orb（角度點 3°；日月對角度點 4°；北交點 2°），
     **不套用日月 +1°**。**兩端皆為特殊天體時取較小者**（例：ASC 對北交點 → 2°）。
  2. 否則 → 用相位 orb（合 6／沖 6／刑 5／拱 5／六合 3），日月任一參與則 +1°，絕對上限 7°。
  3. 兩端皆為外行星 → 不計分、不輸出。
- **`orb_weight = max(0, 1 - (actual_orb / max_orb)²)`**；角距一律以最短弧 `min(d, 360-d)` 計算。
- **行星權重**：日月 `1.0`；水金火 `0.9`；木土 `0.8`；天海冥 `0.6`；北交點與角度點 `0.5`。
- **`salience` 公式**：
  - **跨盤相位**：`round(orb_weight × planet_weight, 3)`。兩端皆為一般天體 → `planet_weight = max(w_a, w_b)`；
    **任一端為北交點 → 固定 `0.5`**。
  - **角度點接觸**：`round(orb_weight × 0.5, 3)`。`planet_weight` **固定 `0.5`**，**不取 max**。
  - **house overlay**：`round(planet_weight × 0.8, 3)`。
  - **人類圖通道**：固定 `companionship/electromagnetic = 0.9`、`dominance = 0.8`、`compromise = 0.7`。
  - **人類圖中心狀態**：固定 `0.5`（低於所有通道值，避免消費端誤把它排到通道之前）。
- **house overlay 的方向語意**：`a_planets_in_b_houses` ＝ **A 的行星**落在 **B 的宮位**；
  `subject = "A"`（visitor）、`object = "B"`（owner）。`b_planets_in_a_houses` 反之。
  `house_system` 固定字面值 `"placidus"`。
- **角度點接觸的方向語意**：`angle_contacts_a_to_b` ＝ **A 的行星**接觸 **B 的角度點**；
  `subject = "A"`、`object = "B"`。`angle_contacts_b_to_a` 反之。
- **`participates_in_convergence`**：`synastry_aspect`、`angle_contact`、`hd_channel_connection` 為 `true`；
  `house_overlay`、`hd_center_state` 為 `false`，且其 `ease_or_tension` 一律 `mixed`。

### 人類圖連結判定

對每一條 `CHANNELS` 中的通道（閘門對，以 `lo-hi` 表示），令 `a` ＝ A 持有的該通道端點數（0–2）、
`b` ＝ B 持有的端點數。同一閘門被多顆行星啟動仍只算一個 active gate。完整 9 格：

| `a` \ `b` | 0 | 1 | 2 |
|---|---|---|---|
| **0** | `none` | `none`（B 單懸閘門） | `dominance`（owner = B） |
| **1** | `none`（A 單懸閘門） | 互補兩端 → `electromagnetic`；同一閘門 → `none` | `compromise`（owner = B） |
| **2** | `dominance`（owner = A） | `compromise`（owner = A） | `companionship` |

- `dominance` ＝ **一方持有整條通道、另一方一端都沒有**。
- `full_channel_owner` 為 `raw_fact` 欄位，值域 `"A"|"B"|null`；
  `compromise` 與 `dominance` 時為持有完整通道的一方，其餘一律 `null`。
- `none` 的通道**不輸出** `channel_connections[]` 元素；每條通道至多出現一次。
- `subject`／`object`：有 owner 時 `subject` ＝ owner、`object` ＝ 另一方；
  `electromagnetic` 與 `companionship` 無方向，固定 `subject = "A"`、`object = "B"`。
- `ease_or_tension` 依 `companionship=ease`／`electromagnetic=mixed`／`dominance=tension`／`compromise=tension`。
- **`center_states` 的 `state` 值域**：`a_defined`（僅 A 自身定義）／`b_defined`（僅 B 自身定義）／
  `both_defined`（雙方各自皆已定義）／`defined_by_merge`（雙方皆未定義，合併後才定義）／
  `undefined`（合併後仍未定義）。`causing_channels` 於 `defined_by_merge` 時為造成定義的通道字串陣列，
  其餘為 `[]`。9 個中心**全部輸出**，每個恰好一筆。

### 時間未知與 `data_confidence`

- **兩側時間皆已知 → 所有 feature `0.95`。**
- **任一側時間未知**（含兩側皆未知）時，該未知側的**整張盤**一律以該側 `tz` 的**當地 12:00** 為出生時刻計算
  （行星位置、人類圖 personality／design 閘門皆然）。此情境下：
  - 有**未知側月亮**參與的 feature → `0.6`（位置本身即為推估，必須誠實揭露）。
  - **其餘所有 feature → `0.85`**（含只牽涉已知側月亮者）。時間未知是整份結果的性質，
    不因某筆 feature 恰好只碰到已知側而回到 `0.95`。
- **時間相依 feature（house overlay、角度點接觸）在任一側時間未知時不產出**，
  對應陣列為 `[]` 並在 `unavailable` 填入 token。
- **人類圖通道的窮盡切分**：時間未知時，只要**任一端點**由**時間未知側**的
  `{月亮, 水星, 金星, 火星}` 之一啟動 → `0.6`；否則 → `0.85`。
  兩側皆未知時，任一側命中即 `0.6`。此切分對 13 個啟動天體
  （日、月、水、金、火、木、土、天、海、冥、地球、北交點、南交點）皆有值。
- **`hd_center_state` 的 `data_confidence`**：兩側時間皆已知 `0.95`；任一側未知時**固定 `0.85`**
  （中心狀態是結構性描述，不隨個別閘門的啟動天體變動）。
- **`unavailable` 的三個固定 token**：`house_overlay`（落宮未產出）、`angle_contacts`（角度點接觸未產出）、
  `hd_lines`（人類圖由未知側月／水／金／火啟動的閘門可能位移，line 級精度不可得；
  對應上述 `0.6` 的降級，並非另一個未輸出的欄位）。時間已知時為空陣列。

### CLI 雙人輸出

- CLI `--json` 的雙人輸出 ＝ HTTP `/synastry` response **完全相同的物件**（同鍵、同值、同順序）。
  兩者共用 `build_synastry_json()`，HTTP 層只負責認證、輸入解析與狀態碼。
- CLI **非 `--json`（Markdown）模式在雙人參數下不支援**：直接 exit `2` 並在 stderr 說明
  「synastry 模式僅支援 `--json`」。理由：Markdown 是給人讀的單盤排版，
  為合盤另造一套排版會產生第二個沒有 oracle 的輸出路徑。

### 完整度、錯誤與安全

- **`evidence_completeness`**：`aspects` 非空且 `unavailable` 為空 → `full`；
  `unavailable` 非空**或** `aspects` 為空 → `partial`。**引擎只會吐這兩個值**；
  第三態由消費端判定。`partial` 一律仍回 **HTTP 200**。
- **錯誤 body 形狀**：4xx 一律
  `{"ok": false, "error": "<token>", "field": "<欄位名或 null>", "detail": "<人可讀說明>"}`；
  5xx 為 `{"ok": false, "error": "<token>", "message": "<固定字串>"}`。
  `error` 為固定可 parse 的 token，消費端只讀它。

  | 情況 | status | `error` | `field` |
  |---|---|---|---|
  | body 非 JSON | 400 | `invalid_json` | `null` |
  | body 非物件；`person_a`／`person_b` 缺漏或非物件 | 400 | `invalid_input` | `person_a` / `person_b` |
  | 缺 `date`／`tz`／`lat`／`lon`／`gender` | 400 | `invalid_input` | 該欄位名 |
  | `time` 存在但格式不合（`"25:99"`／`"abc"`） | 400 | `invalid_input` | `time` |
  | `tz`／`lat`／`lon` 超界或非有限、年份超出 1900–2100 | 400 | `invalid_input` | 該欄位名 |
  | 金鑰缺漏或錯誤 | 401 | `unauthorized` | `null` |
  | `ENGINE_API_KEY` 未設且未開 `ENGINE_ALLOW_OPEN` | 503 | `not_configured` | `null` |
  | 內部錯誤 | 500 | `internal_error` | — |

  `time` 格式錯誤**不視為時間未知**：靜默降級會讓打錯字的呼叫者拿到殘缺解讀卻以為完整。
  `person_a` 與 `person_b` 完全相同 → **接受並照常計算**（所有相位 orb 為 0 是正確結果）。
  500 的 `message` 為固定字串 `"synastry computation failed"`，**不得回傳 `str(exc)`**：
  既有 `/chart` 的 500 會外洩如 `"placidus undefined at high latitude"` 之類的內部訊息。
  實際例外經 `capture_exception` 送 Sentry。
- **重試語意**：`400` 與 `401` **不可重試**（輸入或憑證本身有問題）；
  `503 not_configured` **不可重試**（伺服器設定錯誤，需人介入）；
  `500 internal_error` **可重試**；上游 proxy 產生的 5xx／逾時**可重試**。
- **冪等性**：同一 body 連續兩次 `POST /synastry` 的回應 byte-for-byte 相同。
- **安全/權限**：沿用 `X-Engine-Key`；`ENGINE_API_KEY` 未設時 fail-closed `503`，
  除非 `ENGINE_ALLOW_OPEN=1`。輸入驗證共用 `scripts/validation.py`。
  無新增 secret、無新增外部呼叫、無網路存取。
- **邊界/效能**：0°/360° 跨界以最短弧判定；每人單盤在一次請求內只算一次並共用；
  合盤為 O(11×11) 組合，無 rate limit 需求；不得拖慢既有 `/chart` 路徑。
- **type → strategy 對照**（引擎現有 `human_design()` 只算 type 與 authority，無 strategy，此表為新增）：

  | type | strategy |
  |---|---|
  | 顯示者 | 告知後行動 |
  | 生產者 | 等待回應 |
  | 顯示生產者 | 等待回應後告知 |
  | 投射者 | 等待被邀請 |
  | 反映者 | 等待一個完整月亮週期 |

## Testing Decisions

| Module | 要測? | 測什麼外部行為 | Prior art |
|---|---|---|---|
| `scripts/semantics.py` | ✅ | 給定行星對／相位／orb／時間已知與否，回傳的 `dimensions`（含順序）／`salience`／`ease_or_tension`／`data_confidence`／`feature_id` 逐欄位正確；orb 覆蓋規則正確 | `tests/test_validation.py` |
| `scripts/synastry.py` | ✅ | 五個西洋陣列與 HD 輸出的內容、方向、不對稱性、排序、去重；9 格連結判定；時間未知時的 `unavailable` | `tests/test_engine_astronomy_contract.py` |
| `scripts/chart_engine.py` | ✅ | 單人輸出與 `examples/sample-output.json` 僅差 `schema_version`；單人無 `synastry` 鍵；CLI 與 HTTP 雙人輸出一致 | `tests/test_json_output.py` |
| `scripts/validation.py` | ✅ | 五個必填 `-b` flag 部分給出時 exit 2；`time` 省略／`null`／`"unknown"` 視為未知；格式錯誤回錯 | `tests/test_validation.py` |
| `server.py` | ✅ | `POST /synastry` 的成功／錯誤對照表逐列／冪等性／`partial` 回 200；`/health`；`/chart` deep-equal 回歸 | `tests/test_server.py` |
| `tests/fixtures/themes-v1.json` | ✅ | `THEMES_V1` 與 checked-in 清單逐字相同（含順序） | `tests/test_readme_sync.py` |
| golden fixtures | ✅ | `golden_example.json` diff 僅 `schema_version` 一行；`golden_example.md` 零 diff | `tests/test_engine_astronomy_contract.py` |
| 授權與離線守衛 | ✅ | swisseph 掃描涵蓋新模組；`build_synastry_json` 無網路存取 | `test_runtime_and_test_sources_do_not_import_swisseph`, `tests/test_sidecar_no_network.py` |

## Vertical Slices

### Slice E1 — 引擎 synastry 模式骨架
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #18, #19, #22, #23, #24, #27, #30
- **Acceptance criteria**:
  - [ ] CLI 新增 `--date-b/--tz-b/--lat-b/--lon-b/--gender-b`（五者必填）與 `--time-b`（optional）；五個必填者全給才進入 synastry 模式，部分給出 → exit 2 並指明缺哪些（測試：給 3 個必填 flag → exit 2 且訊息含缺少的兩個 flag 名）。
  - [ ] `--time-b` 省略或給 `unknown` → B 側時間未知；synastry 模式下 `--time`（A 側）同樣可省略或給 `unknown`。單人模式的 `--time` 維持必填、行為不變（測試各一則）。
  - [ ] synastry 模式下未給 `--json` → exit 2 並在 stderr 說明僅支援 `--json`（測試一則）。
  - [ ] **單人模式不輸出 `synastry` 鍵**；雙人模式輸出 `synastry` 物件（本 slice 內容可為空陣列，鍵齊全）。
  - [ ] `schema_version` 改為 `"1.2"`，測試斷言 `startswith("1.")`。
  - [ ] `scripts/chart_engine.py` 與 `server.py` 的**執行期** `schema_version` 字面值不再出現 `"1.1"`（測試僅掃這兩個檔）。
  - [ ] `tests/test_engine_astronomy_contract.py` 的 **live 斷言**（`got["schema_version"]`）改為 `"1.2"`；同檔對 **fixture** 的 `engine_schema_version == "1.1"` 與模擬 envelope 常數**維持不變**（測試斷言該 fixture 檔未被改動）。
  - [ ] `AGENTS.md`／`README.md`／`scripts/mcp_server.py` docstring／18 份翻譯 README 中敘述**當前**版本之處同步為 1.2；`tests/test_readme_sync.py` 保持綠。各 README 版本歷史敘述、`docs/specs/2026-07-13-*`、`tests/fixtures/ephemeris_baseline.json` 不得被改動（測試斷言三者未變）。
  - [ ] 單人輸出與 `examples/sample-output.json` **parse 後 deep-equal，僅排除 `schema_version`**；該檔 git diff 僅允許 `schema_version` 一行。
  - [ ] **不啟用 `sort_keys`**；單人 `--json` 輸出的鍵序與浮點表示與變更前**逐 byte 相同，唯一差異為 `schema_version` 的值**（測試以變更前的 golden bytes 做字串替換後比對）。
  - [ ] `tests/fixtures/golden_example.json` 重新產生且 diff **僅限 `schema_version` 一行**；`tests/fixtures/golden_example.md` **零 diff、byte 相同**（測試各一則）；`GOLDEN_PROVENANCE.md` 記錄本次再生的日期、原因與 diff 範圍。
  - [ ] 同一組雙人輸入連跑兩次，CLI stdout byte-for-byte 相同。
  - [ ] `test_runtime_and_test_sources_do_not_import_swisseph` 的掃描清單擴充至 `scripts/synastry.py` 與 `scripts/semantics.py`（測試斷言清單含這兩個檔）。
  - [ ] 既有測試全綠，含 `test_example_matches_pre_change_golden_bytes`。

### Slice E2 — 西洋跨盤相位
- **Type**: AFK
- **Blocked by**: E1
- **User stories**: #1, #2, #3, #4, #5, #6, #24, #25, #26, #28, #30
- **Acceptance criteria**:
  - [ ] 對 A 的 11 個天體與 B 的同集合計算角距，產出 `synastry.western.aspects[]`，每筆通過 §evidence schema 的驗證函式。
  - [ ] 天體集合固定為 11 個，**南交點不參與**（測試斷言輸出中無南交點 evidence）。
  - [ ] orb 依 §orb 判定順序：北交點任一端 → 用 2° 且不套 +1°；否則用相位 orb 並在日月參與時 +1°（上限 7°）。測試涵蓋「太陽刑北交點」（用 2° 非 6°）界內／界外各一，以及「日月參與 +1° 但不超過 7°」一則。
  - [ ] **`aspects[]` 不含角度點接觸**；測試斷言不出現 `asc`/`desc`/`mc`/`ic`。
  - [ ] 兩端皆為外行星不輸出；木星與土星**參與**（測試各一則）。**不計算 Chiron**。
  - [ ] 一般天體對 `planet_weight = max(w_a, w_b)`；測試以 canonical 範例（水星四分土星 orb 0.7）餵入計算函式，斷言 `salience == 0.882`、`dimensions == ["communication","commitment_stability","autonomy_boundary"]`（含順序）、`data_confidence == 0.95`、`raw_fact.aspect == "square"`、`feature_id == "w-syn-a-mercury-square-b-saturn"`。
  - [ ] 北交點任一端 → `planet_weight == 0.5`（測試：北交點對金星，斷言不是 0.9）。
  - [ ] `orb_weight` 公式測試涵蓋 orb=0（權重 1）、orb=max（權重 0）、orb 略超（不入列）。
  - [ ] 0°/360° 跨界：A 在 359.5°、B 在 0.5° 判為合相 orb 1.0°，斷言不算成 359°。
  - [ ] **禁用欄位名遞迴掃描**：走訪整個 response 的所有 key，斷言不含 `interpretive_valence`、`score`、`compatibility`、`percentage`、`rating`、`total`、`grade`、`吉凶` 任一（大小寫不敏感）。
  - [ ] `feature_id` 符合 `^[a-z]+-[a-z0-9-]+$`、依 §feature_id 模板與 §slug 表產生、同輸入決定性，且**單一 response 內全域唯一**（測試以完整回應斷言集合大小 == 元素數）。
  - [ ] `aspects[]` 依 `salience` desc → `feature_id` asc 排序（測試以人工建構的同 salience 兩筆斷言 tie-break）。
  - [ ] 對至少 5 組樣本盤斷言每筆 evidence 的 `dimensions` ⊂ `themes-v1`，且依 §dimensions 規則（來源表列內順序、A 先 B 後、首次出現去重）產生。
  - [ ] `data_confidence` 三組測試：兩側已知 → `0.95`；**未知側月亮**參與 → `0.6`；已知側月亮參與但另一側未知 → **`0.85`**。
  - [ ] `scripts/semantics.py` 的 `THEMES_V1` 與 `tests/fixtures/themes-v1.json` 逐字相同（含順序）。
  - [ ] `build_synastry_json` 在無網路環境下可完整執行（測試比照 `tests/test_sidecar_no_network.py` 的 socket guard）。
  - [ ] 小行星與次要相位預設不輸出。

### Slice E3 — 西洋雙向 house overlay 與角度點
- **Type**: AFK
- **Blocked by**: E2
- **User stories**: #7, #8, #11, #12, #13, #14, #28
- **Acceptance criteria**:
  - [ ] 輸出 `a_planets_in_b_houses[]` 與 `b_planets_in_a_houses[]` 兩個獨立陣列，每個元素通過 evidence 驗證函式並含 `raw_fact: { planet, house_number, house_system: "placidus" }`（`house_number` 為 1–12 整數）。
  - [ ] 方向語意：`a_planets_in_b_houses` 的每筆 `subject == "A"`（visitor）、`object == "B"`（owner），`feature_id` 形如 `w-ovl-a-<planet>-in-b-h<n>`（測試斷言）。
  - [ ] house overlay 的 `salience == round(planet_weight × 0.8, 3)`、`ease_or_tension == "mixed"`、`participates_in_convergence == false`（測試各一則）。
  - [ ] 角度點接觸的 `salience == round(orb_weight × 0.5, 3)`（`planet_weight` **固定 0.5**，不取 max），`participates_in_convergence == true`（測試一則手算對照：太陽拱 ASC orb 2.0，`orb_weight = 1-(2/4)² = 0.75`，`salience = 0.375`，並斷言不是 0.75）。
  - [ ] 構造 A 火星落 B 十宮但 B 火星不落 A 十宮的資料，斷言兩陣列不對稱。
  - [ ] 角度點接觸雙向分開，orb 行星 3°／日月 4°；兩端皆為特殊天體時取較小者（北交點對 ASC → 2°，測試一則）。測試涵蓋「月亮拱 ASC 用 4° 非 6°」界內／界外各一。
  - [ ] **角度點對角度點不產生 evidence**（測試斷言）。
  - [ ] 兩類的天體集合皆為與 `aspects[]` 相同的 11 個（測試斷言北交點有出現、南交點沒有）。
  - [ ] 任一側時間未知時，這兩類**不產出**：四個陣列為 `[]`（鍵仍存在），`synastry.unavailable == ["house_overlay","angle_contacts","hd_lines"]`（固定順序），`evidence_completeness == "partial"`，**HTTP status 為 200**。
  - [ ] `evidence_completeness` 判定：`aspects` 非空且 `unavailable` 為空 → `full`；`unavailable` 非空**或** `aspects` 為空 → `partial`（兩則測試，含「兩人生日相差極遠導致 aspects 為空仍判 partial 且回 200」）。引擎永不輸出第三個值。
  - [ ] 四個陣列皆依 `salience` desc → `feature_id` asc 排序（測試各一則）。
  - [ ] 同輸入兩次執行結果 byte 相同。

### Slice E4 — 人類圖四種連結與合併中心
- **Type**: AFK
- **Blocked by**: E1
- **User stories**: #2, #9, #10, #26, #28, #29
- **Acceptance criteria**:
  - [ ] 依 §人類圖連結判定的 9 格表判定；測試涵蓋全部 9 格（含 `(2,0)`／`(0,2)` → `dominance`、`(1,0)`／`(0,1)` → `none`）。
  - [ ] `(1,1)` 兩格分歧：互補兩端 → `electromagnetic`；雙方持同一個單閘門 → `none`。
  - [ ] 同一閘門被多顆行星啟動仍只算一個 active gate。
  - [ ] 一人完整一人單端 → `compromise` 且 `raw_fact.full_channel_owner` 為完整通道持有方，斷言方向正確且不判成 `dominance`；一人完整一人零端 → `dominance` 且 owner 正確。
  - [ ] `full_channel_owner` 值域 `"A"|"B"|null`；`electromagnetic`／`companionship` 時為 `null`。
  - [ ] `raw_fact.a_gates`／`b_gates` 依閘門編號 asc、`centers` 依 lo→hi 中心順序（測試斷言）。
  - [ ] 每條通道在 `channel_connections[]` 至多出現一次（以 `raw_fact.channel` 斷言集合大小 == 元素數）；`none` 者不輸出。
  - [ ] 輸出 `center_states[]`：**9 個中心全部出現、每個恰好一筆**，順序為頭→邏輯→喉→G→意志→情緒→薦骨→脾→根（測試逐筆斷言 `raw_fact.center` 的完整期望序列）；`state` ∈ 五個值；`causing_channels` 於 `defined_by_merge` 時非空且依字串 asc（測試斷言其順序）、其餘為 `[]`。
  - [ ] `center_states` 的 evidence：`salience == 0.5`、`ease_or_tension == "mixed"`、`participates_in_convergence == false`、`subject`／`object` 皆為 `null`、`dimensions` ＝ 該中心那一列的 theme、`feature_id` 形如 `hd-ctr-<center_slug>-<state_slug>` 且不含底線（測試各一則）。
  - [ ] `participants.person_x` 輸出 `type`／`strategy`／`authority`／`split_bridges`／`hanging_gates_completed`；`strategy` 依 §type → strategy 表（測試涵蓋五種 type）；`authority` 值域為引擎現行六個中文字面值之一。
  - [ ] `split_bridges` 依 §定義（該人自身被切分的定義中心，因合併新形成、連接原本不同分量的通道）產生，元素為 `{channel, centers}`，依 `channel` 字串 asc；自身單一定義或無定義時為 `[]`（測試：以一組二分人資料斷言逐值期望清單，另一組單一定義斷言 `[]`）。
  - [ ] `hanging_gates_completed` 為**該人自身的懸掛閘門被對方補足**者，元素為 `{own_gate, partner_gate, channel}`，依 `own_gate` asc（測試：以一組 electromagnetic 資料斷言 A 與 B 兩側各自的逐值期望清單，並斷言方向不互換）。
  - [ ] **每筆 `channel_connections[]` 通過與西洋側同一個 evidence 驗證函式**；`method_version == "human-design-synastry-v1"`。
  - [ ] `dimensions` ＝ 連結類型 theme → lo 閘門中心 theme → hi 閘門中心 theme，首次出現去重（測試一組手算對照，斷言完整期望陣列）；`ease_or_tension` 依四型對照。
  - [ ] 時間未知時通道的 `data_confidence` 依**窮盡切分**：任一端點由**未知側**的 `{月,水,金,火}` 啟動 → `0.6`；否則 → `0.85`（測試四則：未知側月啟動 0.6、未知側土星啟動 0.85、未知側木星啟動 0.85、**只有 B 未知而 A 側月亮啟動 → 0.85**）。
  - [ ] `hd_center_state` 的 `data_confidence`：兩側已知 `0.95`、任一側未知 `0.85`（測試各一則）。
  - [ ] 禁用欄位名遞迴掃描（同 E2 名單）在 HD 側亦通過。
  - [ ] 不輸出 Incarnation Cross 配對。

### Slice E5 — 引擎 HTTP 契約
- **Type**: AFK
- **Blocked by**: E2, E3, E4
- **User stories**: #1, #11, #12, #13, #14, #15, #16, #17, #20, #21, #22, #24
- **Acceptance criteria**:
  - [ ] 新增 `POST /synastry`，body 為 `{ "person_a": {...}, "person_b": {...} }`。
  - [ ] `time` 為 optional：省略、`null` 或 `"unknown"` 皆視為時間未知（測試三則）；格式不合回 `400`（斷言**不**被當成時間未知）。
  - [ ] response 頂層結構固定為 §API contract 所列形狀，含頂層 `ok: true`（測試一則）。
  - [ ] `person_a`／`person_b` 在 `western`／`human_design`／`ziwei` 中固定為**空物件**（斷言 `== {}`）。
  - [ ] `ziwei.status == "not_computed"` 且 `ziwei.methodology_note` 等於固定字串（斷言字面值相等）。
  - [ ] `synastry.unavailable` 為固定 token 陣列且順序固定，時間已知時為空陣列（兩則）；非空時各陣列鍵**仍存在且為 `[]`**。
  - [ ] **錯誤對照表逐列測試**：非 JSON→`invalid_json`；缺 `person_b`→`invalid_input`/`field="person_b"`；`person_a` 非物件→`invalid_input`（斷言**不是** 500）；缺 `date`→`invalid_input`/`field="date"`；`lat` 超界→`invalid_input`；`time` 格式錯→`invalid_input`/`field="time"`；`person_a == person_b` → 200 並照常計算。
  - [ ] 內部錯誤回 `500`，body 為 `{"ok": false, "error": "internal_error", "message": "synastry computation failed"}`；斷言 `message` **不含**例外字串（以極地座標觸發 `placidus undefined at high latitude`）。
  - [ ] 沿用 `X-Engine-Key`；無金鑰與錯誤金鑰各回 401 且 `error == "unauthorized"`；`ENGINE_API_KEY` 未設時回 503 且 `error == "not_configured"`，設 `ENGINE_ALLOW_OPEN=1` 時放行（測試各一則）。
  - [ ] 每人的 `name`／`target`／`ziwei_day_divide` 被接受且不影響輸出（測試：給與不給兩次結果 byte 相同）。
  - [ ] 冪等性：同一 body 連續兩次 POST，回應 byte-for-byte 相同。
  - [ ] **CLI／HTTP 一致性**：同一組輸入（含時間未知情境）的 CLI `--json` stdout 與 `/synastry` response body **parse 後 deep-equal**（測試兩則：時間已知與時間未知各一）。
  - [ ] **`/health` 新增 `schema_version` 欄位，既有 `ok` 欄位不變**（斷言兩鍵皆在且 `schema_version == "1.2"`）。
  - [ ] **`/chart` 回歸**：成功回應 parse 後與 `examples/sample-output.json` deep-equal，僅排除 `schema_version`。
  - [ ] `AGENTS.md` 記載完整 request/response/error schema，含五個 `method` 的 `raw_fact` 與 `feature_id` 模板、slug 表、排序規則、錯誤 token 與重試語意。
  - [ ] **部署漂移防護**：新增可離線執行的回歸驗證入口（具名 pytest 子集），涵蓋 `/chart` 既有成功路徑與 `examples/sample-output.json` 對齊；`DEPLOY-HETZNER.md` 的驗證章節指明重建部署後必須執行它並保留輸出為證據。

## Out of Scope

- 前端合盤圖、關係圖表視覺化或任何互動介面。
- composite chart、Davison chart、次限推運、行運合盤等衍生合盤技法。
- 占星或人類圖的解讀文案、AI 解盤、prompt、LLM 呼叫。
- 任何相容度分數、配對百分比、吉凶總分欄位。
- 紫微合盤（固定 `not_computed`）。
- Chiron 與小行星、次要相位。
- 地理編碼與時區查詢（呼叫端責任，既有邊界不變）。
- `importance_for_intent`、`named_school`／`experimental` 的 `method_consensus` 值。
- 三人以上的多方合盤（此 endpoint 固定兩人）。
- **CLI 的 Markdown 合盤排版**（雙人模式僅支援 `--json`）。
- **MCP surface（`scripts/mcp_server.py`）與本地 web UI（`webapp.py`）維持單盤**，
  僅 `mcp_server.py` 更新 docstring 字面值。
- 消費端 life-web 的任何變更（W1–W3 已在另一個 flow 完成並驗證）。
- 把 `DEPLOY-HETZNER.md` 目前未提交的主機更正納入本分支（見 §Further Notes）。
- 跨系統收斂判定（`converged`／`diverged`／`mixed`／`no_direction`／`not_computed`）——
  那是消費端的計算，引擎只提供 `participates_in_convergence` 與 `ease_or_tension` 兩個輸入。

## Further Notes

### 與上游的偏離（五處）

1. **角度點 `salience` 的 `planet_weight`**：上游規則段寫「固定 0.5」、E3 的 AC 寫 `max(行星權重, 0.5)`，互斥。
   本 spec 採**固定 0.5**：所有行星權重皆 ≥ 0.5，取 max 會讓角度點端完全不影響結果，
   使上游自己給的正當理由不成立。
2. **`sort_keys`**：上游要求開啟，但引擎現行鍵序為插入序，開啟會與「單人輸出僅差 `schema_version`」互斥
   並炸掉既有 golden byte 測試。本 spec **不啟用**，改以 CPython dict 保序達成同一個決定性目標。
3. **CLI 時間未知**：上游 E1 要求六個 `-b` flag 全給，但 E5 允許 HTTP 省略 `time`，
   導致時間未知的 HTTP 結果無法用 CLI 離線重現。本 spec 把 `--time-b` 改為 optional。
4. **HD `data_confidence` 的窮盡切分**：上游只列「月／水／金／火」與「日與外行星」，
   木星／土星／地球／交點無值，且未區分是哪一側。本 spec 補為窮盡且綁定「時間未知側」。
5. **`dominance` 的產生規則**：上游只給 theme／權重對照，未給任何產生條件，
   且 9 格表的 `(2,0)`／`(0,2)` 未指派。本 spec 補上完整判定表。

以上皆不影響消費端已驗證的 candidate：消費端讀 `salience` 的**值**、不重算它的**算式**，也不呼叫 CLI。
偏離 1 會讓角度點接觸的 `salience` 較小，可能使個別 theme 落到消費端 0.45 門檻之下 ——
這是**正確**的結果（角度點本就該是低權重訊號），不是回歸。

### 已知風險

**風險 1 — 部署漂移。** 線上 `engine-life.aicycle.cc` 的映像是 **2026-06-29** build 的，
而 repo 已在 `56a8d17`（2026-07-13）。照 `DEPLOY-HETZNER.md` 重建部署會**一併把這一個多月的既有變更推上 prod**，
而 prod 服務現有免費與付費單盤客戶。E5 已把「重建後跑既有回歸驗證」列為驗收條件，
但這只讓風險被測到，不會讓風險消失；部署當下必須把 `/chart` 與 `examples/sample-output.json` 的比對結果留成證據。

**風險 2 — `DEPLOY-HETZNER.md` 在 git 裡是過期的。** 版本庫中的版本仍指向已除役的主機
`acejou@157.90.157.99` 與 `/home/acejou/life-chart-engine`；正確的是 `root@49.12.196.102` 與
`/opt/life-chart-engine`（Hermes box，tunnel token 存 1Password `LIFE_ENGINE_TUNNEL_TOKEN`）。
這份更正目前只存在於 base repo 的**未提交工作區**，不在本分支。
本 flow **刻意不吸收那份未提交變更**（不屬於本 feature 的 diff），但任何人照 git 版本的文件部署都會連錯主機。
這需要一次獨立的 commit 處理。

**風險 3 — `themes-v1` 雙份常數。** 引擎與消費端各持一份且必須逐字相同（見 ADR-0001）。
本 repo 以 `tests/fixtures/themes-v1.json` 為 checked-in 對照；引擎側改動即為消費端的破壞性變更。

**風險 4 — golden fixture 再生。** `golden_example.json` 是「變更前」的 byte 證據，
本次因 1.2 bump 必須再生；`golden_example.md` 則必須零 diff。
若再生時混入 `schema_version` 以外的差異，該測試就從回歸防線退化成自我證明。

### 上線順序（硬性）

引擎 `/synastry` 必須**先於** life-web 上線。life-web 的 `synastryReading` 無條件呼叫 `/synastry`，
且其合盤 cache 前綴已由 `synastry-v2-` 改為 `synastry-v3-`，
所以引擎未上線時 life-web 一上線，**連已付費的既有合盤客戶都會拿到 502/503**。
部署後的驗收訊號：`curl https://engine-life.aicycle.cc/health` 回的 JSON 含 `schema_version: "1.2"`。

**Node.js ≥ 18 仍是 `/chart` 與 CLI 單盤的硬性 runtime 需求**（紫微 sidecar），本 feature 不改變此前提；
`/synastry` 不走該 sidecar，無 per-request Node 依賴。
