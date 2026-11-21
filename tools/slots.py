"""Event-window glyph slots (docs/re/font.md §Glyph slots): every drawn glyph takes one sprite slot (600 slots at
*0x801B7184, 0x44 bytes each). The 3 event windows own fixed ranges (start 10 / 90 / 170, 80 slots each) and share
the shadow range from 300; a window frees only its 80 slots on close, so English with more than 80 glyphs left stray
glyphs on screen. New layout: 140 slots per window at 10 / 150 / 290, shadows at 430-569. Slots 250-599 had no
other user in ev01/map05/battle05/intermission/status runs (tools/lua/slots.lua, 2026-11-22).

Each patch is an `addiu rX, zero, imm` in the exe whose immediate changes; patch() checks the original word first.
Library: patch(exe bytes) -> bytes. WINDOW_GLYPHS is the lint budget (non-space glyphs per message incl. speaker)."""
import struct

T_BASE = 0x800A5800
OLD = {"count": 0x50, "w0": 0x0A, "w1": 0x5A, "w2": 0xAA, "shadow": 0x12C}
NEW = {"count": 140, "w0": 10, "w1": 150, "w2": 290, "shadow": 430}  # 430+140 = 570 <= 600 slots
WINDOW_GLYPHS = NEW["count"]

# (RAM address, register, role); found by tools/lua/slots.lua + windows.lua and a scan around every free/draw call
SITES = [
    (0x800F6C5C, 6, "w0"), (0x800F6C60, 7, "count"), (0x800F6CA8, 6, "w1"), (0x800F6CAC, 7, "count"),
    (0x800F6CD4, 6, "w2"), (0x800F6CD8, 7, "count"),  # window create 0x800F1384(idx, ?, start, count, ...)
    (0x800F1464, 4, "shadow"), (0x800F1654, 4, "shadow"), (0x800F18B0, 4, "shadow"),  # frees (start, count)
    (0x800F1960, 4, "shadow"),  # draw shadow pass
    (0x800F6FD0, 4, "w0"), (0x800F6FD8, 4, "w1"), (0x800F6FDC, 4, "w2"), (0x800F6FE4, 5, "count"),
    (0x800F6FE8, 4, "shadow"), (0x800F6FF0, 5, "count"),
    (0x800F711C, 4, "w0"), (0x800F7124, 5, "count"), (0x800F7128, 4, "shadow"), (0x800F7130, 5, "count"),
    (0x800F7164, 4, "w1"), (0x800F716C, 5, "count"), (0x800F7170, 4, "shadow"), (0x800F7178, 5, "count"),
    (0x800F71AC, 4, "w2"), (0x800F71B4, 5, "count"), (0x800F71B8, 4, "shadow"), (0x800F71C0, 5, "count"),
    (0x800F7EB0, 4, "w0"), (0x800F7EB8, 4, "w1"), (0x800F7EBC, 4, "w2"), (0x800F7EC4, 5, "count"),
    (0x800F7EC8, 4, "shadow"), (0x800F7ED0, 5, "count"),
    (0x8011526C, 4, "w2"), (0x80115274, 4, "w0"), (0x8011527C, 4, "w1"), (0x80115280, 4, "w2"),
    (0x80115288, 5, "count"), (0x8011528C, 4, "shadow"), (0x80115294, 5, "count"),
]


def _addiu(rt, imm):
    return 0x24000000 | rt << 16 | imm


def patch(exe):
    e = bytearray(exe)
    for a, rt, role in SITES:
        o = a - T_BASE
        old = struct.unpack_from("<I", e, o)[0]
        assert old == _addiu(rt, OLD[role]), "slot patch %08X: found %08X" % (a, old)
        struct.pack_into("<I", e, o, _addiu(rt, NEW[role]))
    return bytes(e)
