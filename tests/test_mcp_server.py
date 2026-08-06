"""In-process contract tests for the MCP surface (stdio server, compute_chart).

Uses the SDK's memory transport so the no-network guard can observe the whole
call path (a subprocess would escape the monkeypatch).
"""

import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

import anyio  # noqa: E402  (mcp dependency)
from mcp.shared.memory import create_connected_server_and_client_session  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import chart_engine  # noqa: E402
import mcp_server  # noqa: E402


GOOD_INPUT = {
    "date": "1990-06-15",
    "time": "08:30",
    "tz": 8,
    "lat": 25.0,
    "lon": 121.5,
    "gender": "女",
    "target": "2025-01-01",
}


def _run(coro):
    return anyio.run(coro)


def test_tools_list_pins_compute_chart_input_schema():
    async def scenario():
        async with create_connected_server_and_client_session(
            mcp_server.server._mcp_server
        ) as session:
            tools = await session.list_tools()
            return tools

    tools = _run(scenario)
    assert [t.name for t in tools.tools] == ["compute_chart"]
    schema = tools.tools[0].inputSchema
    assert set(schema["required"]) == {"date", "time", "tz", "lat", "lon", "gender"}
    for optional in ("name", "target", "ziwei_day_divide"):
        assert optional in schema["properties"]
        assert optional not in schema["required"]


def test_call_tool_returns_single_text_content_byte_equal_to_cli_json():
    async def scenario():
        async with create_connected_server_and_client_session(
            mcp_server.server._mcp_server
        ) as session:
            return await session.call_tool("compute_chart", GOOD_INPUT)

    result = _run(scenario)
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].type == "text"

    cli = subprocess.run(
        [
            sys.executable, str(ROOT / "scripts" / "chart_engine.py"), "--json",
            "--date", "1990-06-15", "--time", "08:30", "--tz", "8",
            "--lat", "25.0", "--lon", "121.5", "--gender", "女",
            "--target", "2025-01-01",
        ],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    assert cli.returncode == 0, cli.stderr
    # MCP text == CLI stdout minus exactly one trailing newline (shared serializer)
    assert cli.stdout.endswith("\n") and not cli.stdout.endswith("\n\n")
    assert result.content[0].text == cli.stdout[:-1]
    payload = json.loads(result.content[0].text)
    assert payload["ok"] is True and payload["schema_version"] == "1.2"


def test_invalid_input_is_error_and_session_survives():
    async def scenario():
        async with create_connected_server_and_client_session(
            mcp_server.server._mcp_server
        ) as session:
            bad = await session.call_tool("compute_chart", {**GOOD_INPUT, "date": "1899-12-31"})
            good = await session.call_tool("compute_chart", GOOD_INPUT)
            return bad, good

    bad, good = _run(scenario)
    assert bad.isError is True
    assert "date" in bad.content[0].text
    assert good.isError is False


def test_runtime_failure_is_error_not_crash(monkeypatch):
    def node_is_gone(_inp):
        raise RuntimeError("紫微斗數 sidecar failed — this engine requires Node.js >= 18")

    monkeypatch.setattr(chart_engine, "build_json", node_is_gone)

    async def scenario():
        async with create_connected_server_and_client_session(
            mcp_server.server._mcp_server
        ) as session:
            failed = await session.call_tool("compute_chart", GOOD_INPUT)
            return failed

    failed = _run(scenario)
    assert failed.isError is True
    assert "Node.js >= 18" in failed.content[0].text


def test_compute_path_makes_no_network_calls(monkeypatch):
    def deny(*_a, **_kw):
        raise AssertionError("network call attempted during MCP compute")

    # Patch the outbound primitives (NOT socket.socket — asyncio's socketpair
    # self-pipe would be killed and the guard would misfire on the event loop).
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)

    async def scenario():
        async with create_connected_server_and_client_session(
            mcp_server.server._mcp_server
        ) as session:
            return await session.call_tool("compute_chart", GOOD_INPUT)

    result = _run(scenario)
    assert result.isError is False


def test_missing_mcp_dependency_prints_install_hint(tmp_path):
    # simulate an environment without the mcp package: block its import
    code = (
        "import sys; sys.modules['mcp'] = None\n"
        f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
        "import mcp_server\n"
        "raise SystemExit(mcp_server.main())\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, encoding="utf-8", cwd=tmp_path,
    )
    assert proc.returncode == 1
    assert "pip install 'life-chart-engine[mcp]'" in proc.stderr
    assert "Traceback" not in proc.stderr
