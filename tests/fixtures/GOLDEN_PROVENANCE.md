# Golden fixture provenance

`golden_example.json` / `golden_example.md` are the byte-exact stdout of the
**pre-strict-CLI** engine run with no flags (the historical example-person
fallback), captured so `--example` can prove byte-identical compatibility
(`test_example_matches_pre_change_golden_bytes`, capture-platform-only).

- Captured: 2026-07-15 00:50 (UTC+8), macOS arm64 (`darwin`, see golden_platform.txt), CPython 3.12 (`.venv`), astronomy-engine
  per `requirements.lock`, Node sidecar iztro 2.5.8.
- The byte-identity test runs only when `sys.platform` equals the content of
  `golden_platform.txt` (the capture platform); other platforms rely on the
  suite's tolerance-based assertions. Regenerating on Linux and setting the
  marker to `linux` enables the assertion in CI.
- If Linux CI reports a byte mismatch (last-ulp libm differences), regenerate
  on Linux from the same engine state and commit the result:

```bash
# inside the repo Docker image or any Linux + CPython 3.12 + Node >= 18 env
python scripts/chart_engine.py --example --json > tests/fixtures/golden_example.json
python scripts/chart_engine.py --example        > tests/fixtures/golden_example.md
```

Regenerating from `--example` is valid only while `--example` output is known
byte-identical to the historical fallback on the capturing platform (verified
at capture time on macOS).

## 2026-08-06 — schema_version 1.1 → 1.2 (E1 synastry skeleton)

- **Date:** 2026-08-06
- **Reason:** Slice E1 bumps live `schema_version` from `"1.1"` to `"1.2"` for the
  dual-person synastry mode skeleton. Single-person chart body is otherwise
  unchanged (no `sort_keys`, same insertion order, same float repr).
- **Diff scope:**
  - `tests/fixtures/golden_example.json` — **one line only**:
    `"schema_version": "1.1"` → `"1.2"`.
  - `examples/sample-output.json` — **one line only**: same `schema_version` bump.
  - `tests/fixtures/golden_example.md` — **zero diff** (Markdown path does not
    print `schema_version`).
- **Pre-change oracle:** `tests/fixtures/golden_example_pre_1_2.json` was
  captured from the pre-1.2 engine (`--example --json`) **before** any code
  change and must never be regenerated. Byte-identity tests replace
  `"1.1"`→`"1.2"` in that file and compare to live stdout.

## 2026-08-30 — F-1 閘門 19 中心歸屬修正（情緒 → 根）：重新產生，位元組零差異

- **Date:** 2026-08-30
- **Reason:** `GATE_CENTER[19]` 由 `'情緒'` 改為 `'根'`（見
  `docs/2026-08-30-gate19-root-fix-impact.md`）。修正影響 4.82% 隨機樣本的已定義/開放中心
  與 3.44% 的 Definition，因此依規定全量重新產生 golden。
- **Diff scope:** **零差異。** `golden_example.json`、`golden_example.md`、
  `examples/sample-output.json` 重新產生後與既有檔案位元組完全相同。原因：範例人與小明兩張盤
  都含閘門 19，但都沒有完整的 19-49 通道，因此連通性與所有衍生欄位不變。
- **Commands:**
  ```bash
  .venv/bin/python scripts/chart_engine.py --example --json > tests/fixtures/golden_example.json
  .venv/bin/python scripts/chart_engine.py --example        > tests/fixtures/golden_example.md
  .venv/bin/python scripts/chart_engine.py --json --name "小明" --gender 女 \
    --date 1990-06-15 --time 08:30 --tz 8 --lat 25.033 --lon 121.5654 --target 2025-01-01 \
    > examples/sample-output.json
  ```
- **Determinism:** 上述三個指令各連續執行兩次，第二次輸出與第一次位元組相同。
- **Pre-change oracle:** `tests/fixtures/golden_example_pre_1_2.json` 未重新產生（依 2026-08-06 條目規定）。

## 2026-09-15 — Human Design 命盤輪 OFFSET 修正（-1.375 → -1.75）：全量重新產生（含 pre-1.2 oracle）

