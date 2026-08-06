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
14. As a consumer product, I want an empty `aspects` array to count as `partial` and still be served, so that a determinate result is never turned into a permanent 503 for that user.
15. As a consumer product, I want the response top level to keep `western` / `human_design` / `ziwei` keys and a `1.x` `schema_version`, so that my existing type guard passes unchanged.
16. As a consumer product, I want 紫微 explicitly reported as `not_computed` with a fixed methodology note, so that its absence reads as a deliberate boundary rather than a bug.
17. As a consumer product, I want internal errors to return a fixed machine-parsable `error` string and a documented retryable/not-retryable status split, so that I can decide whether to retry without parsing human prose.
18. As an existing single-chart caller, I want `/chart` and the CLI's single-person output to stay byte-identical apart from the `schema_version` value, so that this feature cannot silently change my existing charts.
19. As an existing single-chart caller, I want the single-person output to contain no `synastry` key at all, so that my parser sees no new optional branch.
20. As an operator, I want `/health` to report `schema_version`, so that I can verify from outside which contract a deployed instance actually serves.
21. As an operator, I want the same `X-Engine-Key` auth and the same fail-closed behaviour on the new endpoint, so that it cannot become an open compute endpoint.
22. As a CLI user, I want to reproduce any HTTP synastry result offline, including the time-unknown case, so that determinism is verifiable without the server.
23. As a CLI user, I want partially supplied `-b` flags to fail loudly naming what is missing, so that I never get a one-person chart when I asked for two.
24. As a maintainer, I want the same two-person input to produce byte-identical output across runs on both the CLI and HTTP, so that determinism remains testable rather than aspirational.
25. As a maintainer, I want the theme ontology asserted against a checked-in fixture in this repo, so that engine and consumer cannot drift apart unnoticed.
26. As a maintainer, I want no compatibility-score or fortune-scoring field anywhere in the schema, so that the product cannot later grow a "relationship score" through the back door.
27. As a maintainer, I want the existing golden-byte regression retired or regenerated explicitly with its provenance updated, so that a green test suite never depends on a fixture nobody re-derived.
28. As a maintainer, I want every output array's sort order pinned, so that "deterministic" is a property I can assert rather than an accident of dict iteration.

## Modules

| Module | 職責（一句） | 公開介面（窄） | 新建/修改 |
|---|---|---|---|
| `scripts/synastry.py` | 由兩份已驗證輸入算出完整 synastry 區塊（唯一的關係運算入口） | `build_synastry(inp_a, inp_b) -> dict` | 新建 |
| `scripts/semantics.py` | `semantics-v1` 規則本體：theme 表、orb 判定順序、權重、`salience`、`data_confidence`、`feature_id` 組成、type→strategy | `THEMES_V1`, `evidence(...)`, `orb_weight(orb, max_orb)`, `resolve_max_orb(a, b, aspect)`, `feature_id(method, **parts)`, `STRATEGY_BY_TYPE` | 新建 |
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
  需要更新版本字面值的**執行期來源**只有兩處：`scripts/chart_engine.py`（成功與 `ok:false` 兩個 envelope）
  與 `server.py`（500 envelope）。**文件與敘述性提及不在「無殘留」斷言範圍內**（見下方「1.1 殘留斷言的範圍」）。
- **序列化：不啟用 `sort_keys`。** 上游要求 `sort_keys=True`，但引擎現行輸出的鍵序是插入序
  （`ok, schema_version, input, western, human_design, ziwei, meta`），開啟排序會改動整份 byte stream，
  與 User story #18 的「僅 `schema_version` 有差異」直接互斥，也會炸掉既有的
  `test_example_matches_pre_change_golden_bytes`。CPython 3.7+ 的 dict 保序，插入序**本身就是決定性的**，
  故決定性目標不需要 `sort_keys` 即可達成。**浮點格式維持現行 `json.dumps` 預設 repr**，
  不做額外格式化；只有 `salience` 與 `data_confidence` 在**計算時**已 `round(..., 3)`。
- **golden byte fixture 的處置**：`tests/fixtures/golden_example.json` 與 `golden_example.md` 內含
  `schema_version "1.1"`，故 1.2 bump 必然使 `test_example_matches_pre_change_golden_bytes` 變紅。
  處置為**重新產生該兩個 fixture**，其 diff 必須**僅限 `schema_version` 字面值那一行（.md 為對應那一處）**，
  並在 `tests/fixtures/GOLDEN_PROVENANCE.md` 記錄本次再生的原因、日期與 diff 範圍。
- **單人輸出回歸 oracle**：parse 後與 `examples/sample-output.json` deep-equal，**僅排除 `schema_version`**。
  `examples/sample-output.json` 不得重新產生（其 git diff 僅允許 `schema_version` 一行）。
- **單人模式不輸出 `synastry` 鍵**；雙人模式才輸出。
- **`1.1` 殘留斷言的範圍**：斷言限定在 `scripts/chart_engine.py` 與 `server.py` 的**執行期字面值**。
  以下位置合法保留 `1.1` 且不得誤殺：18 份翻譯 README 與 `README.md`／`AGENTS.md` 的版本歷史敘述、
  `docs/specs/2026-07-13-engine-polish-funnel-design.md`（歷史 spec）、`tests/fixtures/ephemeris_baseline.json`
  （星曆基線與 schema_version 無關）、以及測試中針對歷史行為的字面斷言。
  需一併更新的**非執行期**位置逐一列出：`AGENTS.md`（§1 identity 與 §4 output reference）、
  `README.md`（Output reference）、`scripts/mcp_server.py` 的 docstring。
  **18 份翻譯 README 是否需同步**：需要，因為 `tests/test_readme_sync.py` 已在守這條線；
  同步範圍限於其中敘述當前 `schema_version` 的欄位／表格，不改其版本歷史句。

