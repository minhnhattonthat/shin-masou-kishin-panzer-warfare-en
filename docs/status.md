# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (phase 1 recon done 2026-11-21). Last build: none yet.
- **Done:**
  - Step 0: repo set up; PCSX-Redux + SCPH-5500 in `tools/`, mkpsxiso 2.30, armips 0.11.0; original boots (`--smoke`
    ok), Start press works, Lua probe logs; pre-commit rejects a failing test; guard hook blocks `sed -i`.
  - Disc unpack/rebuild is byte-identical (phase 3 condition already holds by hand; make it a test in phase 3).
  - Phase 1 recon, all in `docs/re/` (index: README.md):
    - event scripts: 35 blocks, 7640 Shift-JIS strings, absolute pointers (op 0x384/0x0001), base 0x801C2518;
    - battle quotes: BAT_OVER 2 sets x 65 blocks, 2061 strings each, absolute pointers, bases 0x801D79EC /
      0x801DA5A0 (`tools/batquote.py`, test in `tests/test_recon.py`);
    - exe strings: u32 pointers, lui pairs, fixed-stride record fields (`tools/re.py`); 109 exe quotes 「…」 with
      no reference yet;
    - font: SJIS → 12x12 glyph via row table 0x8015711C (JIS level 1); single-byte ASCII is skipped, so English
      needs a renderer patch (phase 5); font TIMs BAT_TIM 0x480000/0x488800;
    - free-space candidates (guess, trap-test in phase 4/5): heap after the event block, exe zero runs;
    - graphics survey G1-G19 (static sweep of all TIMs + MOV.STR): chapter cards (37), status/spirit sheet,
      map command sheet, battle labels, intermission names, credits, mov01 advert subtitles.
  - Savestates (`work/states/`, gitignored, regenerate from the routes below): `title.sstate` (title menu),
    `event1_start.sstate` (first event), `battle_weapon_menu.sstate` (first battle, weapon menu: circle does
    nothing there, no target in range; a battle state must be taken next to an enemy).
- **Next (phase 2, debug tool):** `tools/debug/` with `scenes.tsv` + `warp.lua` reaching from a cold boot: each
  event block (35; warp by event id / RAM state), a battle with quotes (to trace the quote reader and BAT_OVER load),
  intermission menu, status/spirit menu, save screen, every chapter card (G8), game over, ending + credits (G18),
  option screen. Find the scenario/chapter variable first (RAM search between events, `tools/ramfind.py`).
  Memory-card save editor (`save.py`) if warps need it.
- **Open questions for later phases:** where the other font pages come from (font.md); the reader of the exe
  「…」 quotes; control letters `b h m r w z`; whether event blocks can grow (scripts.md §Free space); whether the
  dev loading card BAT_TIM 0x45A000 is ever shown.
- **Open bugs:** none.
- **Waiting on the user:** nothing.

Routes used: title = boot 3600 frames, Start; new game = from title `circle`, mash circle ~11000 frames (long FMV)
to event 1; battle = mash circle 40-frame period ~9000 more frames.
