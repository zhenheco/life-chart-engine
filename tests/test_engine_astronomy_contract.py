import ast
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import chart_engine  # noqa: E402


BASELINE = ROOT / "tests" / "fixtures" / "ephemeris_baseline.json"
SCRIPT = ROOT / "scripts" / "chart_engine.py"
PY = sys.executable
GOLDEN_JSON = ROOT / "tests" / "fixtures" / "golden_example.json"
GOLDEN_MARKDOWN = ROOT / "tests" / "fixtures" / "golden_example.md"
GOLDEN_PLATFORM = (ROOT / "tests" / "fixtures" / "golden_platform.txt").read_text().strip()
BASE_ARGS = [
    PY,
    str(SCRIPT),
    "--name",
    "Test",
    "--gender",
    "女",
    "--date",
    "1990-06-15",
    "--time",
    "08:30",
    "--tz",
    "8",
    "--lat",
    "25.033",
    "--lon",
    "121.5654",
    "--target",
    "2025-01-01",
]

TOP_KEYS = ["ok", "schema_version", "input", "western", "human_design", "ziwei", "meta"]
DEFAULT_LON_TOL = 0.017
LON_TOL = {"月亮": 0.05, "北交點": 0.05, "南交點": 0.05}
HOUSE_FIXTURE_TOLS = {
    "taipei_standard": 0.05,
    "london_solar_sign_cusp": 0.05,
    "high_latitude_65_valid": 0.2,
}


def baseline_data():
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def engine_input(item):
    y, mo, d = map(int, item["input"]["date"].split("-"))
    hh, mm = map(int, item["input"]["time"].split(":"))
    return {
        "name": item["input"]["name"],
        "gender": item["input"]["gender"],
        "date": (y, mo, d),
        "time": (hh, mm),
        "tz_offset": item["input"]["tz_offset"],
        "lat": item["input"]["lat"],
        "lon": item["input"]["lon"],
        "target": item["input"]["target"],
    }


def build_json_or_error(inp):
    try:
        return chart_engine.build_json(inp)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "schema_version": "1.1"}


def shape(value):
    if isinstance(value, dict):
        return ("dict", frozenset(value.keys()), {key: shape(val) for key, val in value.items()})
    if isinstance(value, list):
        return ("list", len(value), [shape(value[0])] if value else [])
    return type(value).__name__


def angular_delta(a, b):
    return abs((a - b + 180) % 360 - 180)


def run_json(*args, text=True):
    return subprocess.run(
        [*args, "--json"],
        cwd=ROOT,
        capture_output=True,
        text=text,
        encoding="utf-8" if text else None,
    )


