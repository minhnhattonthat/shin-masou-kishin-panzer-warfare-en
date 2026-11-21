"""Phase 4: script/ roundtrips to the original bytes, matches a fresh extraction, and covers all text.
Skipped on a clone without the unpacked disc (work/disc/tree)."""
import json
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
SCRIPT = ROOT / "script"
sys.path.insert(0, str(ROOT / "tools"))
pytestmark = pytest.mark.skipif(not (TREE / "SLPS_023.19").exists(), reason="disc not unpacked")

import extract  # noqa: E402
import over  # noqa: E402
import sjis_scan  # noqa: E402
from sjis import encode  # noqa: E402

# SJIS-looking runs that are not text (offset ranges per file, with the reason)
WAIVED = {
    "SLPS_023.19": [(0x15AA8, 0x162E0, "MIPS code bytes (獏ｄ獏ヴ)"),
                    (0xCAB80, 0xCB040, "u16 tables of SJIS codes, step ~15 (font row starts)"),
                    (0xCF390, 0xCFE60, "data table of mirrored kanji pairs")],
    "OVER.BIN": [(0xD0EB4, 0xD0EBA, "overlay code bytes"), (0xD1FAE, 0xD1FB4, "overlay code bytes")],
    "BAT_OVER.BIN": [],
}


@pytest.fixture(scope="module")
def files():
    return {p.relative_to(SCRIPT).as_posix(): json.loads(p.read_text(encoding="utf-8")) for p in SCRIPT.rglob("*.json")}


@pytest.fixture(scope="module")
def data():
    return {n: (TREE / n).read_bytes() for n in WAIVED}


def located(rel, obj, data):
    """(file name, offset, original bytes, line text) for every line."""
    for ln in obj["lines"]:
        i = ln["id"]
        if rel.startswith("events/"):
            name, off = "OVER.BIN", int(obj["block"][0], 16) + int(i.split("_")[1], 16)
            text = ln["speaker"] + "\n" + ln["jp"] if "speaker" in ln else ln["jp"]
        elif i.startswith("bq"):
            _, sec, o = i.split("_")
            name, off, text = "BAT_OVER.BIN", int(sec, 16) * 0x800 + int(o, 16), ln["jp"]
        else:
            name, off, text = ("SLPS_023.19" if i.startswith("exe") else "OVER.BIN"), int(i.split("_")[1], 16), ln["jp"]
        d = data[name]
        yield name, off, d[off:d.index(0, off)], text


def test_files_match_fresh_extraction(files):
    fresh = extract.extract(TREE)
    assert sorted(files) == sorted(fresh), "run tools/extract.py (missing or extra files)"
    for rel, obj in fresh.items():
        got = files[rel]["lines"]
        assert [ln["id"] for ln in got] == [ln["id"] for ln in obj["lines"]], rel
        for a, b in zip(got, obj["lines"]):
            assert {k: v for k, v in a.items() if k not in extract.KEEP} == \
                   {k: v for k, v in b.items() if k not in extract.KEEP}, a["id"]


def test_roundtrip(files, data):
    n = 0
    for rel, obj in files.items():
        for name, off, raw, text in located(rel, obj, data):
            assert encode(text) == raw, (rel, hex(off))
            n += 1
    assert n == 7640 + 71 + 2 * 2061 + 899 + 37  # exe: 900 minus extract.NOT_TEXT


def test_event_pools_fully_covered(data):
    d = data["OVER.BIN"]
    for s, e in over.blocks(d):
        tg, pools = extract.event_strings(d, s, e)
        covered = set()
        for o in tg:
            covered.update(range(o, d.index(0, o)))
        for lo, hi in pools:
            assert all(d[x] == 0 for x in range(lo, hi) if x not in covered), "unexplained bytes in pool %X" % lo
        # every message/choice command pointing into the block lands on an extracted string start
        for i in range(s, e - 16, 4):
            op, p = struct.unpack_from("<I", d, i)[0], struct.unpack_from("<I", d, i + 8)[0]
            if op & 0xFFFF in (over.MSG_OP, 1) and over.BASE <= p < over.BASE + (e - s):
                assert s + p - over.BASE in tg, "cmd %X -> %X is not an extracted string" % (i, p)


def test_battle_blocks_have_no_unexplained_bytes(data):
    import batquote
    e, d = data["SLPS_023.19"], data["BAT_OVER.BIN"]
    for _, base, a, b in batquote.blocks(e):
        blk = d[a * 0x800:b * 0x800]
        _, strings, recs = batquote.parse(blk, base)
        cov = {x for o, s in strings for x in range(o, o + len(s))}
        assert all(blk[x] == 0 for x in range(4, min(recs)) if x not in cov), "sector %X" % a


def test_merge_keeps_english_and_refuses_to_drop_it():
    old = {"lines": [{"id": "a", "jp": "x", "en": "Hi", "notes": "n"}, {"id": "b", "jp": "y", "en": ""}]}
    new = extract.merge({"lines": [{"id": "a", "jp": "z", "en": ""}]}, old)
    assert new["lines"] == [{"id": "a", "jp": "z", "en": "Hi", "notes": "n"}]
    with pytest.raises(SystemExit):
        extract.merge({"lines": []}, old)


def test_no_overlaps(files, data):
    spans = {}
    for rel, obj in files.items():
        for name, off, raw, _ in located(rel, obj, data):
            spans.setdefault(name, []).append((off, off + len(raw) + 1))
    for name, v in spans.items():
        v.sort()
        assert all(a[1] <= b[0] for a, b in zip(v, v[1:])), name


def test_every_sjis_run_extracted_or_waived(files, data):
    cov = {n: set() for n in data}
    for rel, obj in files.items():
        for name, off, raw, _ in located(rel, obj, data):
            cov[name].update(range(off, off + len(raw)))
    left = []
    for name, d in data.items():
        runs = list(sjis_scan.runs(d, 3)) + list(sjis_scan.runs(d, 4, kana=False))
        for o, n, s in runs:
            if o in cov[name] or any(lo <= o < hi for lo, hi, _ in WAIVED[name]) or set(s) <= set("珥"):
                continue  # 珥 = 0xE0E0 fill bytes
            left.append((name, hex(o), s))
    assert not left, left
