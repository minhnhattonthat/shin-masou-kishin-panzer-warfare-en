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


# Battle animation (docs/re/windows.md §Battle HUD slots): the 4 name labels drew at fixed slot bases 0 / 8 / 0x10 /
# 0x18 (8 each), so a 9+ glyph English name ran into the next label's slots and lost glyphs; the quote box (base
# 0x20) freed only 0x20 slots, too few for English quotes (up to 58 glyphs). New: pilot labels 0 / 0x0C, mech labels
# 0x70 / 0x7C (12 each; 0x46-0x95 had no user in battle05, tools/lua/slotdump.lua), quote frees 0x48 (0x20-0x67).
HUD_GLYPHS, QUOTE_GLYPHS = 12, 0x48
SCROLL_GLYPHS = NEW["shadow"]  # 430
WORDS = [  # (RAM address, original word, new word)
    (0x801190FC, _addiu(4, 0x10), _addiu(4, 0x70)),  # top-right mech label slot base
    (0x80119100, 0x00802821, _addiu(5, 0x10)),       # its x was `move a1, a0` (= the old base 0x10)
    (0x80119130, _addiu(4, 0x18), _addiu(4, 0x7C)),  # top-left mech label
    (0x80119188, _addiu(4, 0x08), _addiu(4, 0x0C)),  # bottom-left pilot label (bottom-right stays at 0)
    # the intro's mech names (0x801167DC x=+48, 0x8011681C x=-144) shared those bases, and the HUD labels then took
    # their slots over: keep them paired, or the intro names stay on screen through the battle
    (0x801167DC, _addiu(4, 0x10), _addiu(4, 0x70)),
    (0x8011681C, _addiu(4, 0x18), _addiu(4, 0x7C)),
    (0x80119540, _addiu(5, 0x20), _addiu(5, QUOTE_GLYPHS)),  # quote free(0x20, count)
    (0x80119684, 0x00802821, _addiu(5, QUOTE_GLYPHS)),       # quote free(0x20, count): count was `move a1, a0`
    # chapter-intro scroll pages (0x80115998 first page, 0x80115A10 skip / next page) draw from slot 0 and freed
    # 0..199 only, so an English page (up to ~336 glyphs) left its last lines on screen (bug 4). No window is open
    # during the scroll (the JP's 200 already covered windows 0-1), so free everything below the shadows.
    (0x801159B8, _addiu(5, 0xC8), _addiu(5, SCROLL_GLYPHS)),
    (0x80115A54, _addiu(5, 0xC8), _addiu(5, SCROLL_GLYPHS)),
    (0x80115A90, _addiu(5, 0xC8), _addiu(5, SCROLL_GLYPHS)),
]


def patch(exe):
    e = bytearray(exe)
    for a, rt, role in SITES:
        o = a - T_BASE
        old = struct.unpack_from("<I", e, o)[0]
        assert old == _addiu(rt, OLD[role]), "slot patch %08X: found %08X" % (a, old)
        struct.pack_into("<I", e, o, _addiu(rt, NEW[role]))
    for a, old, new in WORDS:
        assert struct.unpack_from("<I", e, a - T_BASE)[0] == old, "slot patch %08X" % a
        struct.pack_into("<I", e, a - T_BASE, new)
    return bytes(e)
