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
| [scripts.md](scripts.md) | OVER.BIN event blocks, text pool format, message pointers | verified |
| [battle.md](battle.md) | BAT_OVER battle quotes, exe strings, overlay text | partly guessed |
| [graphics.md](graphics.md) | graphics-text survey (TIMs, FMV) | in progress |
| font | dialogue font source / BIOS Krom? ASCII support | not started (phase 1/5) |

Prior work: no earlier fan translation found (web search 2026-11-21). Game: Banpresto/Rakish, 1999-11-25, SRPG
based on the 1999 Cybuster TV anime; original cast (Keigo Ferdinand, Zeldona, Alma, Helena, Furcas…).
