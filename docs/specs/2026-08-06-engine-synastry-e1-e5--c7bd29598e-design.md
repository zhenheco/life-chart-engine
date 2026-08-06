# 引擎 synastry 合盤運算（E1–E5） — SPEC

> Canonical 來源：`zhenheco/life-web` 的 `docs/specs/2026-08-05-synastry-real-computation--8844a06f0a-design.md`
> 的 §Implementation Decisions、§證據語意規則、§Vertical Slices E1–E5。該 spec 已通過該 flow 的
> cross-validation，且 life-web 已驗證的 candidate `c5a0df1b92e947ee27c3cf4b22fccaeea8776857`
> 就是照這份契約寫的。本 spec 把引擎側需要的部分**完整內嵌**（引擎 repo 為公開 repo，讀不到那份 private spec），
> 內容不得與來源分岔。

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

使用者（實際上是消費端產品）會拿到：

- 兩人之間的西洋跨盤相位（誰的哪顆星、對誰的哪顆星、什麼相位、差幾度）
- 雙向的落宮：A 的行星落在 B 的哪些宮、以及 B 的行星落在 A 的哪些宮（兩份，不壓成一份）
- 雙向的角度點接觸（ASC/DSC/MC/IC）
- 人類圖的四種連結（電磁／同伴／支配／妥協）與合併後的中心狀態
- 每一筆事實都附帶可比較的語意欄位，讓消費端能把它排序、篩選、交叉比對，並在輸出中標明依據

以及誠實的缺漏揭露：任一方出生時間未知時，時間相依的項目明確標成 `unavailable`
而不是悄悄用一個猜測值算下去。

## User Stories

1. As a consumer product, I want to POST two people's birth data to one endpoint and get relationship-level facts back, so that I never have to re-implement chart mathematics on my side.
2. As a consumer product, I want every synastry fact to arrive as a uniformly shaped Evidence object, so that one validator can check both the Western and the Human Design side.
3. As a consumer product, I want each Evidence to carry a stable `feature_id`, so that I can cite the exact fact a sentence was derived from.
4. As a consumer product, I want `salience` computed by the engine, so that ranking the strongest contacts does not depend on my re-deriving orb weights.
5. As a consumer product, I want `dimensions` mapped to a fixed theme ontology, so that Western and Human Design evidence about the same life area can be compared at all.
6. As a consumer product, I want `ease_or_tension` on every directional Evidence, so that I can detect when two independent systems agree or disagree.
7. As a consumer product, I want `participates_in_convergence` filled in by the engine, so that non-directional evidence (house overlay, centre states) never votes in that comparison.
8. As a consumer product, I want house overlay delivered as two separate arrays, so that a genuinely asymmetric relationship is not flattened into a false symmetry.
9. As a consumer product, I want the Human Design link classification to be exactly one of four types per channel, so that my downstream copy never has to resolve an ambiguous double classification.
10. As a consumer product, I want merged-chart centre states with the channels that caused them, so that I can explain *why* a centre became defined together.
11. As a consumer product, I want to omit birth time (or send `null` / `"unknown"`), so that a user who does not know their birth hour still gets the time-independent half of the reading.
12. As a consumer product, I want time-dependent items to be listed by fixed token in `synastry.unavailable`, so that I can tell the user exactly what is missing without string-matching prose.
13. As a consumer product, I want `evidence_completeness` to distinguish "complete", "computed but partial" and "unusable", so that I fail closed only on the genuinely retryable case.
14. As a consumer product, I want an empty `aspects` array to count as `partial` and still be served, so that a determinate result is never turned into a permanent 503 for that user.
15. As a consumer product, I want the response top level to keep `western` / `human_design` / `ziwei` keys and a `1.x` `schema_version`, so that my existing type guard passes unchanged.
16. As a consumer product, I want 紫微 explicitly reported as `not_computed` with a methodology note, so that its absence reads as a deliberate boundary rather than a bug.
17. As a consumer product, I want internal errors to return a fixed machine-parsable `error` string, so that I can decide whether to retry without parsing human prose.
18. As an existing single-chart caller, I want `/chart` and the CLI's single-person output to be byte-identical apart from `schema_version`, so that this feature cannot silently change my existing charts.
19. As an existing single-chart caller, I want the single-person output to contain no `synastry` key at all, so that my parser sees no new optional branch.
20. As an operator, I want `/health` to report `schema_version`, so that I can verify from outside which contract a deployed instance actually serves.
21. As an operator, I want the same `X-Engine-Key` auth on the new endpoint, so that it cannot become an open compute endpoint.
22. As a CLI user, I want six `-b` flags to switch the CLI into synastry mode, so that I can reproduce any HTTP result offline and deterministically.
23. As a CLI user, I want partially supplied `-b` flags to fail loudly naming what is missing, so that I never get a one-person chart when I asked for two.
24. As a maintainer, I want the same two-person input to produce byte-identical stdout across runs, so that determinism remains testable rather than aspirational.
25. As a maintainer, I want the theme ontology asserted character-for-character against the consumer's copy, so that the two cannot drift apart unnoticed.
26. As a maintainer, I want no compatibility-score or fortune-scoring field anywhere in the schema, so that the product cannot later grow a "relationship score" through the back door.

