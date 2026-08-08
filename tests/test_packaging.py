import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _build_wheel(output_dir: Path) -> Path:
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(output_dir)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(output_dir.glob("*.whl"))
    assert len(wheels) == 1
    return wheels[0]


def test_wheel_contains_import_package_and_sidecar_without_scripts(tmp_path: Path) -> None:
    wheel = _build_wheel(tmp_path)

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    assert {
        "life_chart_engine/chart_engine.py",
        "life_chart_engine/validation.py",
        "life_chart_engine/ziwei_iztro.cjs",
        "life_chart_engine/vendor/iztro.cjs",
    } <= names
    assert not any(name.startswith("scripts/") for name in names)


def test_cjs_resolves_vendor_bundle_in_packaged_layout(tmp_path: Path) -> None:
    # simulate the wheel layout: sidecar + vendor/ side by side
    pkg = tmp_path / "life_chart_engine"
    (pkg / "vendor").mkdir(parents=True)
    sidecar = pkg / "ziwei_iztro.cjs"
    sidecar.write_bytes((ROOT / "scripts" / "ziwei_iztro.cjs").read_bytes())
    (pkg / "vendor" / "iztro.cjs").write_bytes((ROOT / "vendor" / "iztro.cjs").read_bytes())

    proc = subprocess.run(
        ["node", str(sidecar)],
        input='{"date":"2000-1-1","timeIndex":6,"gender":"女","fixLeap":true,"language":"zh-TW","target":"2025-01-01","dayDivide":"forward"}',
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    assert '"palaces"' in proc.stdout


def test_cjs_fails_loudly_when_no_vendor_bundle(tmp_path: Path) -> None:
    orphan = tmp_path / "ziwei_iztro.cjs"
    orphan.write_bytes((ROOT / "scripts" / "ziwei_iztro.cjs").read_bytes())

    proc = subprocess.run(
        ["node", str(orphan)],
        input="{}",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )

    assert proc.returncode == 1
    assert "vendor bundle not found" in proc.stderr


def test_installed_wheel_entry_points_work_outside_checkout(tmp_path: Path) -> None:
    wheel = _build_wheel(tmp_path / "dist")
    venv_dir = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, capture_output=True)
    pip = venv_dir / "bin" / "pip"
    subprocess.run([str(pip), "install", str(wheel)], check=True, capture_output=True, text=True)

    for exe in ("life-chart", "life-chart-engine"):
        proc = subprocess.run(
            [str(venv_dir / "bin" / exe), "--example", "--json"],
            cwd=tmp_path,  # outside the checkout: no cwd shadowing
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["ok"] is True
        assert payload["schema_version"] == "1.2"


def test_installed_wheel_dual_person_synastry_smoke(tmp_path: Path) -> None:
    """Installed package dual-person mode must emit non-empty synastry aspects.

    Guards the package-relative import path in synastry.py (``from . import semantics``)
    that single-person --example smoke never exercises.
    """
    wheel = _build_wheel(tmp_path / "dist")
    venv_dir = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, capture_output=True)
    pip = venv_dir / "bin" / "pip"
    subprocess.run([str(pip), "install", str(wheel)], check=True, capture_output=True, text=True)

    proc = subprocess.run(
        [
            str(venv_dir / "bin" / "life-chart"),
            "--json",
            "--name", "A",
            "--gender", "女",
            "--date", "1990-06-15",
            "--time", "08:30",
            "--tz", "8",
            "--lat", "25.033",
            "--lon", "121.5654",
            "--date-b", "1988-03-20",
            "--tz-b", "8",
            "--lat-b", "25.0",
            "--lon-b", "121.5",
            "--gender-b", "男",
            "--time-b", "09:15",
        ],
        cwd=tmp_path,  # outside the checkout: no cwd shadowing
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert "synastry" in proc.stdout
    payload = json.loads(proc.stdout)
    assert payload.get("ok") is True
    assert payload["synastry"]["western"]["aspects"]


def test_installed_wheel_mcp_entry_point_smoke(tmp_path: Path) -> None:
    wheel = _build_wheel(tmp_path / "dist")
    venv_dir = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, capture_output=True)
    pip = venv_dir / "bin" / "pip"

    # without the extra: friendly install hint, no traceback
    subprocess.run([str(pip), "install", str(wheel)], check=True, capture_output=True, text=True)
    bare = subprocess.run(
        [str(venv_dir / "bin" / "life-chart-mcp")],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert bare.returncode == 1
    assert "pip install 'life-chart-engine[mcp]'" in bare.stderr
    assert "Traceback" not in bare.stderr

    # with the extra: server starts on stdio and exits cleanly on closed stdin
    subprocess.run(
        [str(pip), "install", f"life-chart-engine[mcp]@{wheel.as_uri()}"],
        check=True, capture_output=True, text=True,
    )
    proc = subprocess.run(
        [str(venv_dir / "bin" / "life-chart-mcp")],
        cwd=tmp_path, input="", capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
