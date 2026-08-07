"""E1 — synastry mode skeleton: CLI dual-person mode, schema 1.2, byte-identity.

Each acceptance criterion has a dedicated test that can fail independently.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "chart_engine.py"
PY = sys.executable
PRE_1_2 = ROOT / "tests" / "fixtures" / "golden_example_pre_1_2.json"
GOLDEN_JSON = ROOT / "tests" / "fixtures" / "golden_example.json"
GOLDEN_MD = ROOT / "tests" / "fixtures" / "golden_example.md"
SAMPLE = ROOT / "examples" / "sample-output.json"
PROVENANCE = ROOT / "tests" / "fixtures" / "GOLDEN_PROVENANCE.md"

# Content hashes for files that must not be rewritten by this slice.
# Do not use `git diff` as an oracle: it is blind to staged-only changes and
# to content after commit. Hashes match the HEAD content as of this pin.
PROTECTED_SHA256 = {
    "tests/fixtures/ephemeris_baseline.json": (
        "ca1ca71e50985c1c246fab58b1c6246f7d58e94157f2876262f1b523f689dd8f"
    ),
    "docs/specs/2026-07-13-engine-polish-funnel-design.md": (
        "7e2ec5669411c9af1f32faa2017d8997586ec1e444e6f4061227f446e31e8e2e"
    ),
}

A_ARGS = [
    "--name", "A",
    "--gender", "女",
    "--date", "1990-06-15",
    "--time", "08:30",
    "--tz", "8",
    "--lat", "25.033",
    "--lon", "121.5654",
]

B_REQUIRED = {
    "--date-b": "1988-03-20",
    "--tz-b": "8",
    "--lat-b": "25.0",
    "--lon-b": "121.5",
    "--gender-b": "男",
}

SYNASTRY_KEYS_WESTERN = {
    "aspects",
    "a_planets_in_b_houses",
    "b_planets_in_a_houses",
    "angle_contacts_a_to_b",
    "angle_contacts_b_to_a",
}
SYNASTRY_KEYS_HD = {"channel_connections", "center_states", "participants"}
TOP_SYNASTRY_KEYS = {
    "ok",
    "schema_version",
    "western",
    "human_design",
    "ziwei",
    "synastry",
    "evidence_completeness",
}


def _run(*args, env=None, text=True):
    return subprocess.run(
        [PY, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=text,
        encoding="utf-8" if text else None,
        env=env,
    )


def _b_flags(**overrides):
    flags = dict(B_REQUIRED)
    flags.update(overrides)
    out = []
    for k, v in flags.items():
        out.extend([k, v])
    return out


def _env_without_node(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["PATH"] = str(bindir)
    return env


# ---------------------------------------------------------------------------
# AC: mode entry on any -b flag; missing required → exit 2
# ---------------------------------------------------------------------------

def test_only_time_b_exits_2_does_not_emit_single_chart():
    """Story #23: any -b flag (even just --time-b) enters synastry mode.

    Full A-side flags are supplied so that ignoring --time-b as noise would
    silently emit a single-person chart (the forbidden outcome).
    """
    result = _run(*A_ARGS, "--time-b", "08:30", "--json")
    assert result.returncode == 2, (
        f"expected exit 2 for incomplete synastry mode, got {result.returncode}; "
        f"stdout={result.stdout[:200]!r}"
    )
    assert result.stdout == "", "must not emit a single-person chart body"


def test_three_required_b_flags_exits_2_names_the_two_missing():
    """Three of five required -b flags → exit 2; stderr names the two missing."""
    result = _run(
        *A_ARGS,
        "--date-b", "1988-03-20",
        "--tz-b", "8",
        "--lat-b", "25.0",
        # missing: --lon-b, --gender-b
        "--json",
    )
    assert result.returncode == 2
    err = result.stderr
    assert "--lon-b" in err or "lon-b" in err
    assert "--gender-b" in err or "gender-b" in err


# ---------------------------------------------------------------------------
# AC: dual mode requires --json
# ---------------------------------------------------------------------------

def test_synastry_mode_without_json_exits_2_with_explanation():
    result = _run(*A_ARGS, *_b_flags(), "--time-b", "09:00")
    assert result.returncode == 2
    assert result.stdout == ""
    combined = result.stderr.lower()
    assert "json" in combined
    assert "synastry" in combined or "雙人" in result.stderr or "only" in combined


# ---------------------------------------------------------------------------
# AC: --example mutually exclusive with any -b flag
# ---------------------------------------------------------------------------

def test_example_with_time_b_exits_2_mutual_exclusion():
    result = _run("--example", "--time-b", "08:30", "--json")
    assert result.returncode == 2
    assert result.stdout == ""
    err = result.stderr.lower()
    assert "example" in err
    assert "mutual" in err or "互斥" in result.stderr or "cannot" in err or "not" in err


def test_example_with_all_required_b_flags_exits_2_mutual_exclusion():
    result = _run("--example", *_b_flags(), "--json")
    assert result.returncode == 2
    assert result.stdout == ""
    err = result.stderr.lower()
    assert "example" in err


# ---------------------------------------------------------------------------
# AC: time unknown in dual mode; single mode time still required
# ---------------------------------------------------------------------------

def test_time_b_omitted_is_accepted_as_unknown_in_synastry_mode():
    result = _run(*A_ARGS, *_b_flags(), "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert "synastry" in payload


def test_time_b_unknown_literal_is_accepted_in_synastry_mode():
    result = _run(*A_ARGS, *_b_flags(), "--time-b", "unknown", "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert "synastry" in payload


def _a_args_without_time():
    a_no_time = []
    skip_next = False
    for a in A_ARGS:
        if skip_next:
            skip_next = False
            continue
        if a == "--time":
            skip_next = True
            continue
        a_no_time.append(a)
    return a_no_time


def test_time_a_omitted_is_accepted_in_synastry_mode():
    result = _run(*_a_args_without_time(), *_b_flags(), "--time-b", "09:00", "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["schema_version"] == "1.2"
    assert "synastry" in payload


def test_time_a_unknown_literal_is_accepted_in_synastry_mode():
    """A-side may pass the literal ``unknown`` in dual mode (not only omit --time)."""
    a_unknown = []
    skip_next = False
    for a in A_ARGS:
        if skip_next:
            skip_next = False
            continue
        if a == "--time":
            a_unknown.extend(["--time", "unknown"])
            skip_next = True
            continue
        a_unknown.append(a)
    result = _run(*a_unknown, *_b_flags(), "--time-b", "09:00", "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["schema_version"] == "1.2"
    assert "synastry" in payload


def test_single_mode_time_still_required():
    result = _run(
        "--name", "Solo",
        "--gender", "女",
        "--date", "1990-06-15",
        "--tz", "8",
        "--lat", "25.0",
        "--lon", "121.5",
        "--json",
    )
    assert result.returncode == 2
    assert "--time" in result.stderr or "time" in result.stderr


@pytest.mark.parametrize(
    "flag, bad_value, field",
    [
        ("--lat-b", "999", "lat"),
        ("--lon-b", "999", "lon"),
        ("--tz-b", "99", "tz"),
        ("--date-b", "not-a-date", "date"),
        ("--time-b", "not-a-time", "time"),
    ],
)
def test_b_side_validation_names_b_flag(flag, bad_value, field):
    """B-side validation errors must report --<field>-b, not A-side --<field>:."""
    overrides = {flag: bad_value}
    # time-b is not in B_REQUIRED; pass a valid time unless this case is testing it.
    time_args = () if flag == "--time-b" else ("--time-b", "09:00")
    result = _run(*A_ARGS, *_b_flags(**overrides), *time_args, "--json")
    assert result.returncode == 2
    assert result.stdout == ""
    assert f"--{field}-b" in result.stderr
    assert f"--{field}:" not in result.stderr


# ---------------------------------------------------------------------------
# AC: single has no synastry key; dual has full synastry skeleton
# ---------------------------------------------------------------------------

def test_single_json_output_has_no_synastry_key():
    result = _run(*A_ARGS, "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert "synastry" not in payload


def test_dual_json_output_has_synastry_with_complete_keys():
    result = _run(*A_ARGS, *_b_flags(), "--time-b", "09:15", "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert set(payload) >= TOP_SYNASTRY_KEYS
    assert payload["schema_version"].startswith("1.")
    assert payload["schema_version"] == "1.2"
    syn = payload["synastry"]
    assert set(syn["western"]) == SYNASTRY_KEYS_WESTERN
    # E2 fills aspects[]; E3 fills overlay + angle contacts; E4 fills HD.
    assert isinstance(syn["western"]["aspects"], list)
    for k in SYNASTRY_KEYS_WESTERN:
        assert isinstance(syn["western"][k], list)
        assert syn["western"][k], f"{k} non-empty when both times known"
    assert set(syn["human_design"]) == SYNASTRY_KEYS_HD
    assert isinstance(syn["human_design"]["channel_connections"], list)
    assert syn["human_design"]["channel_connections"], (
        "channel_connections non-empty when both times known"
    )
    assert len(syn["human_design"]["center_states"]) == 9
    assert "person_a" in syn["human_design"]["participants"]
    assert "person_b" in syn["human_design"]["participants"]
    for person in ("person_a", "person_b"):
        assert set(syn["human_design"]["participants"][person]) == {
            "type",
            "strategy",
            "authority",
            "split_bridges",
            "hanging_gates_completed",
        }
    assert syn["unavailable"] == []
    assert payload["western"] == {"person_a": {}, "person_b": {}}
    assert payload["human_design"] == {"person_a": {}, "person_b": {}}
    assert payload["ziwei"]["status"] == "not_computed"
    assert "methodology_note" in payload["ziwei"]
    # Both times known → aspects non-empty and evidence_completeness full.
    assert syn["western"]["aspects"]
    assert payload["evidence_completeness"] == "full"


# ---------------------------------------------------------------------------
# AC: schema_version 1.2; no residual "1.1" in chart_engine.py / server.py
# ---------------------------------------------------------------------------

def test_schema_version_is_1_2_family():
    result = _run("--example", "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["schema_version"].startswith("1.")
    assert payload["schema_version"] == "1.2"


def test_runtime_sources_have_no_schema_version_1_1_literal():
    for rel in ("scripts/chart_engine.py", "server.py", "scripts/synastry.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert '"1.1"' not in text, f"{rel} still contains runtime schema_version 1.1 literal"


# ---------------------------------------------------------------------------
# AC: byte identity vs pre-1.2 golden after 1.1→1.2 string replace
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    sys.platform != (ROOT / "tests" / "fixtures" / "golden_platform.txt").read_text().strip(),
    reason="byte identity only on capture platform",
)
def test_single_json_bytes_match_pre_1_2_after_version_bump():
    assert PRE_1_2.is_file(), "golden_example_pre_1_2.json must be captured before code changes"
    pre = PRE_1_2.read_bytes()
    assert b'"schema_version": "1.1"' in pre, "pre-1.2 fixture must be genuine pre-change bytes"
    expected = pre.replace(b'"schema_version": "1.1"', b'"schema_version": "1.2"', 1)
    result = _run("--example", "--json", text=False)
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert result.stdout == expected


def test_pre_1_2_fixture_is_not_the_regenerated_golden():
    """Guard against self-proving: pre must differ from post-bump golden."""
    assert PRE_1_2.is_file()
    assert GOLDEN_JSON.is_file()
    pre = PRE_1_2.read_text(encoding="utf-8")
    # After regeneration golden is 1.2; pre must remain 1.1
    assert '"schema_version": "1.1"' in pre
    # And pre must not be identical to a wrongly-copied regenerated golden
    golden = GOLDEN_JSON.read_text(encoding="utf-8")
    if '"schema_version": "1.2"' in golden:
        assert pre != golden


# ---------------------------------------------------------------------------
# AC: sample-output deep-equal excluding schema_version; golden md zero diff intent
# ---------------------------------------------------------------------------

def test_single_output_deep_equal_sample_excluding_schema_version():
    """examples/sample-output.json is the 小明 oracle (not --example 範例)."""
    result = _run(
        "--name", "小明",
        "--gender", "女",
        "--date", "1990-06-15",
        "--time", "08:30",
        "--tz", "8",
        "--lat", "25.0330",
        "--lon", "121.5654",
        "--target", "2025-01-01",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    got = json.loads(result.stdout)
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    got.pop("schema_version", None)
    sample.pop("schema_version", None)
    assert got == sample


def test_golden_md_byte_identical_to_example_markdown():
    result = _run("--example", text=False)
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert result.stdout == GOLDEN_MD.read_bytes()


# ---------------------------------------------------------------------------
# AC: dual mode deterministic byte-for-byte
# ---------------------------------------------------------------------------

def test_dual_mode_stdout_byte_identical_across_two_runs():
    args = [*A_ARGS, *_b_flags(), "--time-b", "10:00", "--json"]
    r1 = _run(*args, text=False)
    r2 = _run(*args, text=False)
    assert r1.returncode == 0, r1.stderr.decode("utf-8", "replace")
    assert r2.returncode == 0, r2.stderr.decode("utf-8", "replace")
    assert r1.stdout == r2.stdout


# ---------------------------------------------------------------------------
# AC: node absent → dual mode still succeeds
# ---------------------------------------------------------------------------

def test_dual_mode_succeeds_without_node_on_path(tmp_path):
    result = _run(
        *A_ARGS,
        *_b_flags(),
        "--time-b", "08:30",
        "--json",
        env=_env_without_node(tmp_path),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert "synastry" in payload


# ---------------------------------------------------------------------------
# AC: swisseph scan list covers new modules
# ---------------------------------------------------------------------------

def test_swisseph_scan_list_includes_synastry_and_semantics():
    contract = (ROOT / "tests" / "test_engine_astronomy_contract.py").read_text(encoding="utf-8")
    assert "synastry.py" in contract
    assert "semantics.py" in contract
    # Files must exist so the scan can cover them
    assert (ROOT / "scripts" / "synastry.py").is_file()
    assert (ROOT / "scripts" / "semantics.py").is_file()


def test_new_modules_do_not_import_swisseph():
    for rel in ("scripts/synastry.py", "scripts/semantics.py"):
        path = ROOT / rel
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert "swisseph" not in {a.name for a in node.names}, rel
            if isinstance(node, ast.ImportFrom):
                assert node.module != "swisseph", rel


# ---------------------------------------------------------------------------
# AC: protected files / history must not be rewritten
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_ephemeris_baseline_not_modified():
    rel = "tests/fixtures/ephemeris_baseline.json"
    path = ROOT / rel
    assert path.is_file()
    assert _sha256_file(path) == PROTECTED_SHA256[rel]


def test_2026_07_13_specs_not_modified():
    specs = sorted((ROOT / "docs" / "specs").glob("2026-07-13-*"))
    assert specs, "expected at least one docs/specs/2026-07-13-* file"
    for path in specs:
        rel = path.relative_to(ROOT).as_posix()
        assert rel in PROTECTED_SHA256, f"missing protected hash pin for {rel}"
        assert _sha256_file(path) == PROTECTED_SHA256[rel], (
            f"{rel} content hash changed; this slice must not rewrite 2026-07-13 specs"
        )


def test_readme_version_history_paragraphs_still_mention_1_1_additive():
    """History prose about the 1.1 additive bump must remain in every README.

    Asserts the exact backtick-form version-history markers (not bare ``1.1`` /
    package-version strings that also appear elsewhere in the docs).
    """
    readmes = sorted(ROOT.glob("README*.md"))
    assert len(readmes) >= 19, f"expected all READMEs, found {len(readmes)}"
    # Markers unique to the 1.1 version-history narrative (present in every
    # language). Bare "1.1" / "schema_version" alone are too weak — they match
    # unrelated package version lines and field tables.
    history_markers = (
        "`schema_version` `1.1`",
        "`schema_version` `1.0`",
        "mutagenTyped",
        "decadal.ageRange",
    )
    for path in readmes:
        text = path.read_text(encoding="utf-8")
        for marker in history_markers:
            assert marker in text, f"{path.name} missing version-history marker {marker!r}"
    # English README must retain the exact additive-bump sentence.
    en = (ROOT / "README.md").read_text(encoding="utf-8")
    assert (
        "`schema_version` `1.1` is an additive, backward-compatible bump" in en
    ), "README.md lost the exact 1.1 additive bump history sentence"


def test_golden_provenance_records_1_2_regeneration():
    text = PROVENANCE.read_text(encoding="utf-8")
    assert "1.2" in text and "schema_version" in text
    assert "golden_example_pre_1_2.json" in text
    assert "2026" in text


def test_single_and_dual_schema_version_match():
    """Single and dual --json paths must emit the same schema_version string."""
    single = _run("--example", "--json")
    dual = _run(*A_ARGS, *_b_flags(), "--time-b", "09:15", "--json")
    assert single.returncode == 0, single.stderr or single.stdout
    assert dual.returncode == 0, dual.stderr or dual.stdout
    sv_single = json.loads(single.stdout)["schema_version"]
    sv_dual = json.loads(dual.stdout)["schema_version"]
    assert sv_single == sv_dual
