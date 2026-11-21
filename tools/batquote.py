"""BAT_OVER.BIN battle-quote blocks (docs/re/battle.md).
Usage: batquote.py [--tree work/disc/tree]  -> per-set counts and a pointer check (exit 1 on any unreached string).
Library: blocks(exe) -> [(set, base, start_sector, end_sector)]; parse(blk, base) -> (id, [(off, bytes)], [rec_off])."""
import argparse
import struct
import sys

SETS = (("A", 0xAFD20, 0x801D79EC), ("B", 0xAFE66, 0x801DA5A0))  # exe offset of u16 sector list, RAM load base


def sector_list(e, o):
    v = []
    while (x := struct.unpack_from("<H", e, o)[0]) != 0xFFFF:
        v.append(x)
        o += 2
    return v


def blocks(e):
    return [(name, base, a, b) for name, off, base in SETS for a, b in zip(sector_list(e, off), sector_list(e, off)[1:])]


def parse(blk, base):
    """Records are 12 bytes (kind, ptr, quote id) whose ptr points into this block; strings precede them."""
    recs = [i - 4 for i in range(4, len(blk) - 8, 4)
            if base <= struct.unpack_from("<I", blk, i)[0] < base + len(blk) and struct.unpack_from("<I", blk, i + 4)[0] < 0x10000]
    first, strings, o = (min(recs) if recs else len(blk)), [], 4
    while o < first and blk[o]:
        e = blk.index(0, o)
        strings.append((o, blk[o:e]))
        o = (e + 4) & ~3
    return struct.unpack_from("<I", blk, 0)[0], strings, recs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default="work/disc/tree")
    a = ap.parse_args()
    e = open(f"{a.tree}/SLPS_023.19", "rb").read()
    d = open(f"{a.tree}/BAT_OVER.BIN", "rb").read()
    bad = 0
    for name, _, base in SETS:
        nb = ns = nr = odd = un = 0
        for s, b_, x, y in blocks(e):
            if s != name:
                continue
            blk = d[x * 0x800:y * 0x800]
            _, strings, recs = parse(blk, base)
            tgt = {struct.unpack_from("<I", blk, r + 4)[0] - base for r in recs}
            nb, ns, nr = nb + 1, ns + len(strings), nr + len(recs)
            odd += sum(1 for t in tgt if not (blk[t - 1] == 0 and blk[t]))
            un += sum(1 for o, _ in strings if o not in tgt)
        print(f"set {name} base {base:08X}: blocks {nb} strings {ns} records {nr} odd targets {odd} unreached {un}")
        bad += un
    sys.exit(1 if bad else 0)
