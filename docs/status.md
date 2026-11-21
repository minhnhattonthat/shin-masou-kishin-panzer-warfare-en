# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6. Translate in progress (2026-11-22). Setup done: glossary seeded (Akurasu/SRW names, D8-D10),
  `docs/synopsis.md`, `docs/style-reference.md`, `docs/translator-brief.md`, `docs/reviewer-brief.md`,
  `tools/batches.py` (split/check/merge/terms; msg and battle quotes auto-wrapped, lint rules as the width check),
  `tools/pairs.py` (reviewer pairs). 73 batches in `work/tl/` (b001-b013 battle quotes, b014-b067 events,
  b067-b073 exe + overlay labels); outputs `work/tl/bNNN.out.tsv`. Merged into script/ = `git log`/`batches.py check`.
  Resume: merge every passing .out.tsv (`batches.py merge bNNN`), translate missing batches with
  `translate-retro-game:translator` ("Read docs/translator-brief.md and follow it for batches ..."), then review
  (`pairs.py` → `translate-retro-game:reviewer`, reports in `work/qa/review/`), fix Critical/Important, Minors to
  `docs/polish.md`.
  Last builds 2026-11-22: `build/smk_marker3` (wide marker + grown/relocated event blocks: 123/123 warps,
  `work/qa/marker3/summary.tsv`), `build/smk_torture` (ASCII torture boxes), `build/smk_qa` (battle-quote ruler).
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
  - Phase 5 so far (font.md §Renderer detail / §VWF, windows.md): one string renderer 0x80102D90; font TIM = 4 bit-
    plane glyph pages; VWF hook `asm/vwf.asm` (armips, code+tables in trap-tested free RAM 0x8016D740) + English
    glyphs made from the game's full-width Latin cells (`tools/font.py`: encode, widths, `width_px`, `glyphs`,
    `--preview`); lowercase encoded at 0xA1-0xBA because b h m r w z are colour/font-mode control letters.
    `tools/insert.py` (en / marker / `--qa ID=TEXT` / `--only` bisect; events + battle repacked, exe + overlay in
    place) wired into `build.py [--marker] [--qa ..] [--only ..] [--out ..]`; `tests/test_insert.py`.
    Event-window glyph slots raised 80 → 140 per window (`tools/slots.py`, verified word patches). Probes:
    `tools/lua/strings.lua` (which string pointer each box draws), `slots.lua`, `windows.lua`, `tools/debug/trap.py`.
    Dialogue budget measured: 240 px/line, speaker + 3 lines, 140 glyphs (windows.md).
  - Phase 5 finish (2026-11-22): **event block growth** (scripts.md §Block growth): pools spill past the block end,
    all 35 blocks move to the end of OVER.BIN (sector list exe 0xAFFE4 rewritten, max 0x1F sectors each), so event
    text has no byte budget. Wide marker (every dialogue line filled to 240 px) tours clean: 123/123 warps.
    Width gate rows all measured (windows.md): dialogue 240 px × 3, choices 228 px × JP options, scroll pages
    256 px centred by insert, battle quotes 188 px × 2, chapter label 200 px, status name fields, battle labels.
    Torture line ok. `tools/lint.py` (in Check via tests/test_lint.py): Japanese left, control codes, px/lines per
    measured box, glyph slots, stub last lines, byte max; `--final` fails untranslated lines. insert: speaker
    names from glossary.md Characters, msg newline padding, scroll centring. Tour: remaining Japanese on screen is
    all graphics (G6 option, G9 status labels/skills/spirits, G18 credits); no odd markers seen.
- **Next (phase 6):** finish translation + review (see Phase). **Engine tasks before phase 7 insert** (insert.py; don't edit
  while translators run): (a) battle quotes: RAM slot is 0xC60 bytes per set (slot table 0x800AB7B8), areas full;
  move the slots to free RAM during battle (candidate 0x801CB118-0x801D1D18, trap-test with `trap.py --from` and
  `tools/lua/loads.lua`) and relayout BAT_OVER like OVER; (b) exe strings longer than their JP bytes: relocate
  (ptrs/lui known in exe.json) to trap-tested free space; (c) mcard titles stay Shift-JIS full-width.
- **Open questions for later phases:** the exe 「…」 quotes
  (no reference found, maybe unused: not seen on the marker tour); the u16
  table before each intro scroll (not per page; insert keeps each page's line count); the save-slot list copy of the
  chapter label (needs a save made by the patched build: measure in phase 8); whether the dev
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
