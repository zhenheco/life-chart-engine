from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from chart_engine import GATE_CENTER  # noqa: E402


def test_gate_19_is_root_and_center_membership_counts_are_pinned():
    assert GATE_CENTER[19] == "根"
    assert sum(center == "情緒" for center in GATE_CENTER.values()) == 7
    assert sum(center == "根" for center in GATE_CENTER.values()) == 9