### API contract — `POST /synastry`

Body `{ "person_a": {...}, "person_b": {...} }`，每人欄位同 `/chart`，但 `time` 為 optional。

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
- **`unavailable` 時各陣列仍存在且為 `[]`**，鍵永不消失。
- `synastry.human_design.participants.person_x` 為**非 evidence 的描述性物件**：
  `{ "type": str, "strategy": str, "authority": str, "split_bridges": [...], "hanging_gates_completed": [...] }`。
  它是 E4 的 type/strategy/authority 與 split bridge／hanging gate 清單的唯一落點。

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

此範例是**規則的產物，不是獨立來源**：`dimensions` ＝ 水星 `{communication}` ∪ 土星
`{commitment_stability, autonomy_boundary}`；`orb_weight = 1 - (0.7/5)² = 0.9804`，
`planet_weight = max(0.9, 0.8) = 0.9`，故 `salience = round(0.9804 × 0.9, 3) = 0.882`；
兩側時間已知且無月亮參與，故 `data_confidence = 0.95`。

- `system` ∈ `western|human_design`；`ease_or_tension` ∈ `ease|tension|mixed`；
  `method_consensus` ∈ `core|named_school|experimental`（本次一律 `core`）。
- **`method` 值域固定五個**，各自的 `method_version`、`subject`/`object`、`raw_fact` 與 `feature_id` 模板如下表。
  `subject`/`object` 值域為 `"A"|"B"`，非方向性的 `hd_center_state` 兩者皆為 `null`。

  | `method` | `method_version` | `subject` / `object` | `raw_fact` 欄位 | `feature_id` 模板 |
  |---|---|---|---|---|
  | `synastry_aspect` | `western-synastry-v1` | `"A"` / `"B"` | `planet_a`(str), `aspect`(str), `planet_b`(str), `exact_angle`(int), `actual_angle`(float), `orb`(float) | `w-syn-a-<planet_a>-<aspect>-b-<planet_b>` |
  | `house_overlay` | `western-synastry-v1` | owner / visitor（見下） | `planet`(str), `house_number`(int 1–12), `house_system`(`"placidus"`) | `w-ovl-<visitor>-<planet>-in-<owner>-h<house_number>` |
  | `angle_contact` | `western-synastry-v1` | `"A"` / `"B"` | `planet`(str), `angle`(`"asc"\|"desc"\|"mc"\|"ic"`), `aspect`(str), `exact_angle`(int), `actual_angle`(float), `orb`(float) | `w-ang-<subject>-<planet>-<aspect>-<object>-<angle>` |
  | `hd_channel_connection` | `human-design-synastry-v1` | 見「連結判定」 | `channel`(`"<lo>-<hi>"`), `link_type`(str), `a_gates`(int[]), `b_gates`(int[]), `centers`(str[2]), `full_channel_owner`(`"A"\|"B"\|null`) | `hd-chan-<lo>-<hi>-<link_type>` |
  | `hd_center_state` | `human-design-synastry-v1` | `null` / `null` | `center`(str), `state`(enum，見下), `causing_channels`(str[]) | `hd-ctr-<center_slug>-<state>` |

  `feature_id` 模板中的行星／中心名一律取**小寫 ASCII slug**（`Mercury`→`mercury`、`北交點`→`north-node`、
  `Solar Plexus`→`solar-plexus`），結果須符合 `^[a-z]+-[a-z0-9-]+$`。
  **同一個 response 內所有 `feature_id` 互異**（含雙向 overlay 與雙向角度點）。
- **不設 `interpretive_valence`**（與 `ease_or_tension` 同構）。
- `salience` / `data_confidence` 為 `0.0–1.0` float，一律 `round(..., 3)`。
- **`dimensions` 的順序與去重**：先取 A 側來源的 theme、再取 B 側來源的 theme，各自**依 `themes-v1` 的宣告順序**
  排列，重複者只保留首次出現。此規則使 `dimensions` 對同一輸入完全決定性。

### 陣列排序（每個陣列都必須有 total order）

| 陣列 | 排序鍵 |
|---|---|
| `aspects` | `salience` desc → `feature_id` asc |
| `a_planets_in_b_houses`, `b_planets_in_a_houses` | `salience` desc → `feature_id` asc |
| `angle_contacts_a_to_b`, `angle_contacts_b_to_a` | `salience` desc → `feature_id` asc |
| `channel_connections` | `salience` desc → `feature_id` asc |
| `center_states` | `raw_fact.center` 依 `themes-v1` 中心表的宣告順序 |
| `causing_channels` | `"<lo>-<hi>"` 字串 asc |
| `unavailable` | 固定 token 順序：`house_overlay`, `angle_contacts`, `hd_lines` |
| `split_bridges`, `hanging_gates_completed` | 閘門編號 asc |

`feature_id` 全域唯一，故上述每組排序鍵皆構成 total order，不存在未定義的平手。

### 主題 ontology `themes-v1`

