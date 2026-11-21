"""Recon: guess the RAM load base of a file region from its string pointers.
Usage: ptrbase.py FILE LO HI [--span 0x40000]
Collects Shift-JIS string starts in [LO, HI) (byte after a 00) and all aligned u32 values 0x80010000-0x80200000 in the
file; prints the bases (value - string offset) shared by the most pointers."""
import argparse
import collections
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sjis_scan import runs  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("lo", type=lambda x: int(x, 0))
ap.add_argument("hi", type=lambda x: int(x, 0))
a = ap.parse_args()
d = open(a.file, "rb").read()
starts = {a.lo + o for o, ln, s in runs(d[a.lo:a.hi], 2) if a.lo + o == 0 or d[a.lo + o - 1] == 0}
vals = collections.Counter(struct.unpack_from("<I", d, i)[0] for i in range(0, len(d) - 3, 4))
c = collections.Counter()
for v, n in vals.items():
    if 0x80010000 <= v < 0x80200000:
        for s in starts:
            b = v - s
            if 0x80000000 <= b < 0x80200000:
                c[b] += 1
print(len(starts), "string starts")
for b, n in c.most_common(5):
    print(f"base {b:08X}: {n} strings pointed to")
