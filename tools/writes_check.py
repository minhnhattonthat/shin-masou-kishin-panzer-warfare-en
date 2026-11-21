"""Phase-7 write check: every byte the build changed in SLPS_023.19, OVER.BIN and BAT_OVER.BIN lies in a range the
build means to touch (tools/romdiff.py on each file against the original).

    python -X utf8 tools/writes_check.py [--tree build/disc/tree] [--orig work/disc/tree]
Exit 0 when all three pass. Ranges: insert.py (string slots, pointer words, lui pairs, sector lists, quote slot
words and record tables, EXE_FREE, appended blocks), asm/vwf.asm (hooks + VWF run), tools/slots.py sites."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batquote  # noqa: E402
import insert  # noqa: E402
import over  # noqa: E402
import slots  # noqa: E402

B = insert.EXE_BASE


def exe_ranges(orig):
    r = [(insert.TABLE, insert.TABLE + 72), (insert.EXE_FREE[0] - B, insert.EXE_FREE[1] - B),
         (0x8016D740 - B, 0x8016DA60 - B),  # asm/vwf.asm code + tables
         (0x8010365C - B, 0x80103664 - B), (0x801030F4 - B, 0x80103114 - B)]  # asm/vwf.asm hooks
    r += [(o, o + 2 * 66) for _, o, _ in batquote.SETS]
    r += [(w, w + 4) for w, _, _ in insert.BQ.values()] + [(t, t + 12 * 65) for _, _, t in insert.BQ.values()]
    r += [(a - B, a - B + 4) for a, _, _ in slots.SITES]
    for ln in json.loads((ROOT / "script/exe.json").read_text(encoding="utf-8"))["lines"]:
        o = int(ln["id"][4:], 16)
        r.append((o, max(o + ln["max"] + 1, (orig.index(0, o) + 4) & ~3)))
        r += [(int(p, 16), int(p, 16) + 4) for p in ln.get("ptrs", [])]
        r += [(int(p, 16), int(p, 16) + 68) for p in ln.get("lui", [])]  # lui + its low half within 16 instructions
    return r


def over_ranges(orig):
    r = [(0, over.EVENT_END_SECTOR * 0x800), (len(orig), 1 << 30)]  # old event blocks zeroed; blocks appended
    for ln in json.loads((ROOT / "script/overlay.json").read_text(encoding="utf-8"))["lines"]:
        o = int(ln["id"][3:], 16)
        r.append((o, o + ln["max"] + 1))
    return r


def run(name, orig_dir, tree, ranges):
    merged = []
    for a, b in sorted(ranges):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    args = ["%X-%X" % (a, b - 1) for a, b in merged]
    p = subprocess.run([sys.executable, "-X", "utf8", ROOT / "tools/romdiff.py", orig_dir / name, tree / name, *args],
                       capture_output=True, text=True)
    print(name, "ok" if p.returncode == 0 else "FAIL", (p.stdout + p.stderr).strip()[-800:])
    return p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default=ROOT / "build/disc/tree", type=Path)
    ap.add_argument("--orig", default=ROOT / "work/disc/tree", type=Path)
    a = ap.parse_args()
    rd = lambda n: (a.orig / n).read_bytes()  # noqa: E731
    bad = run("SLPS_023.19", a.orig, a.tree, exe_ranges(rd("SLPS_023.19")))
    bad |= run("OVER.BIN", a.orig, a.tree, over_ranges(rd("OVER.BIN")))
    bad |= run("BAT_OVER.BIN", a.orig, a.tree, [(len(rd("BAT_OVER.BIN")), 1 << 30)])  # quote blocks appended
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