10 個固定 ID，**宣告順序即為排序基準**：`communication`、`emotion_regulation`、`decision_power`、
`action_tempo`、`intimacy_attraction`、`autonomy_boundary`、`commitment_stability`、`money_division`、
`conflict_repair`、`timing_context`。

此 ontology 是**產品自訂的二次轉譯**，不是任何命理傳統原生的分類（見 ADR-0001）。
本 repo 以 `tests/fixtures/themes-v1.json` 作為 checked-in 對照清單，格式為
`{"themes": [<10 個 ID，依宣告順序>]}`；`scripts/semantics.py` 的 `THEMES_V1` 必須與之逐字相同。
該檔的來源是消費端的同名常數；兩邊任一方變更即為對方的破壞性變更，同步時機為變更當次。

- **西洋：行星 → theme**（相位的 `dimensions` ＝ 雙方行星各自 theme 的聯集）：

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
- **人類圖：中心 → theme**（`center_states` 的排序基準亦為此表的列順序）：

  | 中心 | themes |
  |---|---|
  | Head | `communication`, `decision_power` |
  | Ajna | `communication`, `decision_power` |
  | Throat | `communication`, `action_tempo` |
  | G（Identity） | `commitment_stability`, `autonomy_boundary` |
  | Heart／Ego | `money_division`, `decision_power` |
  | Sacral | `action_tempo`, `intimacy_attraction` |
  | Solar Plexus | `emotion_regulation`, `conflict_repair` |
  | Spleen | `timing_context`, `autonomy_boundary` |
  | Root | `action_tempo`, `emotion_regulation` |

  （引擎內部的中心名為中文：頭／邏輯／喉／G／意志／情緒／薦骨／脾／根，依序對應上表。）

### 西洋計算規則

- **相位 → `ease_or_tension`**：三分 120° = `ease`；六合 60° = `ease`；四分 90° = `tension`；
  對分 180° = `tension`；合相 0° = `mixed`。合相判 `mixed` 是因為它本質中性。
  **角度點接觸沿用同一張表**。house overlay 不適用（固定 `mixed`）。
- **參與 `aspects[]` 的天體集合固定 11 個**：太陽、月亮、水星、金星、火星、木星、土星、天王星、海王星、
  冥王星、**北交點**。**南交點不參與**（恆為北交點對沖，納入會系統性重複）。
  **角度點不進 `aspects[]`**，只出現在角度點接觸陣列。
- **house overlay 的天體集合**：與 `aspects[]` **相同的 11 個**（含北交點，不含南交點與角度點）。
- **角度點接觸的天體集合**：同上 11 個對 4 個角度點（ASC/DSC/MC/IC）。
  **角度點對角度點不產生 evidence**。
- **「外行星」＝天王星、海王星、冥王星**；木星與土星**參與**計算。**不計算 Chiron**。
- **orb 判定順序**（覆蓋規則）：
  1. 任一端為**角度點或北交點** → 用該天體的 orb（角度點 3°；日月對角度點 4°；北交點 2°），
     **不套用日月 +1°**。**兩端皆為特殊天體時取較小者**（例：ASC 對北交點 → 2°）。
  2. 否則 → 用相位 orb（合 6／沖 6／刑 5／拱 5／六合 3），日月任一參與則 +1°，絕對上限 7°。
  3. 兩端皆為外行星 → 不計分、不輸出。
- **`orb_weight = max(0, 1 - (actual_orb / max_orb)²)`**；角距一律以最短弧 `min(d, 360-d)` 計算。
- **行星權重**：日月 `1.0`；水金火 `0.9`；木土 `0.8`；天海冥 `0.6`；北交點與角度點 `0.5`。
- **`salience` 公式**：
  - **跨盤相位**：`round(orb_weight × planet_weight, 3)`。兩端皆為一般天體 → `planet_weight = max(w_a, w_b)`；
    **任一端為北交點 → 固定 `0.5`**（不取 max）。
  - **角度點接觸**：`round(orb_weight × 0.5, 3)`。`planet_weight` **固定 `0.5`**（角度點端的權重），
    **不取 max**。上游 E3 的 AC 寫成 `max(行星權重, 0.5)`，那與其自身的規則段互斥且會讓
    「已用低權重壓低角度點影響力」的正當理由失效（所有行星權重皆 ≥ 0.5，取 max 等於角度點端完全不影響結果）。
    `orb_weight` 以該接觸適用的 orb（行星 3°／日月 4°）為 `max_orb`。
  - **house overlay**：`round(planet_weight × 0.8, 3)`。落宮無 orb 概念，`0.8` 是相對精確相位的方法論折扣。
  - **人類圖通道**：固定 `companionship/electromagnetic = 0.9`、`dominance = 0.8`、`compromise = 0.7`。
  - **人類圖中心狀態**：固定 `0.5`。它不參與收斂判定，此值僅為滿足 evidence schema 的必填欄位，
    且刻意低於所有通道值，避免消費端誤把它排到通道之前。
- **house overlay 的方向語意**：`a_planets_in_b_houses` ＝ **A 的行星**落在 **B 的宮位**；
  該 evidence 的 `subject = "A"`（visitor，行星所有人）、`object = "B"`（owner，宮位所有人）。
  `b_planets_in_a_houses` 反之。`house_system` 固定字面值 `"placidus"`。
- **角度點接觸的方向語意**：`angle_contacts_a_to_b` ＝ **A 的行星**接觸 **B 的角度點**；
  `subject = "A"`、`object = "B"`。`angle_contacts_b_to_a` 反之。
