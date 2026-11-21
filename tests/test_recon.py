"""Recon facts that later phases build on (docs/re/). Skipped on a clone without the unpacked disc."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
sys.path.insert(0, str(ROOT / "tools"))
pytestmark = pytest.mark.skipif(not (TREE / "SLPS_023.19").exists(), reason="disc not unpacked")


def test_battle_quote_pointers_reach_every_string():
    import batquote
    e, d = (TREE / "SLPS_023.19").read_bytes(), (TREE / "BAT_OVER.BIN").read_bytes()
    n = 0
    for _, base, a, b in batquote.blocks(e):
        blk = d[a * 0x800:b * 0x800]
        _, strings, recs = batquote.parse(blk, base)
        tgt = {struct.unpack_from("<I", blk, r + 4)[0] - base for r in recs}
        assert all(o in tgt for o, _ in strings), f"sector {a:X}"
        n += len(strings)
    assert n == 2 * 2061


def test_glyph_row_table_covers_jis_level1():
    e = (TREE / "SLPS_023.19").read_bytes()
    o = 0x8015711C - 0x800A5800
    rows = [struct.unpack_from("<HxBH", e, o + 6 * k) for k in range(164)]
    assert rows[0] == (0x8140, 0, 0) and rows[-1][0] == 0x986A
    assert all(a[0] < b[0] for a, b in zip(rows, rows[1:]))