## Modules

| Module | 職責（一句） | 公開介面（窄） | 新建/修改 |
|---|---|---|---|
| `scripts/synastry.py` | 由兩份已驗證輸入算出完整 synastry 區塊（唯一的關係運算入口） | `build_synastry(inp_a, inp_b) -> dict` | 新建 |
| `scripts/semantics.py` | `semantics-v1` 規則本體：theme 對照表、orb 判定順序、權重與 `salience`、`data_confidence` | `THEMES_V1`, `evidence(...) -> dict`, `orb_weight(orb, max_orb) -> float`, `resolve_max_orb(a, b, aspect) -> float | None` | 新建 |
| `scripts/chart_engine.py` | 既有單人計算核心；新增雙人分派與 `schema_version` 1.2 | `build_json(inp)`（不變）、`build_synastry_json(inp_a, inp_b) -> dict` | 修改 |
| `scripts/validation.py` | 既有輸入驗證；新增「時間未知」與 B 側欄位 | `validate_input(raw, *, allow_unknown_time=False)` | 修改 |
| `server.py` | HTTP surface；新增 `POST /synastry`、`/health` 加 `schema_version` | `POST /synastry` | 修改 |

設計約束：`build_synastry` 只呼叫既有的 `western()` / `human_design()`，**不得**複製任何相位或閘門計算；
每人的單盤計算在一次請求內只跑一次，供相位、overlay 與人類圖三個模組共用。

## Implementation Decisions

- **Schema**：無資料庫。JSON 輸出契約變更如下。
- **`schema_version` 釘 `"1.2"`，必須留在 `1.x` family**。消費端以 `sv.startsWith("1.")` 判定並拒絕 `2.x`；
  bump 成 `2.0` 會讓消費端全站免費排盤失效。所有硬編字面值同步更新，**含 `server.py` 的 500 錯誤 envelope**。
- **單人輸出回歸 oracle**：parse 後與 `examples/sample-output.json` deep-equal，**僅排除 `schema_version`**。
  該檔不得重新產生（git diff 僅允許 `schema_version` 一行）。JSON 輸出強制 `sort_keys=True` 與固定浮點格式。