- **`participates_in_convergence`**：`synastry_aspect`、`angle_contact`、`hd_channel_connection` 為 `true`；
  `house_overlay`、`hd_center_state` 為 `false`（兩者都沒有可比較的方向性強度），
  且其 `ease_or_tension` 一律 `mixed`。

### 人類圖連結判定

對每一條 `CHANNELS` 中的通道（閘門對 `(X, Y)`，以 `lo-hi` 表示），令 `a` ＝ A 持有的該通道端點數（0–2）、
`b` ＝ B 持有的端點數。同一閘門被多顆行星啟動仍只算一個 active gate。完整 9 格判定：

| `a` \ `b` | 0 | 1 | 2 |
|---|---|---|---|
| **0** | `none` | `none`（B 單懸閘門） | `dominance`（owner = B） |
| **1** | `none`（A 單懸閘門） | 互補兩端 → `electromagnetic`；同一閘門 → `none` | `compromise`（owner = B） |
| **2** | `dominance`（owner = A） | `compromise`（owner = A） | `companionship` |

- `dominance` ＝ **一方持有整條通道、另一方一端都沒有**。上游只給了 `dominance` 的 theme／權重對照
  卻未給產生規則，此處補上；`(2,0)`／`(0,2)` 兩格在上游亦未指派。
- `full_channel_owner` 為 **evidence 層欄位**，值域 `"A"|"B"|null`；
  `compromise` 與 `dominance` 時為持有完整通道的一方，其餘一律 `null`。
- `none` 的通道**不輸出** `channel_connections[]` 元素。
- 每條通道在 `channel_connections[]` 中**至多出現一次**。
- `channel_connections` 的 `subject`／`object`：有 owner 時 `subject` ＝ owner、`object` ＝ 另一方；
  `electromagnetic` 與 `companionship` 無方向，固定 `subject = "A"`、`object = "B"`。
- `dimensions` ＝ 連結類型 theme ∪ 該通道兩端中心的 theme，順序依 §dimensions 規則。
- `ease_or_tension` 依 `companionship=ease`／`electromagnetic=mixed`／`dominance=tension`／`compromise=tension`。
- **`center_states` 的 `state` 值域**：`a_defined`（僅 A 自身定義）／`b_defined`（僅 B 自身定義）／
  `both_defined`（雙方各自皆已定義）／`defined_by_merge`（雙方皆未定義，合併後才定義）／
  `undefined`（合併後仍未定義）。`causing_channels` 為造成合併後定義的通道字串陣列，
  非 `defined_by_merge` 時為 `[]`。9 個中心**全部輸出**，每個中心恰好一筆。

### 時間未知與 `data_confidence`

- 兩側時間皆已知 → `0.95`。
- 任一側時間未知時，該側月亮位置以**當地正午 12:00** 推估，凡有**該未知側的月亮**參與的 feature
  一律 `0.6`；只牽涉已知側月亮的 feature 不降級。其餘非時間相依 feature → `0.85`。
- **時間相依 feature（house overlay、角度點接觸）在任一側時間未知時不產出**，
  對應陣列為 `[]` 並在 `unavailable` 填入 token。
- **人類圖側的窮盡切分**：時間未知時，通道的 `data_confidence` 取決於啟動其端點閘門的天體集合 ——
  只要**任一端點**由 `{月亮, 水星, 金星, 火星}` 之一啟動 → `0.6`；否則（日、木、土、天、海、冥、地球、交點）→ `0.85`。
  上游只列了「月／水／金／火」與「日與外行星」兩類，木星／土星／地球／交點無值，此處補為窮盡。
  水星在西洋側算 `0.85`、在人類圖側算 `0.6` 是刻意的：閘門寬度僅 5.625°，水星一日行約 1°，
  時間誤差足以跨閘門改變**分類**；而西洋側 5°–7° 的 orb 下同樣誤差幾乎不改變相位是否成立。
- **`unavailable` 的三個固定 token**：`house_overlay`（落宮未產出）、`angle_contacts`（角度點接觸未產出）、
  `hd_lines`（人類圖由月／水／金／火啟動的閘門可能位移，line 級精度不可得；
  對應上述 `0.6` 的降級，並非另一個未輸出的欄位）。時間已知時為空陣列。

### 完整度、錯誤與安全

- **`evidence_completeness`**：`aspects` 非空且 `unavailable` 為空 → `full`；
  `unavailable` 非空**或** `aspects` 為空 → `partial`。**引擎只會吐 `full`／`partial`**；
  第三態（不可用）由消費端自行判定，引擎不可能回報「我自己的回應無法解析」。
  `aspects` 為空是決定性結果，判為可重試會讓該使用者被永久 503。
- **輸入錯誤對照**：

  | 情況 | 回應 |
  |---|---|
  | body 非 JSON | `400`，`detail: "invalid JSON body"` |
  | body 非物件、缺 `person_a` 或 `person_b` | `400`，指明缺哪一個 |
  | 缺 `date`／`tz`／`lat`／`lon`／`gender` | `400`，指明欄位 |
  | `time` 省略、`null`、`"unknown"` | 接受，該側時間未知 |
  | `time` 存在但格式不合（`"25:99"`／`"abc"`） | `400`，指明欄位（**不視為時間未知** —— 靜默降級會讓打錯字的呼叫者拿到殘缺解讀卻以為完整） |
  | `tz`／`lat`／`lon` 超界或非有限、年份超出 1900–2100 | `400`（沿用既有 `validate_input`） |
  | `person_a` 與 `person_b` 完全相同 | **接受並照常計算**（所有相位 orb 為 0 是正確結果，不是錯誤） |
  | 內部錯誤 | `500`，body `{"ok": false, "error": "internal_error", "message": "<固定字串>"}` |

  `message` 為**固定且不含內部細節的字串**（`"synastry computation failed"`），
  不得回傳 `str(exc)`：既有 `/chart` 的 500 會外洩如 `"placidus undefined at high latitude"` 之類的內部訊息，
  新 endpoint 不重複該行為。實際例外經 `capture_exception` 送 Sentry。
