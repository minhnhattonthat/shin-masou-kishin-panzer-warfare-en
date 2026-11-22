"""Caller tree of the exe function holding an address: who reaches this code (jal or a function-pointer word).

    python -X utf8 tools/callers.py ADDR.. [--depth 4] [--exe work/disc/tree/SLPS_023.19]

ADDR: RAM address (hex), or an exe_XXXXX id / script offset (file offset; RAM = 0x800A5800 + offset).
A function starts after the last `jr ra` (+ delay slot) above ADDR, skipping leading nops: good enough for this
compiler's output (no tail calls into the middle of a function were seen). Prints one line per function:
start, how it is reached (jal sites or pointer words), indented by depth. Used to tell dev-screen-only text
(waive) from text a player can reach (force it on screen).
"""
import argparse
import struct
import sys

T_HDR = 0x800


def load(path):
    b = open(path, "rb").read()
    t_addr = struct.unpack_from("<I", b, 0x18)[0]
    return b[T_HDR:], t_addr


def words(code):
    return struct.unpack_from("<%dI" % (len(code) // 4), code)


def func_start(w, base, addr):
    i = (addr - base) // 4
    while i > 0:
        if w[i - 2] == 0x03E00008:  # jr ra, then its delay slot at i-1
            break
        i -= 1
    while w[i] == 0:
        i += 1
    return base + 4 * i


def reached_by(w, base, start):
    jal = 0x0C000000 | ((start >> 2) & 0x03FFFFFF)
    hits = []
    for i, x in enumerate(w):
        if x == jal:
            hits.append(("jal", base + 4 * i))
        elif x == start:
            hits.append(("ptr", base + 4 * i))
    return hits


def tree(w, base, addr, depth, seen, ind=0):
    s = func_start(w, base, addr)
    hits = reached_by(w, base, s)
    tag = " (seen)" if s in seen else ""
    print("%s%08X fn %08X  <- %s%s" % ("  " * ind, addr, s,
          ", ".join("%s %08X" % h for h in hits[:8]) or "nothing in exe", tag))
    if s in seen or depth == 0:
        return
    seen.add(s)
    for kind, site in hits[:8]:
        if kind == "jal":
            tree(w, base, site, depth - 1, seen, ind + 1)


def parse(a):
    a = a.replace("exe_", "")
    v = int(a, 16)
    return v + 0x800A5800 if v < 0x100000 else v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("addr", nargs="+")
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--exe", default="work/disc/tree/SLPS_023.19")
    a = ap.parse_args()
    code, base = load(a.exe)
    w = words(code)
    for x in a.addr:
        tree(w, base, parse(x), a.depth, set())
        print()


if __name__ == "__main__":
    sys.exit(main())