- **單人模式不輸出 `synastry` 鍵**；雙人模式才輸出。
- **API contract — `POST /synastry`**，body `{ "person_a": {...}, "person_b": {...} }`，
  每人欄位同 `/chart`，但 `time` 為 **optional**（省略／`null`／`"unknown"` 皆視為時間未知）。
  Response 頂層形狀固定：

  ```json
  {
    "schema_version": "1.2",
    "western":      { "person_a": {}, "person_b": {} },
    "human_design": { "person_a": {}, "person_b": {} },
    "ziwei":        { "person_a": {}, "person_b": {}, "status": "not_computed", "methodology_note": "..." },
    "synastry":     { "western": { "aspects": [], "a_planets_in_b_houses": [], "b_planets_in_a_houses": [],
                                   "angle_contacts_a_to_b": [], "angle_contacts_b_to_a": [] },
                      "human_design": { "channel_connections": [], "center_states": [] },
                      "unavailable": [] },
    "evidence_completeness": "full"
  }
  ```

  `person_a` / `person_b` 在 `western` / `human_design` / `ziwei` 中固定為**空物件**，
  只為讓消費端檢查三鍵存在的型別守衛通過；個人盤資料不由此 endpoint 提供。
- **evidence schema（canonical 定義在此節）**：

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
  `planet_weight = max(0.9, 0.8) = 0.9`，故 `salience = 0.9804 × 0.9 = 0.882`；
  兩側時間已知且無月亮參與，故 `data_confidence = 0.95`。
  必須有一條測試把此範例餵進計算函式並斷言逐欄位相符。
  - `feature_id` 格式 `^[a-z]+-[a-z0-9-]+$`，全域唯一且對同一輸入決定性。
  - `system` ∈ `western|human_design`；`ease_or_tension` ∈ `ease|tension|mixed`；
    `method_consensus` ∈ `core|named_school|experimental`。
  - **`method` 值域固定五個**：`synastry_aspect`／`house_overlay`／`angle_contact`／
    `hd_channel_connection`／`hd_center_state`。
  - **不設 `interpretive_valence`**（與 `ease_or_tension` 同構）。
  - `salience` / `data_confidence` 為 `0.0–1.0` float，一律四捨五入至小數點後三位。
- **主題 ontology `themes-v1`（10 個固定 ID）**：`communication`、`emotion_regulation`、`decision_power`、
  `action_tempo`、`intimacy_attraction`、`autonomy_boundary`、`commitment_stability`、`money_division`、
  `conflict_repair`、`timing_context`。此 ontology 是**產品自訂的二次轉譯**，不是任何命理傳統原生的分類
  （見 ADR-0001）；引擎與消費端各持一份常數且必須逐字相同。
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
- **人類圖：中心 → theme**（通道 evidence 的 `dimensions` ＝ 連結類型 theme ∪ 該通道兩端中心的 theme）：

  | 中心 | themes |
  |---|---|
  | Head／Ajna | `communication`, `decision_power` |
  | Throat | `communication`, `action_tempo` |
  | G（Identity） | `commitment_stability`, `autonomy_boundary` |
  | Heart／Ego | `money_division`, `decision_power` |
  | Sacral | `action_tempo`, `intimacy_attraction` |
  | Solar Plexus | `emotion_regulation`, `conflict_repair` |
  | Spleen | `timing_context`, `autonomy_boundary` |
  | Root | `action_tempo`, `emotion_regulation` |

- **西洋：相位 → `ease_or_tension`**：三分 120° = `ease`；六合 60° = `ease`；四分 90° = `tension`；
  對分 180° = `tension`；合相 0° = `mixed`。合相判 `mixed` 是因為它本質中性，
  在沒有逐組合判定表的情況下宣稱它是 ease 或 tension 都是杜撰。**角度點接觸沿用同一張表**。
  house overlay 不適用（固定 `mixed` 且不參與收斂）。
- **人類圖：連結類型 → `ease_or_tension`**：`companionship = ease`；`electromagnetic = mixed`；
  `dominance = tension`；`compromise = tension`。
- **參與 `aspects[]` 的天體集合固定 11 個**：太陽、月亮、水星、金星、火星、木星、土星、天王星、海王星、
  冥王星、**北交點**。**南交點不參與**（恆為北交點對沖，納入會讓每個相位系統性重複一次）。
  納入北交點是對「預設關閉」建議的刻意偏離，理由是它在 `timing_context` 上是唯一的西洋來源，
  且已用 `planet_weight = 0.5` 壓低影響力。**角度點不進 `aspects[]`**，只出現在 E3 的獨立陣列。
