"""Phase-7 write check: every byte the build changed in SLPS_023.19, OVER.BIN, BAT_OVER.BIN and the two font files
lies in a range the build means to touch (tools/romdiff.py against the original), every other disc file is
unchanged, and with --writes (build.py's per-stage write logs) no stage overwrote another's bytes.

    python -X utf8 tools/writes_check.py [--tree build/disc/tree] [--orig work/disc/tree] [--writes build/writes]
Exit 0 when all pass. Ranges: insert.py (JP string slots / fixed-field `max`, pointer words, lui words + their
low halves, sector lists, quote slot words and record tables, EXE_FREE, appended blocks), asm/vwf.asm (hooks + VWF
run), tools/slots.py sites, font.TIM_OFFS (first font TIM)."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batquote  # noqa: E402
import font  # noqa: E402
import fmv  # noqa: E402
import gfx  # noqa: E402
import insert  # noqa: E402
import over  # noqa: E402
import slots  # noqa: E402

B = insert.EXE_BASE
FONT_TIM = 0x8800  # first font TIM (symbols, digits, Latin, kana) before the kanji TIM, docs/re/font.md


def exe_ranges(orig):
    r = [(insert.TABLE, insert.TABLE + 72), (insert.EXE_FREE[0] - B, insert.EXE_FREE[1] - B),
         (0x8016D740 - B, 0x8016DA60 - B),  # asm/vwf.asm code + tables
         (0x8010365C - B, 0x80103664 - B), (0x801030F4 - B, 0x80103114 - B),  # asm/vwf.asm hooks
         (insert.SHORT_FREE[0] - B, insert.SHORT_FREE[1] - B),  # pilot_short + its jal sites
         (0x800C6BFC - B, 0x800C6C00 - B), (0x800C6C2C - B, 0x800C6C30 - B)]
    r += [(a - B, a - B + 4) for a in (0x800E2E28, 0x800E2E64, 0x800E2E8C)]  # map unit box Lv. x (asm/vwf.asm)
    r += [(a - B, a - B + 4) for a in (0x800DD16C, 0x800DD304, 0x800DD4D8, 0x800DD234, 0x800DD3CC, 0x800DD530)]  # spirit grid cost x (D19)
    r += [(o, o + 2 * 66) for _, o, _ in batquote.SETS]
    r += [(w, w + 4) for w, _, _ in insert.BQ.values()] + [(t, t + 12 * 65) for _, _, t in insert.BQ.values()]
    r += [(a - B, a - B + 4) for a, _, _ in slots.SITES] + [(a - B, a - B + 4) for a, _, _ in slots.WORDS]
    for ln in json.loads((ROOT / "script/exe.json").read_text(encoding="utf-8"))["lines"]:
        o = int(ln["id"][4:], 16)
        movable = "region" not in ln and bool(ln.get("ptrs") or ln.get("lui"))
        # a movable string gets only its JP slot (the zeros `max` counts past it may be variables); a fixed field `max`
        r.append((o, (orig.index(0, o) + 4) & ~3 if movable else o + ln["max"] + 1))
        r += [(int(p, 16), int(p, 16) + 4) for p in ln.get("ptrs", [])]
        for p in ln.get("lui", []):  # the lui word and its low-half users
            r += [(q, q + 4) for q in [int(p, 16)] + insert.lo_users(orig, int(p, 16))]
    return r


def over_ranges(orig):
    r = [(0, over.EVENT_END_SECTOR * 0x800), (len(orig), 1 << 30)]  # old event blocks zeroed; blocks appended
    for ln in json.loads((ROOT / "script/overlay.json").read_text(encoding="utf-8"))["lines"]:
        o = int(ln["id"][3:], 16)
        r.append((o, o + ln["max"] + 1))
    return r


def _romdiff(name, args):
    p = subprocess.run([sys.executable, "-X", "utf8", ROOT / "tools/romdiff.py", *args], capture_output=True, text=True)
    print(name, "ok" if p.returncode == 0 else "FAIL", (p.stdout + p.stderr).strip()[-800:])
    return p.returncode


def run(name, orig_dir, tree, ranges, writes=None):
    """Range check; with a write log also romdiff --writes (wrong original bytes, a write overwritten by a later
    stage, overlapping writes), ranges then limited to the appended tail."""
    merged = []
    for a, b in sorted(ranges):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    files = [orig_dir / name, tree / name]
    bad = _romdiff(name, files + ["%X-%X" % (a, b - 1) for a, b in merged])
    if writes and (writes / (name + ".log")).exists():
        size = (orig_dir / name).stat().st_size
        bad |= _romdiff(name + " writes", files + ["%X-%X" % (size, (1 << 30) - 1), "--writes", writes / (name + ".log")])
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default=ROOT / "build/disc/tree", type=Path)
    ap.add_argument("--orig", default=ROOT / "work/disc/tree", type=Path)
    ap.add_argument("--writes", type=Path, help="dir of build write logs NAME.log (build.py writes build/writes/)")
    a = ap.parse_args()
    rd = lambda n: (a.orig / n).read_bytes()  # noqa: E731
    bad = run("SLPS_023.19", a.orig, a.tree, exe_ranges(rd("SLPS_023.19")), a.writes)
    bad |= run("OVER.BIN", a.orig, a.tree, over_ranges(rd("OVER.BIN")), a.writes)
    bad |= run("BAT_OVER.BIN", a.orig, a.tree, [(len(rd("BAT_OVER.BIN")), 1 << 30)], a.writes)  # quotes appended
    g = gfx.ranges(a.orig)  # graphics-text redraws: the pixel block of every copy of a redrawn TIM
    for n in sorted(set(font.TIM_OFFS) | set(g)):  # VWF glyph cells: inside the first font TIM only
        offs = [o for m, o in [*font.TIM_OFFS.items(), *font.TIM_COPIES] if m == n]
        bad |= run(n, a.orig, a.tree, [(o, o + FONT_TIM) for o in offs] + g.get(n, []), a.writes)
    for n, r in fmv.ranges(a.orig).items():  # FMV subtitles: the sectors of every captioned frame
        bad |= run(n, a.orig, a.tree, r, a.writes)
    checked = {"SLPS_023.19", "OVER.BIN", "BAT_OVER.BIN", *font.TIM_OFFS, *g, "MOV.STR"}
    for p in sorted(a.orig.rglob("*")):
        rel = p.relative_to(a.orig).as_posix()
        if p.is_file() and rel not in checked and p.read_bytes() != (a.tree / rel).read_bytes():
            print(rel, "FAIL: changed, but the build has no writer for it")
            bad = 1
    # every copy of the font must carry the VWF cells: a 64-byte run the patch changes, searched in every built file
    o_font = rd("BAT_TIM.BIN")[font.TIM_OFFS["BAT_TIM.BIN"]:][:FONT_TIM]
    b_font = (a.tree / "BAT_TIM.BIN").read_bytes()[font.TIM_OFFS["BAT_TIM.BIN"]:][:FONT_TIM]
    k = next(i for i in range(0x1000, FONT_TIM, 0x40) if o_font[i:i + 0x40] != b_font[i:i + 0x40])
    for p in sorted(a.tree.rglob("*")):
        if p.is_file() and o_font[k:k + 0x40] in p.read_bytes():
            print(p.relative_to(a.tree).as_posix(), "FAIL: holds an unpatched copy of the font TIM (font.TIM_COPIES)")
            bad = 1
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
