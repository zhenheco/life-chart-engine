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
