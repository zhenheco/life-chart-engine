"""Loud-error contract when the Node sidecar is unavailable or failing.

Every surface must fail loudly with a message naming the supported runtime
("Node.js >= 18") and never emit a partial chart.
"""

import json
import os
import stat
import subprocess
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "chart_engine.py"
PY = sys.executable
ARGS = [
    "--gender", "女", "--date", "1990-06-15", "--time", "08:30",
    "--tz", "8", "--lat", "25.0", "--lon", "121.5", "--target", "2025-01-01",
]


def _env_without_node(tmp_path, fake_node_script=None):
    """PATH containing only python's dir (and optionally a fake node)."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    if fake_node_script is not None:
        fake = bindir / "node"
        fake.write_text(fake_node_script)
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    env = dict(os.environ)
    env["PATH"] = str(bindir)
    return env


def test_json_mode_without_node_emits_one_loud_envelope(tmp_path):
    result = subprocess.run(
        [PY, str(SCRIPT), *ARGS, "--json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        env=_env_without_node(tmp_path),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "Node.js >= 18" in payload["error"]
    # stdout is exactly one JSON object, nothing else
    assert result.stdout.strip() == json.dumps(
        payload, ensure_ascii=False, indent=2
    ).strip()


def test_markdown_mode_without_node_keeps_stdout_empty(tmp_path):
    result = subprocess.run(
        [PY, str(SCRIPT), *ARGS],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        env=_env_without_node(tmp_path),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Node.js >= 18" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "fake_node",
    [
        "#!/bin/sh\necho 'boom' >&2\nexit 3\n",          # non-zero exit
        "#!/bin/sh\nexec /bin/sleep 60\n",                # hangs → timeout (absolute path: PATH is stripped)
        "#!/not/an/interpreter\n",                       # exec-format/launch OSError
    ],
    ids=["nonzero-exit", "timeout", "exec-error"],
)
def test_failing_or_hanging_node_converges_to_the_same_loud_path(tmp_path, fake_node):
    result = subprocess.run(
        [PY, str(SCRIPT), *ARGS, "--json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        env={**_env_without_node(tmp_path, fake_node),
             **({"LIFE_ZIWEI_TIMEOUT": "2"} if "sleep" in fake_node else {})},
        timeout=90,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "Node.js >= 18" in payload["error"]


def test_http_chart_500_withholds_sidecar_message(monkeypatch):
    """HTTP is a public surface: the sidecar's stderr (container paths, Node
    output) must never reach the caller. The operator guidance still reaches
    the CLI (test above), the container log and Sentry — the HTTP body is a
    fixed message."""
    def node_is_gone(_inp):
        raise RuntimeError(
            "紫微斗數 sidecar failed: node executable not found on PATH "
            "(this engine requires Node.js >= 18)"
        )

    fake_engine = types.ModuleType("scripts.chart_engine")

    def build_json(inp):
        node_is_gone(inp)

    fake_engine.build_json = build_json
    monkeypatch.setitem(sys.modules, "scripts.chart_engine", fake_engine)
    monkeypatch.setenv("ENGINE_ALLOW_OPEN", "1")
    sys.modules.pop("server", None)
    import server
    from fastapi.testclient import TestClient

    client = TestClient(server.app, raise_server_exceptions=False)
    response = client.post("/chart", json={
        "date": "1990-06-15", "time": "08:30", "tz": 8,
        "lat": 25.0, "lon": 121.5, "gender": "女",
    })
    sys.modules.pop("server", None)

    assert response.status_code == 500
    assert response.json() == {
        "ok": False,
        "error": "internal_error",
        "message": "chart computation failed",
    }
    assert "Node.js" not in response.text
    assert "sidecar" not in response.text