- **重試語意**：`400` 不可重試（輸入本身有問題，重試必得同樣結果）；
  `500` 與 `503` 可重試。`error` 欄位為固定字串供消費端分支。
- **冪等性**：同一 body 連續兩次 `POST /synastry` 的回應 byte-for-byte 相同（無時鐘依賴、無隨機性）。
- **安全/權限**：沿用 `X-Engine-Key`（無金鑰與錯誤金鑰各回 401）；
  `ENGINE_API_KEY` 未設時 fail-closed `503`，除非 `ENGINE_ALLOW_OPEN=1`。
  輸入驗證共用 `scripts/validation.py`。無新增 secret、無新增外部呼叫、無網路存取。
- **邊界/效能**：0°/360° 跨界以最短弧判定；每人單盤在一次請求內只算一次並共用；
  合盤為 O(11×11) 組合，無 rate limit 需求；不得拖慢既有 `/chart` 路徑。
- **type → strategy 對照**（`participants` 用；引擎現有 `human_design()` 只算 type 與 authority，
  無 strategy，故此表為新增，置於 `scripts/semantics.py`）：

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
| `scripts/synastry.py` | ✅ | 五個西洋陣列與兩個 HD 陣列的內容、方向、不對稱性、排序、去重；9 格連結判定；時間未知時的 `unavailable` | `tests/test_engine_astronomy_contract.py` |
| `scripts/chart_engine.py` | ✅ | 單人輸出與 `examples/sample-output.json` 僅差 `schema_version`；單人無 `synastry` 鍵；同輸入兩次 stdout byte 相同 | `tests/test_json_output.py` |
| `scripts/validation.py` | ✅ | 五個必填 `-b` flag 部分給出時 exit 2 並指明缺哪些；`time` 省略／`null`／`"unknown"` 視為未知；格式錯誤回錯 | `tests/test_validation.py` |
| `server.py` | ✅ | `POST /synastry` 的成功／400 對照表／401／未設金鑰 503／500 形狀；冪等性；`/health` 含 `schema_version`；`/chart` deep-equal 回歸 | `tests/test_server.py` |
| `tests/fixtures/themes-v1.json` | ✅ | `THEMES_V1` 與 checked-in 清單逐字相同（含順序） | `tests/test_readme_sync.py` |
| golden fixtures | ✅ | 再生後的 `golden_example.json`／`.md` 與前一版 diff 僅限 `schema_version` | `tests/test_engine_astronomy_contract.py` |

## Vertical Slices

### Slice E1 — 引擎 synastry 模式骨架
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #18, #19, #22, #23, #24, #27
- **Acceptance criteria**:
  - [ ] CLI 新增 `--date-b/--tz-b/--lat-b/--lon-b/--gender-b`（五者必填）與 `--time-b`（optional）；五個必填者全給才進入 synastry 模式，部分給出 → exit 2 並指明缺哪些（測試：給 3 個必填 flag → exit 2 且訊息含缺少的兩個 flag 名）。
  - [ ] `--time-b` 省略或給 `unknown` → B 側時間未知；`--time`（A 側）在 synastry 模式下同樣可省略或給 `unknown`。單人模式的 `--time` 維持必填，行為不變（測試各一則）。
  - [ ] **單人模式不輸出 `synastry` 鍵**；雙人模式輸出 `synastry` 物件（本 slice 內容可為空陣列，鍵齊全）。
  - [ ] `schema_version` 改為 `"1.2"`，測試斷言 `startswith("1.")`。
  - [ ] `scripts/chart_engine.py` 與 `server.py` 的**執行期** `schema_version` 字面值不再出現 `"1.1"`（測試僅掃這兩個檔）。`AGENTS.md`／`README.md`／`scripts/mcp_server.py` docstring 一併更新為 1.2；18 份翻譯 README 中敘述當前版本之處同步（`tests/test_readme_sync.py` 保持綠）。歷史敘述、`docs/specs/2026-07-13-*`、`tests/fixtures/ephemeris_baseline.json` 不得被改動（測試斷言這三者未變）。
  - [ ] 單人輸出與 `examples/sample-output.json` **parse 後 deep-equal，僅排除 `schema_version`**；該檔不得重新產生（git diff 僅允許 `schema_version` 一行）。
  - [ ] **不啟用 `sort_keys`**；單人 `--json` 輸出的鍵序與浮點表示與變更前**逐 byte 相同，唯一差異為 `schema_version` 的值**（測試以變更前的 golden bytes 做字串替換後比對）。
  - [ ] `tests/fixtures/golden_example.json` 與 `golden_example.md` 重新產生，其 diff **僅限 `schema_version` 字面值**（測試斷言 diff 行數與內容）；`tests/fixtures/GOLDEN_PROVENANCE.md` 記錄本次再生的日期、原因與 diff 範圍。
  - [ ] 同一組雙人輸入連跑兩次，CLI stdout byte-for-byte 相同。
  - [ ] `AGENTS.md` 與 `README.md` Output reference 同步新增 synastry 與 `1.2` 說明，含成功回應含頂層 `ok` 的敘述。
  - [ ] 既有測試全綠，含 `test_runtime_and_test_sources_do_not_import_swisseph` 與 `test_example_matches_pre_change_golden_bytes`。

