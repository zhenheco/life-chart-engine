"""HTTP-level functional tests for the local web UI (webapp.py).

The result page renders client-side, so assertions stay at API level:
/api/chart (the JSON export surface), /api/markdown, /api/pdf.
"""

import json
import os
import stat
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import webapp  # noqa: E402


GOOD = {
    "name": "測試", "gender": "女", "date": "1990-06-15", "time": "08:30",
    "tz": "8", "lat": "25.0", "lon": "121.5", "target": "2025-01-01",
}


@pytest.fixture()
def server():
    srv = webapp.create_server(port=0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    thread.join(timeout=5)


def _post(srv, path, payload):
    req = urllib.request.Request(
        f"http://127.0.0.1:{srv.server_port}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read()


def test_factory_reports_actual_bound_port_and_serves_index(server):
    assert server.server_port != 0
    with urllib.request.urlopen(
        f"http://127.0.0.1:{server.server_port}/", timeout=30
    ) as resp:
        assert resp.status == 200
        assert b"Life Chart" in resp.read()


def test_api_chart_is_semantically_equal_to_cli_json(server):
    status, ctype, body = _post(server, "/api/chart", GOOD)
    assert status == 200
    assert "json" in ctype
    web_payload = json.loads(body)
    assert web_payload["ok"] is True

    cli = subprocess.run(
        [webapp.VENV_PY, str(ROOT / "scripts" / "chart_engine.py"),
         "--json", "--name", "測試", "--gender", "女", "--date", "1990-06-15",
         "--time", "08:30", "--tz", "8", "--lat", "25.0", "--lon", "121.5",
         "--target", "2025-01-01"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    assert cli.returncode == 0
    assert web_payload == json.loads(cli.stdout)  # parsed-JSON semantic equality


def test_api_markdown_returns_three_system_report(server):
    status, ctype, body = _post(server, "/api/markdown", GOOD)
    assert status == 200
    assert "markdown" in ctype
    text = body.decode("utf-8")
    assert "西洋星盤" in text and "人類圖" in text and "紫微" in text


def test_empty_date_returns_friendly_error_not_usage_text(server):
    status, _ctype, body = _post(server, "/api/chart", {**GOOD, "date": ""})
    assert status == 200  # API contract: errors ride in the JSON envelope
    payload = json.loads(body)
    assert payload["ok"] is False
    assert "usage" not in payload["error"]
    assert "--date" not in payload["error"] or "輸入欄位" in payload["error"]
    assert "date" in payload["error"] or "出生" in payload["error"]


def test_main_prints_actual_bound_port_and_serves(monkeypatch, capsys):
    launched = {}

    class FakeServer:
        server_port = 43210
        def serve_forever(self):
            launched["served"] = True
        def shutdown(self):
            pass

    monkeypatch.setattr(webapp, "create_server", lambda port: FakeServer())
    monkeypatch.setattr(webapp.webbrowser, "open", lambda url: launched.setdefault("url", url))
    monkeypatch.setattr(sys, "argv", ["webapp.py", "--port", "0"])

    webapp.main()

    out = capsys.readouterr().out
    assert "http://127.0.0.1:43210/" in out
    assert launched.get("served") is True
    assert launched.get("url") == "http://127.0.0.1:43210/"


def test_friendly_error_names_only_the_failing_field(server):
    status, _ctype, body = _post(server, "/api/chart", {**GOOD, "tz": "99"})
    payload = json.loads(body)
    assert payload["ok"] is False
    assert "--tz" in payload["error"]
    assert "--lat" not in payload["error"]  # 不能整包 usage 全列


def test_life_venv_missing_executable_fails_at_factory(monkeypatch, tmp_path):
    monkeypatch.setenv("LIFE_VENV", str(tmp_path / "no-such-venv"))
    with pytest.raises(RuntimeError) as excinfo:
        webapp.create_server(port=0)
    assert "venv" in str(excinfo.value)


def test_life_venv_override_is_respected(monkeypatch, tmp_path):
    monkeypatch.setattr(webapp, "VENV_PY", webapp.VENV_PY)  # teardown 還原全域
    fake_venv = tmp_path / "venv" / "bin"
    fake_venv.mkdir(parents=True)
    (fake_venv / "python").symlink_to(sys.executable)
    monkeypatch.setenv("LIFE_VENV", str(tmp_path / "venv"))
    srv = webapp.create_server(port=0)
    try:
        assert webapp.VENV_PY == str(fake_venv / "python")
    finally:
        srv.server_close()


def test_pdf_with_mocked_browser_yields_pdf_bytes(server, monkeypatch, tmp_path):
    fake = tmp_path / "fake-browser"
    fake.write_text(
        "#!/bin/sh\n"
        "# 回歸釘：Chrome 150 的 --headless=new 會掛死；POSIX file URL 不得四斜線\n"
        'case "$*" in *--headless=new*) echo "regression: headless=new" >&2; exit 9;; esac\n'
        'case "$*" in *"file:////"*) echo "regression: file:////" >&2; exit 9;; esac\n'
        'case "$*" in *"file:///"*) : ;; *) echo "no file url" >&2; exit 9;; esac\n'
        'for a in "$@"; do case "$a" in --print-to-pdf=*) out="${a#--print-to-pdf=}";; esac; done\n'
        'printf "%%PDF-1.4 fake" > "$out"\n'
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(webapp, "find_browser", lambda: str(fake))

    status, ctype, body = _post(server, "/api/pdf", GOOD)
    assert status == 200
    assert ctype == "application/pdf"
    assert body.startswith(b"%PDF")


def _browser_can_print():
    """Probe: can the discovered browser actually headless-print here?

    Some execution contexts (observed: python-parent subprocess under a
    sandboxed harness on macOS, Chrome 150) hang on headless printing even
    though the same command works from an interactive shell. The real-browser
    test only runs where a 10s probe print succeeds — everywhere else the
    mocked-browser test carries the coverage.
    """
    browser = webapp.find_browser()
    if browser is None:
        return False
    import tempfile
    tmp = tempfile.mkdtemp(prefix="lifechart_probe_")
    html = Path(tmp) / "probe.html"
    pdf = Path(tmp) / "probe.pdf"
    html.write_text("<html><body>probe</body></html>", encoding="utf-8")
    try:
        subprocess.run(
            [browser, "--headless", "--disable-gpu", "--no-first-run",
             "--user-data-dir=" + str(Path(tmp) / "ud"),
             "--print-to-pdf=" + str(pdf), html.as_uri()],
            capture_output=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return pdf.exists()


_BROWSER_PRINTS = _browser_can_print()


@pytest.mark.skipif(
    not _BROWSER_PRINTS,
    reason="no discovered browser that can headless-print in this environment",
)
def test_pdf_with_real_discovered_browser(server):
    status, ctype, body = _post(server, "/api/pdf", GOOD)
    assert status == 200, body[:200]
    assert ctype == "application/pdf"
    assert body.startswith(b"%PDF")