- **「外行星」＝天王星、海王星、冥王星**；木星與土星**參與**計算。**不計算 Chiron**（astronomy-engine 無此資料）。
- **orb 判定順序**（覆蓋規則，決定接觸存不存在）：
  1. 任一端為**角度點或北交點** → 用該天體的 orb（角度點 3°；日月對角度點 4°；北交點 2°），
     **不套用日月 +1°**。**兩端皆為特殊天體時取較小者**（例：ASC 對北交點 → 2°）。
  2. 否則 → 用相位 orb（合 6／沖 6／刑 5／拱 5／六合 3），日月任一參與則 +1°，絕對上限 7°。
  3. 兩端皆為外行星 → 不計分、不輸出。

  規則 1 的角度點分支只適用於 E3；北交點分支適用於 E2 的 `aspects[]`。
- **`orb_weight = max(0, 1 - (actual_orb / max_orb)²)`**。
- **`salience` 公式**：
  - **跨盤相位**：`round(orb_weight × planet_weight, 3)`。兩端皆為一般天體 → `planet_weight = max(w_a, w_b)`；
    **任一端為北交點 → 固定 `0.5`**（不取 max；取 max 會讓壓低影響力的正當理由不成立）。
  - **角度點接觸**：同公式，`planet_weight` **固定 `0.5`**；`orb_weight` 以該接觸適用的 orb（行星 3°／日月 4°）為 `max_orb`。
  - **house overlay**：`round(planet_weight × 0.8, 3)`。落宮無 orb 概念，`0.8` 是相對精確相位的方法論折扣。
  - **人類圖通道**：固定 `companionship/electromagnetic = 0.9`、`dominance = 0.8`、`compromise = 0.7`。
  - **行星權重**：日月 `1.0`；水金火 `0.9`；木土 `0.8`；天海冥 `0.6`；北交點與角度點 `0.5`。
- **`participates_in_convergence`**：西洋 `aspects[]`、角度點接觸、人類圖 `channel_connections[]` 為 `true`；
  house overlay 與人類圖合併後中心狀態為 `false`（兩者都沒有可比較的方向性強度），
  且其 `ease_or_tension` 一律 `mixed`、`dimensions` 沿用行星→theme／中心→theme 表，不另立宮位→theme 表。
- **角度點對角度點不產生 evidence**（角度點本身不是天體，兩端皆為角度點沒有傳統依據）。
- **`data_confidence`**：兩側時間皆已知 → `0.95`。任一側時間未知時，該側月亮位置以**當地正午 12:00** 推估，
  凡有該側月亮參與的 feature 一律 `0.6`；其餘非時間相依 feature → `0.85`。
  時間相依 feature（house overlay、角度點接觸、HD line）在時間未知時**不產出**，標 `unavailable`。
  人類圖側：時間未知時由**月／水／金／火**啟動的閘門所屬通道 `0.6`，僅由日與外行星啟動者 `0.85`。
- **`method_consensus`**：本次產出一律 `core`；`named_school` 與 `experimental` 保留 enum 但不產生。
- **人類圖連結判定**：術語固定電磁／支配／妥協／同伴；依雙方 active gate 在通道兩端計數；
  同一閘門被多顆行星啟動仍只算一個；一人完整一人單端判**妥協**並輸出 `full_channel_owner`；
  雙方皆完整先判**同伴**；電磁必須互補兩端；雙方持同一個單閘門 → `none`。
- **`evidence_completeness`**：`aspects` 非空且無 `unavailable` → `full`；有 `unavailable` **或** `aspects` 為空 → `partial`。
  引擎只會吐 `full`／`partial`；`insufficient` 由消費端判定（引擎不可能回報「我自己的回應無法解析」）。
  `aspects` 為空是決定性結果，判為可重試會讓該使用者被永久 503。