- **Date:** 2026-09-15
- **Reason:** `scripts/chart_engine.py:98` 的 `OFFSET` 錯了 0.375°，使整條人類圖 64 閘門輪相對真實星座
  度數轉錯位置。以已出版的 Human Design 命盤輪為準（barneyandflow.com/gate-zodiac-degrees；
  Scribd "Gates and Zodiac Placements"：閘門25 = 358°15′(358.25°) 起、閘門17 = 3°52′30″(3.875°) 起、
  閘門41 = 寶瓶座2°00′(302.0°) 起）比對，`OFFSET=-1.375` 使這三個錨點全部落在錯誤的閘門；
  `OFFSET=-1.75` 三點全部吻合，並與獨立套件 `hd-chart-engine@0.1.1`（`WHEEL_START=223.25`，
  即 `-1.75 + 40*5.625`）互相印證。新增 `tests/test_human_design_gate_wheel_offset.py` 把這三個
  錨點釘死為回歸測試。
- **Diff scope：**
  - `tests/fixtures/golden_example.json` / `.md` — `--example` 範例人：通道 `3-60` → `27-50`，
    9 個星體的人類圖 personality/design 閘門或爻改變。
  - `examples/sample-output.json` — 小明範例：profile `1/3` → `2/4`，10 個星體的 gate/line 改變
    （太陽 12.1→12.2、設計 36.3→36.4 等）。
  - `tests/fixtures/ephemeris_baseline.json` — 12 個 fixture 中 11 個（`ok:true` 的全部）的
    `build_json.human_design` 改變；`jupiter_station_before` 額外變了 type（顯示者→生產者）、
    authority、definition、channels；`high_latitude_65_valid` 失去 `26-44` 通道與「脾」中心的定義。
    兩個 `human_design_boundary` 註記（`hd_boundary_design_sun`、`hd_boundary_personality_moon`）
    用同一批出生資料重新算出最近邊界距離（舊值是相對錯誤輪盤的邊界，換到正確輪盤後不再貼齊，
    但仍在 0.01° 內，案例依然有效）；`western`／`ephemeris` 兩節未動（見
    `tests/fixtures/update_hd_baseline.py` 的內建理由與容忍界線）。完整 per-case before/after
    表見該腳本的執行輸出與 PR 說明。
  - `README.md` 與其 18 份翻譯 — 人類圖範例片段（`角色 1/3`、`"profile": "1/3"`、
    `{ "gate": 12, "line": 1 }`／`{ "gate": 36, "line": 3 }`）同步改為 `2/4` / `12,2` / `36,4`。
  - `tests/fixtures/golden_example_pre_1_2.json` — **這次例外重新產生**：取修正後的
    `golden_example.json` 把 `"schema_version": "1.2"` 換回 `"1.1"`（與 2026-08-06 條目記載的
    「pre = golden 換掉 schema_version 這一行」關係完全一致，byte-diff 驗證過兩檔案在該次之前
    也只差這一行）。原因：這支 fixture 凍結的是「1.1→1.2 只加一個欄位」這個宣稱，不是要永遠背著
    一個已知錯誤的人類圖輪盤；放著不修，`test_single_json_bytes_match_pre_1_2_after_version_bump`
    會強迫未來的引擎輸出繼續符合錯誤輪盤，等於把 bug 焊進保護測試。測試本身（byte-identity 邏輯）
    完全未改動，只有凍結的位元組內容更新。
- **Commands:**
  ```bash
  .venv/bin/python scripts/chart_engine.py --example --json > tests/fixtures/golden_example.json
  .venv/bin/python scripts/chart_engine.py --example        > tests/fixtures/golden_example.md
  .venv/bin/python scripts/chart_engine.py --json --name "小明" --gender 女 \
    --date 1990-06-15 --time 08:30 --tz 8 --lat 25.033 --lon 121.5654 --target 2025-01-01 \
    > examples/sample-output.json
  .venv/bin/python tests/fixtures/update_hd_baseline.py
  python3 -c "
  data = open('tests/fixtures/golden_example.json','rb').read()
  pre = data.replace(b'\"schema_version\": \"1.2\"', b'\"schema_version\": \"1.1\"', 1)
  open('tests/fixtures/golden_example_pre_1_2.json','wb').write(pre)
  "
  ```
- **Determinism:** 上述引擎指令各連續執行兩次，第二次輸出與第一次位元組相同。
- **Protected hash pin:** `tests/test_synastry_cli.py` 的
  `PROTECTED_SHA256["tests/fixtures/ephemeris_baseline.json"]` 依規定隨這次刻意的重新產生一併
  更新（不是刪除該保護測試；它保護的是「不該被別的 slice 順手改到」，不是「這個檔案的內容永遠不能
  因為修 bug 而變」）。