### Slice E2 — 西洋跨盤相位
- **Type**: AFK
- **Blocked by**: E1
- **User stories**: #1, #2, #3, #4, #5, #6, #24, #25, #26, #28
- **Acceptance criteria**:
  - [ ] 對 A 的 11 個天體與 B 的同集合計算角距，產出 `synastry.western.aspects[]`，每筆通過 §evidence schema 的驗證函式。
  - [ ] 天體集合固定為 11 個（十大行星＋北交點），**南交點不參與**（測試斷言輸出中無南交點 evidence）。
  - [ ] orb 依 §orb 判定順序：北交點任一端 → 用 2° 且不套 +1°；否則用相位 orb 並在日月參與時 +1°（上限 7°）。測試涵蓋「太陽刑北交點」（用 2° 非 6°）界內／界外各一，以及「日月參與 +1° 但不超過 7°」一則。
  - [ ] **`aspects[]` 不含角度點接觸**；測試斷言 `aspects[]` 中不出現 ASC/DSC/MC/IC。
  - [ ] 兩端皆為外行星（天海冥）不輸出；木星與土星**參與**（測試各一則）。**不計算 Chiron**。
  - [ ] 一般天體對 `planet_weight = max(w_a, w_b)`；測試以 §evidence schema 的 canonical 範例（水星四分土星 orb 0.7）餵入計算函式，斷言 `salience == 0.882`、`dimensions == ["communication","commitment_stability","autonomy_boundary"]`（含順序）與 `data_confidence == 0.95`。
  - [ ] 北交點任一端 → `planet_weight == 0.5`（測試：北交點對金星，斷言不是 0.9）。
  - [ ] `orb_weight` 公式測試涵蓋 orb=0（權重 1）、orb=max（權重 0）、orb 略超（不入列）。
  - [ ] 0°/360° 跨界：A 在 359.5°、B 在 0.5° 判為合相 orb 1.0°，測試斷言不算成 359°。
  - [ ] 輸出 `ease_or_tension`；**禁用欄位名遞迴掃描**：走訪整個 response 的所有 key，斷言不含 `interpretive_valence`、`score`、`compatibility`、`percentage`、`rating`、`total`、`grade`、`吉凶` 任一（大小寫不敏感）。
  - [ ] `feature_id` 符合 `^[a-z]+-[a-z0-9-]+$`、依 §feature_id 模板產生、同輸入決定性（兩次執行相同），且**單一 response 內全域唯一**（測試以完整回應斷言集合大小 == 元素數）。
  - [ ] `aspects[]` 依 `salience` desc → `feature_id` asc 排序（測試以人工建構的同 salience 兩筆斷言 tie-break）。
  - [ ] 對至少 5 組樣本盤斷言每筆 evidence 的 `dimensions` ⊂ `themes-v1`，且依行星→theme 表產生。
  - [ ] `data_confidence` 依時間已知與否及是否含**未知側**月亮取值（三組測試：兩側已知 0.95／未知側月亮 0.6／已知側月亮但另一側未知 0.85）。
  - [ ] `scripts/semantics.py` 的 `THEMES_V1` 與 `tests/fixtures/themes-v1.json` 逐字相同（含順序）。
  - [ ] 小行星與次要相位預設不輸出。

### Slice E3 — 西洋雙向 house overlay 與角度點
- **Type**: AFK
- **Blocked by**: E2
- **User stories**: #7, #8, #11, #12, #13, #14, #28
- **Acceptance criteria**:
  - [ ] 輸出 `a_planets_in_b_houses[]` 與 `b_planets_in_a_houses[]` 兩個獨立陣列，每個元素通過 evidence 驗證函式並含 `raw_fact: { planet, house_number, house_system: "placidus" }`（`house_number` 為 1–12 整數）。
  - [ ] 方向語意：`a_planets_in_b_houses` 的每筆 `subject == "A"`、`object == "B"`（測試斷言）。
  - [ ] house overlay 的 `salience == round(planet_weight × 0.8, 3)`、`ease_or_tension == "mixed"`、`dimensions` 沿用行星→theme 表、`participates_in_convergence == false`（測試各一則）。
  - [ ] 角度點接觸的 `salience == round(orb_weight × 0.5, 3)`（`planet_weight` **固定 0.5**，不取 max），`participates_in_convergence == true`（測試一則手算對照：太陽拱 ASC orb 2.0，`orb_weight = 1-(2/4)² = 0.75`，`salience = 0.375`，並斷言不是 0.75）。
  - [ ] 構造 A 火星落 B 十宮但 B 火星不落 A 十宮的資料，斷言兩陣列不對稱。
  - [ ] 角度點接觸（ASC/DSC/MC/IC）雙向分開，orb 行星 3°／日月 4°；兩端皆為特殊天體時取較小者（北交點對 ASC → 2°，測試一則）。測試涵蓋「月亮拱 ASC 用 4° 非 6°」界內／界外各一。
  - [ ] **角度點對角度點不產生 evidence**（測試斷言）。
  - [ ] house overlay 與角度點接觸的天體集合皆為與 `aspects[]` 相同的 11 個（測試斷言北交點有出現、南交點沒有）。
  - [ ] 任一側時間未知時，這兩類**不產出**：四個陣列為 `[]`（鍵仍存在），`synastry.unavailable == ["house_overlay","angle_contacts","hd_lines"]`（固定順序），`evidence_completeness == "partial"`。
  - [ ] `evidence_completeness` 判定：`aspects` 非空且 `unavailable` 為空 → `full`；`unavailable` 非空**或** `aspects` 為空 → `partial`（兩則測試，含「兩人生日相差極遠導致 aspects 為空仍判 partial」）。引擎永不輸出第三個值（測試斷言值域為兩者之一）。
  - [ ] 四個陣列皆依 `salience` desc → `feature_id` asc 排序（測試各一則）。
  - [ ] 同輸入兩次執行結果 byte 相同。