- **`synastry.unavailable`** 為固定 token 陣列：`house_overlay`／`angle_contacts`／`hd_lines`；時間已知時為空陣列。
- **安全/權限**：沿用 `X-Engine-Key`（無金鑰與錯誤金鑰各回 401）；沿用 `ENGINE_API_KEY` 未設時 fail-closed 503
  （除非 `ENGINE_ALLOW_OPEN=1`）。輸入驗證共用 `scripts/validation.py`，
  缺必要欄位回 400 並指明欄位。無新增 secret、無新增外部呼叫、無網路存取（determinism 前提不變）。
  內部錯誤 body 固定 `{"ok": false, "error": "internal_error", "message": "..."}`。
- **邊界/效能**：0°/360° 跨界必須以最短弧判定；每人單盤在一次請求內只算一次並共用；
  合盤是 O(11×11) 的組合，無 rate limit 需求；不得因新增模式而拖慢既有 `/chart` 路徑。

## Testing Decisions

好測試只測外部行為。既有 prior art 都在 `tests/`。

| Module | 要測? | 測什麼外部行為 | Prior art |
|---|---|---|---|
| `scripts/semantics.py` | ✅ | 給定行星對／相位／orb／時間已知與否，回傳的 `dimensions`／`salience`／`ease_or_tension`／`data_confidence` 逐欄位正確；orb 判定順序的覆蓋規則正確 | `tests/test_validation.py` |
| `scripts/synastry.py` | ✅ | 給定兩份出生資料，五個陣列的內容、方向、不對稱性、去重與排序正確；時間未知時標 `unavailable` | `tests/test_engine_astronomy_contract.py` |
| `scripts/chart_engine.py` | ✅ | 單人輸出與 `examples/sample-output.json` 僅差 `schema_version`；單人無 `synastry` 鍵；同輸入兩次 stdout byte 相同 | `tests/test_json_output.py` |
| `scripts/validation.py` | ✅ | 六個 `-b` flag 部分給出時 exit 2 並指明缺哪些；`time` 省略／`null`／`"unknown"` 皆視為時間未知 | `tests/test_validation.py` |
| `server.py` | ✅ | `POST /synastry` 的成功／400／401／500 形狀；`/health` 含 `schema_version`；`/chart` 成功路徑不變 | `tests/test_server.py` |
| themes 常數比對 | ✅ | 引擎的 `themes-v1` 與 checked-in 清單逐字相同 | `tests/test_readme_sync.py`（同類：checked-in 對照） |

## Vertical Slices

### Slice E1 — 引擎 synastry 模式骨架
- **Type**: AFK
- **Blocked by**: None
- **User stories**: #18, #19, #22, #23, #24
- **Acceptance criteria**:
  - [ ] CLI 新增 `--date-b/--time-b/--tz-b/--lat-b/--lon-b/--gender-b`；六者全給才進入 synastry 模式，部分給出 → exit 2 並指明缺哪些。
  - [ ] **單人模式不輸出 `synastry` 鍵**；雙人模式輸出 `synastry` 物件（本 slice 內容可為空）。
  - [ ] `schema_version` 改為 `"1.2"`，測試斷言 `startswith("1.")`。
  - [ ] 所有硬編 `schema_version` 字面值同步更新，**含 `server.py` 的 500 錯誤 envelope**（測試斷言無殘留 `"1.1"`）。
  - [ ] 單人輸出與 `examples/sample-output.json` **parse 後 deep-equal，僅排除 `schema_version`**；該檔不得重新產生（git diff 僅允許 `schema_version` 一行）。
  - [ ] JSON 輸出強制 `sort_keys=True` 與固定浮點格式；同一組雙人輸入連跑兩次 stdout byte-for-byte 相同。
  - [ ] `AGENTS.md` 與 `README.md` Output reference 同步新增 synastry 與 `1.2` 說明。
  - [ ] 既有測試全綠，含 `test_runtime_and_test_sources_do_not_import_swisseph`。

