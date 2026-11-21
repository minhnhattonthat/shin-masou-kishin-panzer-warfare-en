# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon in progress. Last build: none yet (2026-11-21).
- **Done:**
  - Step 0: repo set up; PCSX-Redux + SCPH-5500 in `tools/`, mkpsxiso 2.30, armips 0.11.0; original boots (`--smoke`
    ok), Start press works, Lua probe logs; pre-commit rejects a failing test; guard hook blocks `sed -i`.
  - Disc unpack/rebuild is byte-identical (phase 3 condition already holds by hand; make it a test in phase 3).
  - Recon so far in `docs/re/`: event scripts fully mapped (35 blocks, 7640 Shift-JIS strings, absolute RAM pointers
    in op 0x384/0x0001 commands, base 0x801C2518); exe strings (direct pointers, base 0x800A5800); BAT_OVER quotes
    located (pointer form not found yet); graphics survey started (T_TIM done).
  - Savestates (`work/states/`, gitignored, regenerate from the routes in this file): `title.sstate` (title menu),
    `event1_start.sstate` (first event), `battle_weapon_menu.sstate` (first battle, weapon menu).
- **Next (to finish phase 1):**
  1. Graphics survey: read `work/gfx/sheets/{TIM,BAT_TIM,GRA5}.BIN_*.png` (regenerate: `tools/tim.py` +
     `tools/montage.py`, see docs/re/graphics.md), list every Japanese element; find chapter-card and 攻撃技 sources;
     list MOV.STR movies with burned-in text.
  2. Font: find the dialogue/menu font (exe/TIM or BIOS Krom; hook the draw call) and whether ASCII renders.
  3. BAT_OVER quote access (read watch on a quote in RAM during battle) and the exe `lui/addiu` string refs.
  4. Free space: what follows the event slot in RAM (0x801C2518 + block size), exe/overlay padding.
- **Open bugs:** none.
- **Waiting on the user:** nothing.

Routes used: title = boot 3600 frames, Start; new game = from title `circle`, mash circle ~11000 frames (long FMV)
to event 1; battle = mash circle 40-frame period ~9000 more frames.