### Slice E4 — 人類圖四種連結與合併中心
- **Type**: AFK
- **Blocked by**: E1
- **User stories**: #2, #9, #10, #26, #28
- **Acceptance criteria**:
  - [ ] 依 §人類圖連結判定的 9 格表判定 `companionship|compromise|dominance|electromagnetic|none`；測試涵蓋全部 9 格（含 `(2,0)`／`(0,2)` → `dominance`、`(1,0)`／`(0,1)` → `none`）。
  - [ ] `(1,1)` 兩格分歧：互補兩端 → `electromagnetic`；雙方持同一個單閘門 → `none`（斷言不誤判為電磁或同伴）。
  - [ ] 同一閘門被多顆行星啟動仍只算一個 active gate。
  - [ ] 一人完整一人單端 → `compromise` 且 `raw_fact.full_channel_owner` 為完整通道持有方，斷言方向正確且不判成 `dominance`；一人完整一人零端 → `dominance` 且 owner 正確。
  - [ ] `full_channel_owner` 值域 `"A"|"B"|null`；`electromagnetic`／`companionship` 時為 `null`（測試斷言）。
  - [ ] 每條通道在 `channel_connections[]` 至多出現一次（測試以 `raw_fact.channel` 斷言集合大小 == 元素數）；`none` 者不輸出。
  - [ ] 輸出 `center_states[]`：**9 個中心全部出現、每個恰好一筆**，`state` ∈ `a_defined|b_defined|both_defined|defined_by_merge|undefined`，`causing_channels` 於 `defined_by_merge` 時非空、其餘為 `[]`（測試各一則）；其 evidence 的 `salience == 0.5`、`ease_or_tension == "mixed"`、`participates_in_convergence == false`、`subject`／`object` 皆為 `null`。
  - [ ] `center_states[]` 依 §中心 → theme 表的列順序排序（測試斷言）。
  - [ ] Split bridge 與 Hanging Gates 被對方補足清單輸出於 `synastry.human_design.participants.person_x`（**非 evidence 物件**），依閘門編號 asc 排序（測試各一則）。
  - [ ] **每筆 `channel_connections[]` 通過與西洋側同一個 evidence 驗證函式**（測試：以同一函式同時驗西洋與 HD 兩側輸出）；`method_version == "human-design-synastry-v1"`。
  - [ ] `dimensions` ＝ 連結類型 theme ∪ 該通道兩端中心 theme，順序依 §dimensions 規則（測試一組手算對照）；`ease_or_tension` 依 `companionship=ease`／`electromagnetic=mixed`／`dominance=tension`／`compromise=tension`。
  - [ ] 時間未知時的 `data_confidence` 依**窮盡切分**：任一端點由 `{月,水,金,火}` 啟動 → `0.6`；否則 → `0.85`（測試三則：月啟動 0.6、土星啟動 0.85、木星啟動 0.85 —— 第三則專門守住上游未指派的那格）。
  - [ ] `participants.person_x` 輸出 `type`／`strategy`／`authority`，`strategy` 依 §type → strategy 表（測試涵蓋五種 type）。
  - [ ] 禁用欄位名遞迴掃描（同 E2 名單）在 HD 側亦通過。
  - [ ] 不輸出 Incarnation Cross 配對。