### Slice E2 — 西洋跨盤相位
- **Type**: AFK
- **Blocked by**: E1
- **User stories**: #1, #2, #3, #4, #5, #6, #26
- **Acceptance criteria**:
  - [ ] 對 A 的十大行星＋交點與 B 的同集合計算角距，產出 `synastry.western.aspects[]`，每筆符合 §Implementation Decisions 的 evidence schema。
  - [ ] 天體集合固定為 11 個（十大行星＋北交點），**南交點不參與**（測試斷言輸出中無南交點 evidence）。
  - [ ] orb 依 §Implementation Decisions 的**判定順序**：北交點任一端 → 用 2° 且不套 +1°；否則用相位 orb 並在日月參與時 +1°（上限 7°）。測試涵蓋「太陽刑北交點」（用 2° 非 6°）界內／界外各一，以及「日月參與 +1° 但不超過 7°」一則。
  - [ ] **`aspects[]` 不含角度點接觸**（角度點屬 E3 的獨立輸出）；測試斷言 `aspects[]` 中不出現 ASC/DSC/MC/IC。
  - [ ] 兩端皆為外行星（天海冥）不輸出；木星與土星**參與**計算（測試各一則）。**不計算 Chiron**。
  - [ ] `planet_weight = max(w_a, w_b)`；測試以 §Implementation Decisions 的 canonical 範例（水星四分土星 orb 0.7）餵入計算函式，斷言 `salience == 0.882`、`dimensions` 與 `data_confidence` 逐欄位相符。
  - [ ] `orb_weight` 公式測試涵蓋 orb=0（權重 1）、orb=max（權重 0）、orb 略超（不入列）。
  - [ ] 0°/360° 跨界：A 在 359.5°、B 在 0.5° 判為合相 orb 1.0°，測試斷言不算成 359°。
  - [ ] 外行星對外行星不產生 evidence（以兩張同世代盤斷言）。
  - [ ] 輸出 `ease_or_tension` 且 schema **無** `interpretive_valence`、無任何吉凶加減總分欄位（schema grep 斷言）。
  - [ ] `feature_id` 符合 `^[a-z]+-[a-z0-9-]+$` 且同輸入決定性（兩次執行 id 相同）。
  - [ ] 對至少 5 組樣本盤斷言每筆 evidence 的 `dimensions` ⊂ `themes-v1`，且依 §Implementation Decisions 的行星→theme 對照表產生（例：水星四分土星須含 `communication`、`commitment_stability`、`autonomy_boundary`）。
  - [ ] `salience` 依 `orb_weight × planet_weight` 計算，至少一組手算對照；`data_confidence` 依時間已知與否及是否含月亮取值（三組測試）。
  - [ ] 引擎的 `themes-v1` 常數與消費端的同名常數**逐字相同**（以 checked-in 清單比對測試）。
  - [ ] 小行星與次要相位預設不輸出。

