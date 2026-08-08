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
