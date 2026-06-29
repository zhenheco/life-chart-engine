import json
import subprocess
from pathlib import Path

from scripts.chart_engine import ziwei


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "scripts" / "ziwei_iztro.cjs"
FIXTURE = ROOT / "tests" / "fixtures" / "ziwei_py_iztro_2_5_0_parity.json"


def _input(date, time="08:30", gender="女", target="2025-01-01", ziwei_day_divide=None):
    year, month, day = map(int, date.split("-"))
    hour, minute = map(int, time.split(":"))
    inp = {
        "name": "Test",
        "gender": gender,
        "date": (year, month, day),
        "time": (hour, minute),
        "tz_offset": 8.0,
        "lat": 25.0,
        "lon": 121.5,
        "target": target,
    }
    if ziwei_day_divide is not None:
        inp["ziwei_day_divide"] = ziwei_day_divide
    return inp


def _comparable_ziwei(result):
    return {
        "five": result["five"],
        "soul": result["soul"],
        "body": result["body"],
        "ti": result["ti"],
        "palaces": result["palaces"],
    }


def _palace(result, name):
    return next(palace for palace in result["palaces"] if palace["name"] == name)


def test_boundary_before_1985_lunar_new_year_uses_lunar_year_values():
    result = _comparable_ziwei(ziwei(_input("1985-02-10", time="00:30")))

    assert result["five"] == "水二局"
    assert result["body"] == "火星"
    assert _palace(result, "命宮") == {
        "name": "命宮",
        "gz": "丁丑",
        "flag": "身",
        "major": [],
        "minor": [
            "天魁",
            "陀羅(廟)",
        ],
        "adj": [
            "天才",
            "天壽",
            "天空",
        ],
        "decadal": "2-11",
    }


def test_non_boundary_dates_match_py_iztro_2_5_0_fixture():
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))

    for case in cases:
        actual = _comparable_ziwei(
            ziwei(
                _input(
                    case["input"]["date"],
                    time=case["input"]["time"],
                    gender=case["input"]["gender"],
                    target=case["input"]["target"],
                )
            )
        )
        assert actual == case["ziwei"], case["input"]["date"]


def test_node_sidecar_returns_plain_iztro_subset():
    request = {
        "date": "1985-2-10",
        "timeIndex": 0,
        "gender": "女",
        "fixLeap": True,
        "language": "zh-TW",
        "target": "2025-01-01",
    }

    proc = subprocess.run(
        ["node", str(SIDECAR)],
        input=json.dumps(request),
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    data = json.loads(proc.stdout)
    assert set(data) == {
        "fiveElementsClass",
        "soul",
        "body",
        "palaces",
        "horoscope",
    }
    assert set(data["horoscope"]) == {"decadal", "yearly", "age"}
    # mutagen stays a bare star-name array (1.0 contract); mutagenTyped adds 四化 type
    for scope in ("decadal", "yearly"):
        section = data["horoscope"][scope]
        assert all(isinstance(s, str) and s for s in section["mutagen"])
        typed = section["mutagenTyped"]
        assert [m["type"] for m in typed] == ["祿", "權", "科", "忌"]
        assert [m["star"] for m in typed] == section["mutagen"]
    assert data["fiveElementsClass"] == "水二局"
    assert data["body"] == "火星"
    assert len(data["palaces"]) == 12

    ming = next(p for p in data["palaces"] if p["name"] == "命宮")
    assert ming["heavenlyStem"] == "丁"
    assert ming["earthlyBranch"] == "丑"
    assert ming["isBodyPalace"] is True
    assert "astrolabe" not in ming
    assert set(ming) == {
        "name",
        "heavenlyStem",
        "earthlyBranch",
        "isOriginalPalace",
        "isBodyPalace",
        "majorStars",
        "minorStars",
        "adjectiveStars",
        "decadal",
    }


def test_late_rat_hour_day_divide_can_stay_on_current_day():
    current_day = _comparable_ziwei(
        ziwei(_input("2004-02-29", time="23:30", ziwei_day_divide="current"))
    )
    early_same_day = _comparable_ziwei(ziwei(_input("2004-02-29", time="00:30")))
    forward_day = _comparable_ziwei(ziwei(_input("2004-02-29", time="23:30")))
    early_next_day = _comparable_ziwei(ziwei(_input("2004-03-01", time="00:30")))

    assert current_day["palaces"] == early_same_day["palaces"]
    assert forward_day["palaces"] == early_next_day["palaces"]


def test_horoscope_mutagen_labeled_and_decadal_age_range():
    # Avy: 虛歲 41 in 2026 (木三局) → current 大限 is 33-42, not 43-52.
    # The bare iztro fields made an LLM consumer mislabel the decade and re-derive
    # the 四化 type from 天干; the engine now surfaces both explicitly.
    result = ziwei(_input("1986-08-19", time="19:58", gender="女", target="2026-06-24"))
    dec, yr, age = result["dec"], result["yr"], result["age"]

    # mutagen stays bare strings (non-breaking); mutagenTyped carries the 四化 type
    assert all(isinstance(s, str) for s in dec["mutagen"])
    assert [m["type"] for m in dec["mutagenTyped"]] == ["祿", "權", "科", "忌"]

    # 大限 age range surfaced directly (the off-by-one fix: 43-52 -> 33-42)
    assert dec["ageRange"] == [33, 42]

    # 丙年流年四化: 廉貞化忌
    assert yr["heavenlyStem"] == "丙"
    assert {"star": "廉貞", "type": "忌"} in yr["mutagenTyped"]

    # current 虛歲 exposed so the decade is unambiguous
    assert isinstance(age["nominalAge"], int) and age["nominalAge"] >= 1


def test_node_sidecar_rejects_missing_target():
    request = {
        "date": "1985-2-10",
        "timeIndex": 0,
        "gender": "女",
        "fixLeap": True,
        "language": "zh-TW",
    }

    proc = subprocess.run(
        ["node", str(SIDECAR)],
        input=json.dumps(request),
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )

    assert proc.returncode != 0
    assert proc.stdout == ""
    assert "target" in proc.stderr