@pytest.mark.parametrize("json_mode", [False, True])
@pytest.mark.parametrize("missing_flag", ["--date", "--time", "--tz", "--lat", "--lon", "--gender"])
def test_cli_reports_each_missing_birth_flag_without_stdout(missing_flag, json_mode):
    args = BASE_ARGS[2:]
    missing_index = args.index(missing_flag)
    args = args[:missing_index] + args[missing_index + 2 :]
    if json_mode:
        args.append("--json")

    result = subprocess.run(
        [PY, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert missing_flag in result.stderr


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        ("--date", "1_990-06-15"),
        ("--date", "1990-13-45"),
        ("--date", "1991-02-29"),
        ("--date", "1899-12-31"),
        ("--date", "2101-01-01"),
        ("--time", "25:99"),
        ("--time", "8: 5"),
        ("--tz", "20"),
        ("--tz", "nan"),
        ("--tz", "inf"),
        ("--lat", "95"),
        ("--lat", "-inf"),
        ("--lon", "200"),
        ("--lon", "nan"),
        ("--target", "1990-13-45"),
        ("--target", "1991-02-29"),
        ("--target", "1899-12-31"),
        ("--target", "2101-01-01"),
    ],
)
def test_cli_rejects_invalid_birth_values_through_argparse(flag, value):
    args = BASE_ARGS[2:]
    value_index = args.index(flag) + 1
    args[value_index] = value

    result = subprocess.run(
        [PY, str(SCRIPT), *args, "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert flag in result.stderr


def test_cli_accepts_and_normalizes_unpadded_dates_times_and_window_boundaries():
    for birth_date, target, expected_date, expected_time in [
        ("1990-6-15", "2025-1-1", "1990-06-15", "08:05"),
        ("1900-1-1", "1900-1-1", "1900-01-01", "08:05"),
        ("2100-12-31", "2100-12-31", "2100-12-31", "08:05"),
    ]:
        args = BASE_ARGS[2:]
        args[args.index("--date") + 1] = birth_date
        args[args.index("--time") + 1] = "8:5"
        args[args.index("--target") + 1] = target
        result = run_json(PY, str(SCRIPT), *args)
        assert result.returncode == 0, result.stderr or result.stdout
        payload = json.loads(result.stdout)
        assert payload["input"]["date"] == expected_date
        assert payload["input"]["time"] == expected_time
        assert payload["input"]["target"] == target.replace("-1-1", "-01-01")


@pytest.mark.parametrize(
    ("birth_flag", "value"),
    [
        ("--date", "2000-01-01"),
        ("--time", "12:00"),
        ("--tz", "8"),
        ("--lat", "25.033"),
        ("--lon", "121.5654"),
        ("--gender", "女"),
    ],
)
def test_example_rejects_birth_flag_combinations(birth_flag, value):
    result = subprocess.run(
        [PY, str(SCRIPT), "--example", birth_flag, value, "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "--example" in result.stderr
    assert birth_flag in result.stderr


def test_example_accepts_non_birth_overrides():
    result = run_json(
        PY,
        str(SCRIPT),
        "--example",
        "--name",
        "Renamed",
        "--target",
        "2026-01-02",
        "--ziwei-day-divide",
        "current",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["input"]["name"] == "Renamed"
    assert payload["input"]["target"] == "2026-01-02"


@pytest.mark.skipif(
    sys.platform != GOLDEN_PLATFORM,
    reason="byte identity is only meaningful on the platform where goldens were captured "
    f"(fixtures captured on {GOLDEN_PLATFORM}; regenerate on linux to enable in CI)",
)
@pytest.mark.parametrize(
    ("extra_args", "fixture"),
    [(["--json"], GOLDEN_JSON), ([], GOLDEN_MARKDOWN)],
)
def test_example_matches_pre_change_golden_bytes(extra_args, fixture):
    result = subprocess.run(
        [PY, str(SCRIPT), "--example", *extra_args],
        cwd=ROOT,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8")
    assert result.stdout == fixture.read_bytes()


def test_main_accepts_argv_and_json_stdout_uses_the_shared_serializer(monkeypatch, capsys):
    envelope = {"ok": True, "schema_version": "1.1", "sentinel": "盤"}
    monkeypatch.setattr(chart_engine, "build_json", lambda _inp: envelope)

    exit_code = chart_engine.main([*BASE_ARGS[2:], "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == chart_engine.to_json_text(envelope) + "\n"
    assert captured.err == ""


def test_main_buffers_markdown_before_one_stdout_write(monkeypatch):
    writes = []
    monkeypatch.setattr(chart_engine, "compose_markdown", lambda _inp: "complete chart\n")
    monkeypatch.setattr(chart_engine.sys.stdout, "write", writes.append)

    exit_code = chart_engine.main(BASE_ARGS[2:])

    assert exit_code == 0
    assert writes == ["complete chart\n"]


def test_contract_literals_and_shape_match_baseline():
    data = baseline_data()
    assert data["engine_schema_version"] == "1.1"
    for item in data["fixtures"]:
        got = build_json_or_error(engine_input(item))
        assert shape(got) == shape(item["build_json"]), item["id"]
        assert got["schema_version"] == "1.1"
        if got["ok"]:
            assert list(got) == TOP_KEYS
            assert got["meta"]["ephemeris"] == "astronomy-engine"
            assert got["western"]["system"] == "Tropical / Placidus / astronomy-engine"


def test_western_values_and_retrograde_flags_stay_within_baseline_tolerance():
    for item in baseline_data()["fixtures"]:
        expected = item["build_json"]
        got = build_json_or_error(engine_input(item))
        assert got["ok"] is expected["ok"], item["id"]
        if not got["ok"]:
            continue

        expected_planets = {p["name"]: p for p in expected["western"]["planets"]}
        for planet in got["western"]["planets"]:
            name = planet["name"]
            tol = LON_TOL.get(name, DEFAULT_LON_TOL)
            delta = angular_delta(planet["lon"], expected_planets[name]["lon"])
            assert delta <= tol, f"{item['id']} {name} lon delta={delta:.8f} tol={tol}"
            assert planet["retrograde"] is expected_planets[name]["retrograde"], item["id"]

        if item["id"] in HOUSE_FIXTURE_TOLS:
            house_tol = HOUSE_FIXTURE_TOLS[item["id"]]
            for got_house, expected_house in zip(
                got["western"]["houses"], expected["western"]["houses"], strict=True
            ):
                delta = angular_delta(got_house["lon"], expected_house["lon"])
                assert delta <= house_tol, (
                    f"{item['id']} house {got_house['house']} delta={delta:.8f} tol={house_tol}"
                )
            for key in ("ascendant", "midheaven"):
                delta = angular_delta(got["western"][key]["lon"], expected["western"][key]["lon"])
                assert delta <= house_tol, f"{item['id']} {key} delta={delta:.8f} tol={house_tol}"


def test_human_design_boundary_fixtures_report_gate_or_line_jumps(capsys):
    checked = 0
    hard_failures = []
    for item in baseline_data()["fixtures"]:
        if not item.get("annotations", {}).get("human_design_boundary"):
            continue
        checked += 1
        got_hd = build_json_or_error(engine_input(item))["human_design"]
        expected_hd = item["build_json"]["human_design"]
        for key in ["type", "authority", "definition"]:
            if got_hd[key] != expected_hd[key]:
                hard_failures.append(f"{item['id']} {key}: got={got_hd[key]!r} expected={expected_hd[key]!r}")
        for got_gate, expected_gate in zip(got_hd["gates"], expected_hd["gates"], strict=True):
            for side in ("personality", "design"):
                if got_gate[side] != expected_gate[side]:
                    print(
                        "HD_JUMP",
                        item["id"],
                        got_gate["planet"],
                        side,
                        f"got={got_gate[side]['gate']}.{got_gate[side]['line']}",
                        f"expected={expected_gate[side]['gate']}.{expected_gate[side]['line']}",
                    )
    captured = capsys.readouterr()
    if captured.out:
        print(captured.out, end="")
    assert checked >= 2
    assert not hard_failures, "HD type/authority/definition changed:\n" + "\n".join(hard_failures)


def test_cli_exit_codes_fallback_and_deterministic_output():
    ok = run_json(*BASE_ARGS)
    assert ok.returncode == 0, ok.stderr or ok.stdout
    payload = json.loads(ok.stdout)
    assert list(payload) == TOP_KEYS
    assert payload["meta"]["ephemeris"] == "astronomy-engine"
    assert payload["western"]["system"] == "Tropical / Placidus / astronomy-engine"

    example = run_json(PY, str(SCRIPT), "--example")
    assert example.returncode == 0, example.stderr or example.stdout
    assert json.loads(example.stdout)["input"]["date"] == "2000-01-01"

    invalid_arg = subprocess.run(
        [PY, str(SCRIPT), "--gender", "x"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert invalid_arg.returncode == 2

    lat70 = run_json(
        PY,
        str(SCRIPT),
        "--name",
        "lat70",
        "--gender",
        "女",
        "--date",
        "1990-06-15",
        "--time",
        "08:30",
        "--tz",
        "0",
        "--lat",
        "70",
        "--lon",
        "0",
        "--target",
        "2025-01-01",
    )
    assert lat70.returncode == 1
    assert json.loads(lat70.stdout)["ok"] is False

    first = run_json(*BASE_ARGS, text=False)
    second = run_json(*BASE_ARGS, text=False)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout


def test_build_json_does_not_need_python_network(monkeypatch):
    def fail_socket(*_args, **_kwargs):
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket, "socket", fail_socket)
    got = chart_engine.build_json(
        {
            "name": "offline",
            "gender": "女",
            "date": (1990, 6, 15),
            "time": (8, 30),
            "tz_offset": 8.0,
            "lat": 25.033,
            "lon": 121.5654,
            "target": "2025-01-01",
        }
    )
    assert got["ok"] is True


def test_runtime_and_test_sources_do_not_import_swisseph():
    checked = [ROOT / "scripts" / "chart_engine.py", ROOT / "scripts" / "ephemeris.py"]
    checked.extend((ROOT / "tests").glob("test_*.py"))
    for path in checked:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name for alias in node.names}
                assert "swisseph" not in names, str(path)
            if isinstance(node, ast.ImportFrom):
                assert node.module != "swisseph", str(path)
    assert "swisseph" not in sys.modules


def test_requirements_use_astronomy_engine_without_pyswisseph():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "pyswisseph" not in requirements
    # 精確 pin 與 pyproject 一致：golden fixtures 依賴 byte-exact 輸出
    assert "astronomy-engine==2.1.19" in requirements


def test_horoscope_failure_fails_the_whole_request_loudly(monkeypatch):
    # all-or-nothing: a horoscope construction failure must never yield
    # an "ok": true response with horoscope=None (silent partial result)
    real_ziwei = chart_engine.ziwei

    def ziwei_without_horoscope_keys(inp):
        zw = real_ziwei(inp)
        return {k: v for k, v in zw.items() if k not in ("dec", "yr", "age")}

    monkeypatch.setattr(chart_engine, "ziwei", ziwei_without_horoscope_keys)
    inp = dict(chart_engine.INPUT)

    with pytest.raises(KeyError):
        chart_engine.build_json(inp)
