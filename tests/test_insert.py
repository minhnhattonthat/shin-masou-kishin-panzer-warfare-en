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
    for n in FILES:
        shutil.copy(TREE / n, tmp_path / n)
    return tmp_path


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


def test_en_mode_without_english_changes_nothing(tree):
    changed = insert.insert(tree, ROOT / "script", "en")
    assert changed == {n: 0 for n in FILES}


def test_marker_every_pointer_reaches_its_marker(tree):
    insert.insert(tree, ROOT / "script", "marker")
    ovr = (tree / "OVER.BIN").read_bytes()
    n = 0
    for p in sorted((ROOT / "script" / "events").glob("*.json")):
        f = json.loads(p.read_text(encoding="utf-8"))
        s = int(f["block"][0], 16)
        for ln in f["lines"]:
            if ln["kind"] == "dummy":
                continue
            want = insert.marker_text(ln, ln["jp"])
            want = font.encode(ln["speaker"]) + b"\n" + font.encode(want) if "speaker" in ln else font.encode(want)
            for ptr in ln["ptrs"]:
                o = s + struct.unpack_from("<I", ovr, s + int(ptr, 16))[0] - over.BASE
                assert ovr[o:ovr.index(0, o)] == want, ln["id"]
                n += 1
    assert n > 7600


def test_qa_override_and_overflow(tree):
    insert.insert(tree, ROOT / "script", "en", {"exe_00D38": "Astral Canon"})
    e = (tree / "SLPS_023.19").read_bytes()
    assert e[0xD38:0xD38 + 13] == font.encode("Astral Canon") + b"\0"
    with pytest.raises(insert.Overflow):
        insert.insert(tree, ROOT / "script", "en", {"exe_00D38": "x" * 40})
