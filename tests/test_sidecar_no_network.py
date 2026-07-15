"""Static no-network assertion for the Node sidecar sources.

The Python in-process socket guard cannot observe a spawned Node child
process, so the sidecar's freedom from network primitives is proven
statically over both .cjs sources instead (documented boundary in AGENTS.md).
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR_SOURCES = (
    ROOT / "scripts" / "ziwei_iztro.cjs",
    ROOT / "vendor" / "iztro.cjs",
)

# every network-capable Node built-in, with and without the node: prefix,
# via require() or dynamic import()
_NET_MODULES = r"(?:https?|http2|net|tls|dgram|dns)"
NETWORK_PRIMITIVES = (
    rf"require\(\s*['\"](?:node:)?{_NET_MODULES}['\"]\s*\)",
    rf"import\(\s*['\"](?:node:)?{_NET_MODULES}['\"]\s*\)",
    r"\bfetch\s*\(",
    r"\bXMLHttpRequest\b",
    r"\bWebSocket\b",
)


def test_sidecar_sources_contain_no_network_primitives():
    problems = []
    for source in SIDECAR_SOURCES:
        text = source.read_text(encoding="utf-8", errors="replace")
        for pattern in NETWORK_PRIMITIVES:
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{source.name}:{line}: {match.group(0)!r}")
    assert not problems, "\n" + "\n".join(problems)
