"""tools/gfx.py: every redraw row fits, covers its original text, and changes nothing outside its rect."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
pytestmark = pytest.mark.skipif(not (ROOT / "work/disc/tree/GRA5.BIN").exists(), reason="disc not unpacked")

import gfx  # noqa: E402


def test_rows_check():
    assert gfx.check() == 0


def test_draw_stays_in_rect():
    px = [[0] * 40 for _ in range(20)]
    r = dict(x="4", y="4", w="30", h="12", text="Wide text that overflows", font="tiny5", ink="1", edge="outline:2",
             bg="0", align="center")
    gfx.draw(px, r)
    assert all(v == 0 for y, row in enumerate(px) for x, v in enumerate(row) if not (4 <= x < 34 and 4 <= y < 16))
    assert any(v == 1 for row in px for v in row)
