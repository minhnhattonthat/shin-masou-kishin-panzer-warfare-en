# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| [disc.md](disc.md) | disc files, LBAs, exe load address, sector tables, identity rebuild | verified |
| [scripts.md](scripts.md) | OVER.BIN event blocks, text pool format, message pointers, free-space candidates | verified (free space: guess) |
| [battle.md](battle.md) | BAT_OVER battle quotes (2 sets, absolute pointers), exe strings (pointer / lui / record forms), overlay text | verified statically; runtime readers not traced |
| [graphics.md](graphics.md) | graphics-text survey G1-G19 (TIMs, VRAM, FMV) | static sweep done |
| [debug.md](debug.md) | stage byte, game-mode table, chapter-card buffer, intermission/memory-card flow (debug tool) | verified |
| [font.md](font.md) | renderer (SJIS → 12x12 glyph via row table), font TIMs, no half-width ASCII | verified; page streaming open |

Tools: `tools/over.py` (event blocks), `tools/batquote.py` (quote blocks + pointer check), `tools/re.py` (exe string
refs: u32 / lui pairs), `tools/tim.py` + `tools/montage.py` (TIM sweep), `tools/vram.py` (VRAM dump render),
`tools/str_movies.py` (FMV list/frames), `tools/sjis_scan.py`, `tools/ptrbase.py`, `tools/ramfind.py`.

Prior work: no earlier fan translation found (web search 2026-11-21). Game: Banpresto/Rakish, 1999-11-25, SRPG
based on the 1999 Cybuster TV anime; original cast (Keigo Ferdinand, Zeldona, Alma, Helena, Furcas…).
