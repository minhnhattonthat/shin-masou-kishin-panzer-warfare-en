"""Exe reference finder: which exe strings are reached by u32 pointers and which by lui+addiu/ori pairs.
Usage: re.py [--exe work/disc/tree/SLPS_023.19] [--lo 0x0 --hi 0x10000]
  -> counts, and every string start in [lo, hi) reached by neither (file offset, RAM, text).
Library: lui_targets(exe) -> {ram_addr: [pc, ...]} for lui rX,hi + addiu/ori/load/store rY,rX,lo within 16 instructions."""
import argparse
import struct
import sys

T_BASE = 0x800A5800  # RAM = T_BASE + file offset (docs/re/disc.md)


def lui_targets(e):
    out, n = {}, len(e) // 4
    w = struct.unpack_from("<%dI" % n, e)
    for i in range(0x200, n):  # skip header
        x = w[i]
        if x >> 26 != 0x0F:
            continue
        rt, hi = x >> 16 & 31, x & 0xFFFF
        for j in range(i + 1, min(i + 17, n)):
            y = w[j]
            op, rs = y >> 26, y >> 21 & 31
            if rs == rt and op in (0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B):
                lo = y & 0xFFFF
                t = (hi << 16) + (lo if op == 0x0D else (lo - 0x10000 if lo & 0x8000 else lo))
                out.setdefault(t & 0xFFFFFFFF, []).append(T_BASE + 4 * i)
            if y >> 26 == 0x0F and (y >> 16 & 31) == rt:
                break  # register reloaded
    return out


def string_starts(e, lo, hi):
    starts, i = [], lo
    while i < hi:
        if (0x81 <= e[i] <= 0x9F or 0xE0 <= e[i] <= 0xEF) and (i == 0 or e[i - 1] == 0) and i % 4 == 0:
            j = e.index(0, i)
            try:
                t = e[i:j].decode("cp932")
                # text, not code bytes that happen to decode: no control chars / half-width kana / PUA
                if len(t) >= 2 and all(c == "\n" or (c >= " " and not "｡" <= c <= "ﾟ"
                                                     and not "" <= c <= "") for c in t):
                    starts.append((i, t))
            except UnicodeDecodeError:
                pass
            i = (j + 4) & ~3
        else:
            i += 4
    return starts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="work/disc/tree/SLPS_023.19")
    ap.add_argument("--lo", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--hi", type=lambda s: int(s, 0), default=0x10000)
    a = ap.parse_args()
    e = open(a.exe, "rb").read()
    words = set(struct.unpack_from("<%dI" % (len(e) // 4), e))
    lui = lui_targets(e)
    ss = string_starts(e, max(a.lo, 0x800), a.hi)
    direct = [s for s in ss if T_BASE + s[0] in words]
    pair = [s for s in ss if T_BASE + s[0] not in words and T_BASE + s[0] in lui]
    none = [s for s in ss if T_BASE + s[0] not in words and T_BASE + s[0] not in lui]
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"strings {len(ss)}  u32 pointer {len(direct)}  lui pair {len(pair)}  none {len(none)}")
    for o, t in pair:
        print(f"  lui {o:06X} {T_BASE + o:08X} pc={','.join('%08X' % p for p in lui[T_BASE + o][:3])} {t[:30]!r}")
    for o, t in none:
        print(f"  none {o:06X} {T_BASE + o:08X} {t[:30]!r}")