### Slice E3 — 西洋雙向 house overlay 與角度點
- **Type**: AFK
- **Blocked by**: E2
- **User stories**: #7, #8, #11, #12, #13, #14
- **Acceptance criteria**:
  - [ ] 輸出 `a_planets_in_b_houses[]` 與 `b_planets_in_a_houses[]` 兩個獨立陣列，每個元素為合法 evidence 物件並含 `raw_fact: { planet, house_number, house_system: "placidus" | <引擎既有值> }`（`house_number` 為 1–12 整數）。
  - [ ] house overlay 的 `salience = round(planet_weight × 0.8, 3)`（無 orb 概念故不套 `orb_weight`）、`ease_or_tension = "mixed"`、`dimensions` 沿用行星→theme 表、`participates_in_convergence = false`（測試各一則）。
  - [ ] 角度點接觸的 `salience = round(orb_weight × max(行星權重, 0.5), 3)`，`participates_in_convergence = true`（測試一則手算對照）。
  - [ ] 構造 A 火星落 B 十宮但 B 火星不落 A 十宮的資料，斷言兩陣列不對稱。
  - [ ] 角度點接觸（ASC/DSC/MC/IC）雙向分開，orb 行星 3°／日月 4°；兩端皆為特殊天體時取較小者。測試涵蓋「月亮拱 ASC 用 4° 非 6°」界內／界外各一（此測試屬 E3，不屬 E2）。
  - [ ] 任一側時間未知時本 slice 輸出標 `unavailable`，並在 `synastry.unavailable: string[]` 填入對應的固定 token（`house_overlay`／`angle_contacts`／`hd_lines`），`evidence_completeness` 為 `partial`（非 `insufficient`）。
  - [ ] `evidence_completeness` 判定：`aspects` 非空且無 `unavailable` → `full`；有 `unavailable` **或** `aspects` 為空 → `partial`（兩則測試，含「兩人生日相差極遠導致 aspects 為空仍判 partial」）。
  - [ ] 決定性測試通過。

### Slice E4 — 人類圖四種連結與合併中心
- **Type**: AFK
- **Blocked by**: E1
- **User stories**: #2, #9, #10, #26
- **Acceptance criteria**:
  - [ ] 依雙方 active gate 計數判定 `companionship|compromise|dominance|electromagnetic|none`。
  - [ ] 測試涵蓋所有 `(0,1,2) × (0,1,2)` 共 9 種組合。
  - [ ] 雙方持同一個單閘門 → `none`（斷言不誤判為電磁或同伴）。
  - [ ] 同一閘門被多顆行星啟動仍只算一個 active gate。
  - [ ] 一人完整一人單端 → `compromise` 並輸出 `full_channel_owner`，斷言方向正確且不判成 `dominance`。
  - [ ] 輸出合併後中心狀態（A 定義／B 定義／僅合併後定義／皆未定義）並標出造成定義的通道；其 evidence 的 `ease_or_tension = "mixed"`、`participates_in_convergence = false`。
  - [ ] 輸出 Split bridge 與 Hanging Gates 被對方補足清單。
  - [ ] **每筆 `channel_connections[]` 必須是合法的 evidence 物件**，含 `feature_id`／`system: "human_design"`／`dimensions`／`salience`／`ease_or_tension`／`method_consensus`／`data_confidence`（測試：以同一個 evidence 驗證函式同時驗西洋與 HD 兩側輸出）。
  - [ ] `dimensions` ＝ 連結類型 theme ∪ 該通道兩端中心 theme（測試一組手算對照）；`ease_or_tension` 依 `companionship=ease`／`electromagnetic=mixed`／`dominance=tension`／`compromise=tension`。
  - [ ] 時間未知時，由月／水／金／火啟動的閘門所屬通道 `data_confidence = 0.6`，僅由日與外行星啟動者 `0.85`（測試各一則）。
  - [ ] 輸出雙方 type/strategy/authority，且 schema **無**任何相容度百分比欄位（grep 斷言）。
  - [ ] 不輸出 Incarnation Cross 配對。

