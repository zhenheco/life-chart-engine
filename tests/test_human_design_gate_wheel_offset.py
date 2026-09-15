from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from chart_engine import SEQ, gate_line  # noqa: E402

# Published Human Design mandala boundaries (barneyandflow.com/gate-zodiac-degrees;
# Scribd "Gates and Zodiac Placements"):
#   Gate 25 = 28deg15'00" Pisces (358.25 deg) .. 03deg52'30" Aries
#   Gate 17 = 03deg52'30" (3.875 deg) .. 09deg30' Aries
#   Gate 41 starts 02deg00' Aquarius (302.0 deg)
# These pin the wheel's absolute rotation, independent of the OFFSET constant's
# own value, so a future re-derivation of OFFSET is still checked against the
# real mandala instead of against itself.


def test_gate_25_starts_at_358_25_degrees():
    assert gate_line(358.25) == (25, 1)


def test_last_line_before_gate_25_is_the_preceding_wheel_gate():
    preceding_gate = SEQ[-1]  # wheel is circular; SEQ[-1] is gate 36
    assert gate_line(358.24) == (preceding_gate, 6)


def test_gate_17_starts_at_3_875_degrees():
    assert gate_line(3.875) == (17, 1)


def test_gate_41_starts_at_302_degrees():
    assert gate_line(302.0) == (41, 1)


def test_just_below_302_degrees_is_previous_gate_line_6():
    previous_gate = SEQ[SEQ.index(41) - 1]  # gate 60
    assert gate_line(301.999) == (previous_gate, 6)


def test_wheel_wraps_around_0_degrees_consistently():
    # -0.1 deg and 359.9 deg are the same ecliptic longitude; the wheel lookup
    # must agree across the 360/0 modulo boundary.
    assert gate_line(-0.1) == gate_line(359.9) == (25, 2)
