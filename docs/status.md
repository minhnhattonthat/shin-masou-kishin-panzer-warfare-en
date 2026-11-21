# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike and marker build next (phase 4 extract done 2026-11-22). Last build: 2026-11-21,
  `build/smk_en.bin` sha1 e0b0a78b… (= original, no edits yet).
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
  - Phase 3 identity build: `build.py` = `check_rom` → `unpack()` (dumpsxiso into `build/disc/`, fresh each run) →
    `repack()` (mkpsxiso → `build/smk_en.bin/.cue`). `tests/test_identity.py` unpacks + repacks into
    `build/identity/` and asserts the sha1 equals `rom.sha1` (in Check, ~3 s; skipped without the dump). File edits
    go between unpack and repack in `build.main()`.
  - Phase 4 extract: `tools/extract.py` (+ codec `tools/sjis.py`: SJIS, `\n`, space, `{b}{h}{m}{r}{w}{z}`, `[XX]`)
    → `script/` (39 files, 12,770 strings): `events/evXXX.json` x35 (7619 msg + 21 choice with `speaker` split
    off, 68 chapter-intro scroll pages, 3 ダミー), `battle_A/B.json` (2061 each; B text = A, marked `same`),
    `exe.json` (900: 700 pointer/lui + 200 record-region strings with `max` field sizes), `overlay.json` (37
    chapter save labels). `tests/test_extract.py`: roundtrip of every string, script/ = fresh extraction, event
    pools and battle blocks have no unexplained bytes, no overlaps, every SJIS run in exe/OVER/BAT_OVER is
    extracted or waived (waivers listed with reasons). Findings in scripts.md / battle.md §Exe extraction.
- **Next (phase 5, engine spike + marker build):** renderer patch for ASCII/VWF (font.md: half-width bytes are
  skipped; control letters b h m r w z collide with ASCII letters, so the EN encoding must remap them or use
  another code range); trace the font page source; marker build replacing every string with `[id]` (full-width
  Latin works without engine changes) to find non-text strings and measure box widths (width gate). Insertion
  must: repack each event pool within its bounds (`pools` in each JSON; command data follows the pool), rewrite
  ptrs; battle blocks within their sectors; exe strings in place up to `max` or relocate via ptrs/lui.
- **Open questions for later phases:** where the other font pages come from (font.md); the exe 「…」 quotes
  (no reference found, maybe unused: the marker build will tell); effect of control letters `b m r w`; the u16
  table before each intro scroll (line timing?); whether event blocks can grow (scripts.md §Free space); whether the dev
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