### Slice E5 — 引擎 HTTP 契約
- **Type**: AFK
- **Blocked by**: E2, E3, E4
- **User stories**: #1, #11, #12, #15, #16, #17, #20, #21
- **Acceptance criteria**:
  - [ ] 新增 `POST /synastry`，body 為 `{ "person_a": {...}, "person_b": {...} }`。
  - [ ] `time` 為 **optional**：省略、`null` 或 `"unknown"` 皆視為時間未知，該側時間相依項標 `unavailable`、`evidence_completeness` 為 `partial`（測試一則）。
  - [ ] response 頂層結構固定為 §Implementation Decisions 所列形狀，確保消費端檢查 `western`/`human_design`/`ziwei` 三鍵 + `1.x` 的型別守衛通過（測試一則）。
  - [ ] `person_a`／`person_b` 在 `western`／`human_design`／`ziwei` 中固定為**空物件**（測試斷言為空）。
  - [ ] `synastry.unavailable` 為固定 token 陣列（`house_overlay`／`angle_contacts`／`hd_lines`），時間已知時為空陣列（測試兩則）。
  - [ ] 內部錯誤 body 為 `{"ok": false, "error": "internal_error", "message": "..."}`，`error` 為固定可 parse 的字串。
  - [ ] 沿用 `X-Engine-Key`；無金鑰與錯誤金鑰各回 401（測試各一則）。
  - [ ] 缺必要欄位回 400 並指明欄位；內部錯誤回 500 且 body 為 `{"ok": false, ...}`。
  - [ ] **`/health` 新增 `schema_version` 欄位，既有 `ok` 欄位不變**；`/chart` 成功路徑欄位不變（回歸測試）。
  - [ ] `AGENTS.md` 記載完整 request/response/error schema。
  - [ ] **部署漂移防護**：新增一個可離線執行的回歸驗證腳本／測試，涵蓋 `/chart` 既有成功路徑與 `examples/sample-output.json` 對齊，並在 `DEPLOY-HETZNER.md` 的驗證章節指明重建部署後必須執行它。線上映像目前落後 repo 一個多月，重建會一併帶上既有變更（見 §Further Notes）。

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
- 消費端 life-web 的任何變更（W1–W3 已在另一個 flow 完成並驗證）。
- 把 `DEPLOY-HETZNER.md` 目前未提交的主機更正納入本分支（見 §Further Notes）。

## Further Notes

**已知風險 1 — 部署漂移。** 線上 `engine-life.aicycle.cc` 的映像是 **2026-06-29** build 的，
而 repo 已在 `56a8d17`（2026-07-13）。照 `DEPLOY-HETZNER.md` 重建部署會**一併把這一個多月的既有變更推上 prod**，
而 prod 服務現有免費與付費單盤客戶。E5 已把「重建後跑既有回歸驗證」列為驗收條件，
但這只讓風險被測到，不會讓風險消失；部署當下必須把 `/chart` 既有成功路徑與
`examples/sample-output.json` 的比對結果留成證據。

**已知風險 2 — `DEPLOY-HETZNER.md` 在 git 裡是過期的。** 版本庫中的版本仍指向已除役的主機
`acejou@157.90.157.99` 與 `/home/acejou/life-chart-engine`；正確的是 `root@49.12.196.102` 與
`/opt/life-chart-engine`（Hermes box，tunnel token 存 1Password `LIFE_ENGINE_TUNNEL_TOKEN`）。
這份更正目前只存在於 base repo 的**未提交工作區**，不在本分支。
本 flow **刻意不吸收那份未提交變更**（它不屬於本 feature 的 diff，會違反「每一行 diff 可追溯」），
但任何人照 git 版本的文件部署都會連錯主機。這需要一次獨立的 commit 處理。

**已知風險 3 — `themes-v1` 雙份常數。** 引擎與消費端各持一份且必須逐字相同（見 ADR-0001）。
引擎側改動即為消費端的破壞性變更；比對測試是唯一的防線。

**上線順序（硬性）。** 引擎 `/synastry` 必須**先於** life-web 上線。
life-web 的 `synastryReading` 無條件呼叫 `/synastry`，且其合盤 cache 前綴已由 `synastry-v2-` 改為 `synastry-v3-`，
所以引擎未上線時 life-web 一上線，**連已付費的既有合盤客戶都會拿到 502/503**。
部署後的驗收訊號：`curl https://engine-life.aicycle.cc/health` 回的 JSON 含 `schema_version: "1.2"`。

**Node.js ≥ 18 仍是硬性 runtime 需求**（紫微 sidecar），本 feature 不改變此前提。
