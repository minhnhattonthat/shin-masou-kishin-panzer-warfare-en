"""OVER.BIN event-script blocks (see docs/re/scripts.md).

Event blocks start on a sector whose header has bytes 1-3 = 0 and bytes 8-11 = 06 00 00 00; each loads at
RAM 0x801C2518. Message command: four u32 words (0x384, flags, RAM pointer to the string, 0).
Usage: over.py FILE  -> one line per block (sectors, message count, odd pointers)."""
import struct
import sys

BASE = 0x801C2518
EVENT_END_SECTOR = 0x1A0  # sectors from here on are code/data, not event scripts
MSG_OP = 0x384


def blocks(d):
    starts = [o for o in range(0, EVENT_END_SECTOR * 0x800, 0x800)
              if d[o + 8:o + 12] == b"\x06\0\0\0" and d[o + 1:o + 4] == b"\0\0\0"]
    return list(zip(starts, starts[1:] + [EVENT_END_SECTOR * 0x800]))


def is_text_start(d, o):
    return d[o - 1] == 0 and (0x81 <= d[o] <= 0x9F or 0xE0 <= d[o] <= 0xEF or d[o] == 0x0A)


def messages(d, s, e):
    """(cmd_offset, flags, ptr, string_offset) for each message command in block [s, e)."""
    out = []
    for i in range(s, e - 16, 4):
        op, flags, p, z = struct.unpack_from("<4I", d, i)
        if op & 0xFFFF == MSG_OP and BASE <= p < BASE + (e - s):
            out.append((i, flags, p, s + p - BASE))
    return out


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    for s, e in blocks(d):
        msgs = messages(d, s, e)
        odd = [m for m in msgs if not is_text_start(d, m[3])]
        print(f"block {s // 0x800:3X}-{e // 0x800:3X} msgs {len(msgs):4d} odd {len(odd)}")
        for i, fl, p, o in odd:
            print(f"   cmd {i:06X} flags {fl:X} ptr {p:08X} -> {o:06X}: {d[o - 4:o + 20].hex(' ')}")