### Slice E5 — 引擎 HTTP 契約
- **Type**: AFK
- **Blocked by**: E2, E3, E4
- **User stories**: #1, #11, #12, #13, #15, #16, #17, #20, #21, #24
- **Acceptance criteria**:
  - [ ] 新增 `POST /synastry`，body 為 `{ "person_a": {...}, "person_b": {...} }`。
  - [ ] `time` 為 optional：省略、`null` 或 `"unknown"` 皆視為時間未知（測試三則）；`time` 存在但格式不合回 `400`（測試一則，斷言**不**被當成時間未知）。
  - [ ] response 頂層結構固定為 §API contract 所列形狀，含頂層 `ok: true`，確保消費端檢查 `western`/`human_design`/`ziwei` 三鍵 + `1.x` 的型別守衛通過（測試一則）。
  - [ ] `person_a`／`person_b` 在 `western`／`human_design`／`ziwei` 中固定為**空物件**（測試斷言 `== {}`）。
  - [ ] `ziwei.status == "not_computed"` 且 `ziwei.methodology_note` 等於 §API contract 的固定字串（測試斷言字面值相等）。
  - [ ] `synastry.unavailable` 為固定 token 陣列且順序固定，時間已知時為空陣列（測試兩則）；`unavailable` 非空時各陣列鍵**仍存在且為 `[]`**（測試斷言鍵存在）。
  - [ ] 輸入錯誤依 §輸入錯誤對照表（測試涵蓋：非 JSON、缺 `person_b`、缺 `date`、`lat` 超界、`person_a == person_b` 接受）。
  - [ ] 內部錯誤回 `500`，body 為 `{"ok": false, "error": "internal_error", "message": "synastry computation failed"}`；測試斷言 `message` **不含**例外字串（以會拋 `placidus undefined at high latitude` 的極地座標觸發）。
  - [ ] 沿用 `X-Engine-Key`；無金鑰與錯誤金鑰各回 401（測試各一則）；`ENGINE_API_KEY` 未設時回 503，設 `ENGINE_ALLOW_OPEN=1` 時放行（測試各一則）。
  - [ ] 冪等性：同一 body 連續兩次 POST，回應 byte-for-byte 相同（測試一則）。
  - [ ] **`/health` 新增 `schema_version` 欄位，既有 `ok` 欄位不變**（測試斷言兩鍵皆在且 `schema_version == "1.2"`）。
  - [ ] **`/chart` 回歸**：成功回應 parse 後與 `examples/sample-output.json` deep-equal，僅排除 `schema_version`（測試一則，取代「欄位不變」的不可執行敘述）。
  - [ ] `AGENTS.md` 記載完整 request/response/error schema，含五個 `method` 的 `raw_fact` 與 `feature_id` 模板、排序規則、重試語意。
  - [ ] **部署漂移防護**：新增可離線執行的回歸驗證入口（例如 `pytest -k regression` 的具名子集），涵蓋 `/chart` 既有成功路徑與 `examples/sample-output.json` 對齊；`DEPLOY-HETZNER.md` 的驗證章節指明重建部署後必須執行它並保留輸出為證據。

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
- **MCP surface（`scripts/mcp_server.py`）與本地 web UI（`webapp.py`）維持單盤**，不新增合盤工具或畫面；
  兩者僅隨 `to_json_text` 自動繼承 1.2，`mcp_server.py` 只更新 docstring 字面值。
- 消費端 life-web 的任何變更（W1–W3 已在另一個 flow 完成並驗證）。
- 把 `DEPLOY-HETZNER.md` 目前未提交的主機更正納入本分支（見 §Further Notes）。
- 跨系統收斂判定（`converged`／`diverged`／`mixed`／`no_direction`／`not_computed`）——
  那是消費端的計算，引擎只負責提供 `participates_in_convergence` 與 `ease_or_tension` 兩個輸入。

## Further Notes

### 與上游的偏離（五處，皆為上游的內部矛盾或引擎側才看得見的缺漏）

1. **角度點 `salience` 的 `planet_weight`**：上游規則段寫「固定 0.5」、E3 的 AC 寫 `max(行星權重, 0.5)`，兩者互斥。
   本 spec 採**固定 0.5**，因為所有行星權重皆 ≥ 0.5，取 max 會讓角度點端完全不影響結果，
   使上游自己給的正當理由（已用低權重壓低角度點影響力）不成立。
2. **`sort_keys`**：上游要求開啟，但引擎現行鍵序為插入序，開啟會改動整份 byte stream，
   與「單人輸出僅差 `schema_version`」互斥並炸掉既有 golden byte 測試。本 spec **不啟用**，
   改以 CPython dict 保序達成同一個決定性目標。
3. **CLI 時間未知**：上游 E1 要求六個 `-b` flag 全給，但 E5 允許 HTTP 省略 `time`，
   導致時間未知的 HTTP 結果無法用 CLI 離線重現。本 spec 把 `--time-b` 改為 optional。
4. **HD `data_confidence` 的窮盡切分**：上游只列「月／水／金／火」與「日與外行星」，
   木星／土星／地球／交點無值。本 spec 補為窮盡切分。
5. **`dominance` 的產生規則**：上游只給 theme／權重對照，未給任何產生條件，
   且 9 格表的 `(2,0)`／`(0,2)` 未指派。本 spec 補上完整 9 格判定表。

以上皆不影響消費端已驗證的 candidate：消費端讀 `salience` 的**值**、不重算它的**算式**，
也不呼叫 CLI。偏離 1 會讓角度點接觸的 `salience` 較小，可能使個別 theme 落到消費端 0.45 門檻之下 ——
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

**風險 4 — golden fixture 再生。** `golden_example.json`／`.md` 是「變更前」的 byte 證據，
本次因 1.2 bump 必須再生。若再生時混入 `schema_version` 以外的差異，
`test_example_matches_pre_change_golden_bytes` 就從回歸防線退化成自我證明。
E1 的 AC 要求斷言 diff 範圍，`GOLDEN_PROVENANCE.md` 要求記錄理由。

### 上線順序（硬性）

引擎 `/synastry` 必須**先於** life-web 上線。life-web 的 `synastryReading` 無條件呼叫 `/synastry`，
且其合盤 cache 前綴已由 `synastry-v2-` 改為 `synastry-v3-`，
所以引擎未上線時 life-web 一上線，**連已付費的既有合盤客戶都會拿到 502/503**。
部署後的驗收訊號：`curl https://engine-life.aicycle.cc/health` 回的 JSON 含 `schema_version: "1.2"`。

**Node.js ≥ 18 仍是硬性 runtime 需求**（紫微 sidecar），本 feature 不改變此前提。
