#!/usr/bin/env python3
"""MCP surface for life-chart-engine.

A thin stdio wrapper over ``build_json()`` — no calculation logic lives here.
The ``compute_chart`` tool mirrors the HTTP ``/chart`` body fields; its result
is a single text content equal to the shared envelope serializer's output
(CLI ``--json`` stdout minus the trailing newline).

Requires the ``mcp`` optional extra: ``pip install 'life-chart-engine[mcp]'``.
"""

import sys

try:
    from . import chart_engine
    from .validation import DEFAULT_NAME, DEFAULT_TARGET, validate_input
except ImportError:
    import chart_engine
    from validation import DEFAULT_NAME, DEFAULT_TARGET, validate_input

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # covers ModuleNotFoundError (mcp extra not installed)
    FastMCP = None

INSTALL_HINT = (
    "life-chart-mcp requires the MCP optional dependency.\n"
    "Install it with: pip install 'life-chart-engine[mcp]'\n"
)


def _build_server():
    server = FastMCP(
        "life-chart-engine",
        instructions=(
            "Deterministic offline chart computation: Western natal + Human "
            "Design + 紫微斗數 from one birth record. Same input → same output."
        ),
    )

    @server.tool()
    def compute_chart(
        date: str,
        time: str,
        tz: float,
        lat: float,
        lon: float,
        gender: str,
        name: str = DEFAULT_NAME,
        target: str = DEFAULT_TARGET,
        ziwei_day_divide: str = "forward",
    ) -> str:
        """Compute all three chart systems for one birth record.

        date/time are local birth-clock values ("YYYY-M-D" / "H:M", zero-padding
        optional, year within 1900–2100); tz is the DST-aware UTC offset at
        birth; gender is 男 or 女. Returns the engine's full JSON envelope
        (schema_version 1.2) as text.
        """
        # ValueError from validate_input → FastMCP surfaces it as isError=true
        # with the message (field-named), and the session survives.
        inp = validate_input({
            "date": date, "time": time, "tz": tz, "lat": lat, "lon": lon,
            "gender": gender, "name": name, "target": target,
            "ziwei_day_divide": ziwei_day_divide,
        })
        envelope = chart_engine.build_json(inp)
        return chart_engine.to_json_text(envelope)

    return server


server = _build_server() if FastMCP is not None else None


def main() -> int:
    if FastMCP is None or server is None:
        sys.stderr.write(INSTALL_HINT)
        return 1
    server.run()  # stdio transport
    return 0


if __name__ == "__main__":
    sys.exit(main())
