"""Phase 5: insertion (tools/insert.py) and the VWF tables (tools/font.py).
Skipped on a clone without the unpacked disc (work/disc/tree)."""
import json
import shutil
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
sys.path.insert(0, str(ROOT / "tools"))
pytestmark = pytest.mark.skipif(not (TREE / "SLPS_023.19").exists(), reason="disc not unpacked")

import font  # noqa: E402
import insert  # noqa: E402
import over  # noqa: E402

FILES = ("OVER.BIN", "BAT_OVER.BIN", "SLPS_023.19")


@pytest.fixture
def tree(tmp_path):
    for n in FILES + ("T_TIM.BIN",):
        shutil.copy(TREE / n, tmp_path / n)
    return tmp_path


def event_blocks(tree):
    """Event blocks as the loader reads them: [t[i], t[i+1]) sectors of OVER.BIN from the exe's sector list."""
    ovr, exe = (tree / "OVER.BIN").read_bytes(), (tree / "SLPS_023.19").read_bytes()
    t = struct.unpack_from("<36H", exe, insert.TABLE)
    return [ovr[a * 0x800:b * 0x800] for a, b in zip(t, t[1:])]


def test_encode():
    assert font.encode("Hi, bob!") == b"H\xa9, \xa2\xaf\xa2!"
    assert font.encode("{h}A\nB[0D]") == b"hA\nB\x0d"
    assert font.encode("「A」") == "「".encode("cp932") + b"A" + "」".encode("cp932")
    for ch in font.CONTROL + "\0\n":
        assert font.byte_of(ch) is None or font.byte_of(ch) >= 0xA0


def test_tables():
    exe = (TREE / "SLPS_023.19").read_bytes()
    code, width = font.tables((TREE / "BAT_TIM.BIN").read_bytes(), font.TIM_OFFS["BAT_TIM.BIN"], exe)
    for c in range(0x20, 0x7F):
        ch = chr(c)
        if "a" <= ch <= "z":
            continue
        b = font.byte_of(ch)
        assert b is not None and 0 < width[b] <= 12, ch
        assert code[b] or ch == " ", ch
    font.tables_asm(code, width)  # asserts control bytes keep width 0
    # shifting the cells left keeps the measured widths
    patched = font.patch_tim((TREE / "BAT_TIM.BIN").read_bytes(), font.TIM_OFFS["BAT_TIM.BIN"], exe)
    assert font.tables(patched, font.TIM_OFFS["BAT_TIM.BIN"], exe) == (code, width)


def test_en_mode_without_english_changes_only_the_layout(tree):
    orig = [(TREE / "OVER.BIN").read_bytes()[s:e] for s, e in over.blocks((TREE / "OVER.BIN").read_bytes())]
    changed = insert.insert(tree, ROOT / "script", "en")
    assert changed["BAT_OVER.BIN"] == 0
    assert event_blocks(tree) == orig  # moved to the end of OVER.BIN, same bytes
    ovr = (tree / "OVER.BIN").read_bytes()
    assert not any(ovr[:over.EVENT_END_SECTOR * 0x800])  # old copies zeroed
    t_tim = (TREE / "T_TIM.BIN").read_bytes()
    assert ovr[insert.OVER_SECTORS * 0x800:insert.OVER_READ_END * 0x800] == t_tim[:0x1800]
    assert ovr[over.EVENT_END_SECTOR * 0x800:insert.OVER_SECTORS * 0x800] == \
        (TREE / "OVER.BIN").read_bytes()[over.EVENT_END_SECTOR * 0x800:]
    exe, e0 = (tree / "SLPS_023.19").read_bytes(), (TREE / "SLPS_023.19").read_bytes()
    assert [i for i in range(len(e0)) if exe[i] != e0[i]] and \
        all(insert.TABLE <= i < insert.TABLE + 72 for i in range(len(e0)) if exe[i] != e0[i])


def test_marker_every_pointer_reaches_its_marker(tree):
    insert.insert(tree, ROOT / "script", "marker")
    blocks = event_blocks(tree)
    n = 0
    for k, p in enumerate(sorted((ROOT / "script" / "events").glob("*.json"))):
        f, blk = json.loads(p.read_text(encoding="utf-8")), blocks[k]
        assert len(blk) <= insert.MAX_BLOCK
        for ln in f["lines"]:
            if ln["kind"] == "dummy":
                continue
            want = insert.marker_text(ln, ln["jp"])
            want = font.encode(ln["speaker"]) + b"\n" + font.encode(want) if "speaker" in ln else font.encode(want)
            for ptr in ln["ptrs"]:
                o = struct.unpack_from("<I", blk, int(ptr, 16))[0] - over.BASE
                assert blk[o:blk.index(0, o)] == want, ln["id"]
                n += 1
    assert n > 7600


def test_speaker_names(tmp_path):
    g = tmp_path / "g.md"
    g.write_text("## Characters\n| JP | EN | max |\n|---|---|---|\n| ケイゴ | Keigo | |\n\n## Places\n| JP | EN |\n"
                 "| 王都 | Capital |\n", encoding="utf-8")
    assert insert.speaker_names(g) == {"ケイゴ": "Keigo"}


def test_pool_overflow_spills_past_the_block_end(tree):
    f = json.loads((ROOT / "script/events/ev000.json").read_text(encoding="utf-8"))
    big = {ln["id"]: "W" * 150 for ln in f["lines"] if "speaker" in ln}  # far more than the pool holds
    insert.insert(tree, ROOT / "script", "en", big)
    blk = event_blocks(tree)[0]
    assert 0x8000 < len(blk) <= insert.MAX_BLOCK
    for ln in f["lines"]:
        if ln["id"] in big:
            o = struct.unpack_from("<I", blk, int(ln["ptrs"][0], 16))[0] - over.BASE
            spk = insert.speaker_names().get(ln["speaker"], ln["speaker"])
            assert blk[o:blk.index(0, o)] == font.encode(spk) + b"\n" + b"W" * 150
    with pytest.raises(insert.Overflow):
        insert.insert(tree, ROOT / "script", "en", {k: "W" * 400 for k in big})


def test_qa_override_and_overflow(tree):
    insert.insert(tree, ROOT / "script", "en", {"exe_00D38": "Astral Canon"})
    e = (tree / "SLPS_023.19").read_bytes()
    assert e[0xD38:0xD38 + 13] == font.encode("Astral Canon") + b"\0"
    with pytest.raises(insert.Overflow):
        insert.insert(tree, ROOT / "script", "en", {"exe_00D38": "x" * 40})
