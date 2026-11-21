"""Debug tool (tools/debug/): scene list shape, blank card, and the exe facts warp.lua relies on (docs/re/debug.md)."""
import csv
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
sys.path.insert(0, str(ROOT / "tools" / "debug"))
T_BASE = 0x800A5800


def test_scene_list():
    with open(ROOT / "tools" / "debug" / "scenes.tsv", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    assert rows[0] == ["name", "stage", "how", "wait", "frames", "keys", "note"]
    names = [r[0] for r in rows[1:]]
    assert len(names) == len(set(names))
    for r in rows[1:]:
        assert len(r) == 7, r
        assert r[2] in ("event", "card", "map", "battle", "title") or r[2].split(":")[0] in ("force", "card"), r
        assert 1 <= int(r[1]) <= 35 and int(r[3]) >= 0 and int(r[4]) > int(r[3])
    for s in range(1, 36):  # every stage's event, card and map
        assert {f"ev{s:02d}", f"card{s:02d}", f"map{s:02d}"} <= set(names)


def test_blank_card():
    import warp_all
    d = warp_all.blank_card()
    assert d[:2] == b"MC" and all(d[128 * i] == 0xA0 for i in range(1, 16))


@pytest.mark.skipif(not (TREE / "SLPS_023.19").exists(), reason="disc not unpacked")
def test_exe_facts():
    e = (TREE / "SLPS_023.19").read_bytes()
    w = lambda a: struct.unpack_from("<I", e, a - T_BASE)[0]  # noqa: E731
    assert w(0x80129DA8) == 0x3C1C8017 and w(0x80129DAC) == 0x279C75C0  # $gp = 0x801775C0
    assert w(0x8014BAC4 + 4 * 4) == 0x800F2104  # mode 4 = event init (loads the block by stage byte)
    tbl = struct.unpack_from("<36H", e, 0x801557E4 - T_BASE)  # event-block sectors, stage 1..35
    assert tbl[0] == 0 and tbl[35] == 0x1A0 and list(tbl) == sorted(tbl)
