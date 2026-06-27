import ast
import json
import socket
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import chart_engine  # noqa: E402


BASELINE = ROOT / "tests" / "fixtures" / "ephemeris_baseline.json"
SCRIPT = ROOT / "scripts" / "chart_engine.py"
PY = sys.executable
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

    fallback = run_json(PY, str(SCRIPT))
    assert fallback.returncode == 0, fallback.stderr or fallback.stdout
    assert json.loads(fallback.stdout)["input"]["date"] == "2000-01-01"

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
    assert "astronomy-engine>=2.1.19" in requirements
