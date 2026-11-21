# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 3. Identity build next (phase 2 debug tool done 2026-11-21). Last build: none yet.
- **Done:**
  - Step 0: repo set up; PCSX-Redux + SCPH-5500 in `tools/`, mkpsxiso 2.30, armips 0.11.0; original boots (`--smoke`
    ok), Start press works, Lua probe logs; pre-commit rejects a failing test; guard hook blocks `sed -i`.
  - Disc unpack/rebuild is byte-identical (phase 3 condition already holds by hand; make it a test in phase 3).
  - Phase 1 recon, all in `docs/re/` (index: README.md): event scripts (35 blocks, 7640 SJIS strings, absolute
    pointers), battle quotes (2 sets x 65 blocks), exe strings, font renderer (SJIS → 12x12, no ASCII: renderer patch
    in phase 5), free-space candidates, graphics survey G1-G19.
  - Phase 2 debug tool (`tools/debug/`, facts in `docs/re/debug.md`): `warp.lua` + `scenes.tsv` (124 scenes) +
    `warp_all.py` (cold boot each, `work/qa/warp/summary.tsv`, `--states` → `work/states/<scene>.sstate`). Pins the
    stage byte 0x801775E4 through New Game (events, chapter cards, battle maps of all 35 stages, a battle animation)
    and forces the game-mode word 0x801781F0 as an event starts (intermission + SAVE/LOAD/STATUS pages/NEXT, option,
    game over, staff roll); title/LOAD/CONTINUE by keys; branch cards 1 and 5 by TIM injection (`card:K`).
    Sweep result: see "Warp sweep" below. Game-written save fixture `tools/debug/saves/stage05_intermission.mcd`
    (title > LOAD lands in the intermission, no error).
- **Next (phase 3, identity build):** `build.py` that unpacks (dumpsxiso) and repacks (mkpsxiso) the disc with no
  edits, checked by a test that the rebuilt .bin sha1 equals `rom.sha1`; then phase 4 (extract to `script/`).
- **Open questions for later phases:** where the other font pages come from (font.md); the reader of the exe 「…」
  quotes; control letters `b h m r w z`; whether event blocks can grow (scripts.md §Free space); whether the dev
  loading card BAT_TIM 0x45A000 is ever shown; the chapter-card picker / branch flags for cards 1 and 5 (debug.md);
  unit record layout (GOD mode, stress values) and a save editor (`save.py`), deferred to phase 8 stress saves: the
  warps reach every stage without saves; a forced intermission has zeroed stats, so menu stress values need RAM
  writes or the editor then.
- **Open bugs:** none.
- **Waiting on the user:** nothing.

Warp sweep (original disc, 2026-11-21): `warp_all.py --states` 123/123 scenes reached from a cold boot, every
proof shot non-blank and eyeballed by sheet (events show dialogue, all 37 chapter cards incl. branch cards 1/5,
battle maps, battle VS intro, intermission pages, save/load, option, game over, staff roll, title menu); 56
states in `work/states/`. PCSX-Redux exited 1 mid-run on 2 of 51 runs with 3 parallel instances: `--retry`
(default 2) re-runs those; `--resume` keeps passed runs. A full sweep takes ~40 min at `--jobs 3`.
