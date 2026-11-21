# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator, in progress (2026-11-22).
  Phase 8 so far: `warp_all.py --rom build/smk_en.cue` 123/123 (`work/qa/warp_en`, states regenerated); JP
  reference warps `work/qa/warp_jp` (16 UI scenes). **Graphics:** `tools/gfx.py` (rows in `gfx/<group>.tsv`, drawn
  in palette-index space into every byte-identical copy of the TIM's pixel block; `img` rows for hand-drawn rects;
  `export`/`preview`/`check`; build stage after armips, writes_check covers the copies; `tests/test_gfx.py`). OFL
  fonts in `fonts/` (docs/fonts.md). Pilot done: 37 chapter cards (`gfx/cards.tsv`, Nunito 26/900, white + dark
  outline, right-aligned, long titles on 2 lines; verified in game `work/qa/cards_en`). Graphics agents (sonnet,
  `docs/graphics-brief.md`, row lists `work/gfx/<group>.txt`) drew the other groups, all merged: mapui (G11, 63 img
  rows), status (G9, 38), menus (G6 option + G16 intermission buttons, 23), battle (G12 + G13 16 reaction TIMs, 21),
  story (G1 prologue 5 pages, G15 caption, G14 loading + dev card, 8), credits (G18, 272 cells; roll = overlay 4
  cell table OVER 0x13F0). 462 rows, `gfx.py check` ok, build sha1 87c51b59…, Check 42 passed. In-game look
  verified on intermission/status/option/credits (`work/qa/gfx_en`); NOT yet seen in game: map command menu +
  battle-confirm (mapui), battle damage/reaction labels, prologue pages, ev01 caption, loading screen — warp/zoom
  them first (agents worked offline; check sprite clipping of Ranged/Gnd/Sea/Luk, "Rear Melee" width, prologue
  page placement, the caption CLUT). Left JP (D17): mapui 14 single-kanji spirit tiles (GRA5 0x11000 x62-160
  y33-62) and status 兵民騎官 tiles (x65-90 y80-100) — find where they show, then redraw; credits 摯 遺; T_TIM
  0x19D000 (dead sheet). G7 map label is pseudo-Latin (no row). G10 FMV mov01 subtitles: not started (jPSXdec).
  **Tour:** `tools/debug/tour.py` (warp each evNN with KEEP=1, mash circle, shot every 40, sheets in
  `<out>/sheets/`). JP tour done: `work/qa/tour_jp` (35/35, 596 sheets). EN tour not yet run on the current build
  (run it, then `qa_gate.py init work/qa/manifest.tsv work/qa/tour/sheets --build build/smk_en.bin`, chunks of
  30, visual-qa agents with `docs/visual-qa-brief.md`, up to 4 at a time).
  **Bug (3) fixed** (commit ffac57d): the map weapon list's garbage column / half window / missing HIT label was
  not glyph slots (the list uses a running slot counter from 0) but `exe_A72E8` 靭: bytes `90 78 20 00` of a 12-byte
  sprite-record table that the extractor took for a string; insert moved and zeroed it. `extract.NOT_TEXT` skips it
  (swept every other short pointer string: all real text). Found with `tools/bisect_ids.py` (build with listed ids
  kept JP) + `tools/debug/bug3_check.py` (cold boot ev01 KEEP=1 to f10500, scores the garbage column).
  Play session `work/play/confirm` (state `work/states/ev01_map_p1.sstate`, f9950 of ev01 KEEP=1): player attack
  (command menu, target, map confirm 0010), battle, end turn, enemy-phase counter screen (0015): all clean.
  Phase-7 review fixes (2026-11-22, H:\translation\.harness\reviews\...-phase7.md, all 7 Important + 4 Minor):
  (1) fixed-field alignment: `insert.align` re-pads exe/overlay fields like the JP (leading = right, both = centre)
  within the slot's bytes (D16). (2) HUD bug fixed: battle labels had 8 glyph slots each (bases 0/8/0x10/0x18);
  `slots.py` WORDS re-bases mechs 0x70/0x7C (+ the VS-intro names that shared them), pilot L 0x0C, quote free count
  0x20 → 0x48; 8 army labels abbreviated like the JP (D15); verified battle05 (`work/qa/hud_fix`), windows.md §Battle
  HUD slots. (3) mcard system title + save line kept JP (keep_jp.txt). (4)(6) `tests/test_insert.py::test_real_script`
  inserts the real script/ and runs writes_check + every-pointer/lui-reaches-its-string + no-stale-refs + no branch
  into a hook; shared-lui guard in `_relocate` (`test_shared_lui_string_does_not_move`); lint final in Check.
  (5) per-stage write log (`insert.log_diff` → `build/writes/*.log`, romdiff `--writes`), narrowed ranges, font
  files checked, other disc files must be unchanged. (7) lint px/glyph budgets: ov 200 px, HUD tables, quote 72
  glyphs. Minors: vacated slots zeroed, `script/jp_known.txt` (jp_left exits 0), D13/D14 order, appended bytes counted.
  Build sha1 b05f04a4…, smoke ok, Check 38 passed.
  Phase 7 is **done**: `python build.py` is green
  (build `smk_en.bin` sha1 3cbcd114…, smoke ok), `lint.py --final` 0 errors (control codes, px/lines per measured box),
  `batches.py check` 0 problems, `tools/writes_check.py` (romdiff on exe / OVER / BAT_OVER vs planned ranges, run by
  build.py) passes, Check 34 passed. Engine work (docs/re/battle.md §Runtime, §Relocation): (a) battle-quote blocks
  rebuilt for new RAM slots A 0x801CB118 / B 0x801CE718 and appended to BAT_OVER.BIN; the record-pointer tables
  (exe 0xC59D8 / 0xC5CE4) and load-address words follow; English quotes render from both sets (`work/qa/bq_en`).
  (b) the 42 long exe strings move (`insert._relocate`) into slot tails / old slots / 0x8016DA60-0x8016DC3F, u32
  ptrs + lui pairs re-aimed. (c) card titles stay JP (D14, `script/keep_jp.txt`). `tools/bisect_boot.py` bisects a
  black boot by script file (`build.py --only` now works in en mode).
  Phase 6 review fixes (2026-11-22, commit 1b3ec32): Havoc Beam / Caloric Buoy in both exe lists (b105, D13), Mira
  cut + dropped translator questions + US-spelling ids in polish.md "Hand-kept" (survives `review_fixes.py --polish`),
  D11 (harmonise), D12 (pilot waived), reviewer brief read-in-parts line.
  Phase 6: all 73 batches have a reviewer verdict in `docs/review/reports.tsv`, C/I fixes b102-b104, 233 Minors in
  `docs/polish.md`. Raw reviewer outputs: `work/review_in/`.
  Phase 6 history: glossary seeded (Akurasu/SRW names, D8-D10),
  `docs/synopsis.md`, `docs/style-reference.md`, `docs/translator-brief.md`, `docs/reviewer-brief.md`,
  `tools/batches.py` (split/check/merge/terms; msg and battle quotes auto-wrapped, lint rules as the width check),
  `tools/pairs.py` (reviewer pairs). 73 batches in `work/tl/` (b001-b013 battle quotes, b014-b067 events,
  b067-b073 exe + overlay labels); outputs `work/tl/bNNN.out.tsv`. **All 73 batches translated and merged** (wave 1,
  15 translator agents; lint 0 errors, 10,706 English lines, 0 untranslated; 34 exe strings over their JP bytes
  await phase-7 relocation). Translator reports' NEW TERM / UNSURE / CUT lines are collected in `docs/terms-pending.md`.
  Steps (1)-(3) done 2026-11-22: glossary has all wave-1 terms, conflicts settled (Masouhei / Masou Soldier, spirit
  commands Gain/Grit/Spellbind, Sky Slash, Reslug/Bemlug, Rebel Knight...: see glossary "Decisions"); consistency pass
  `tools/harmonise.py` (majority EN per repeated JP line + speaker, 204 lines merged). (4) review: one
  `translate-retro-game:reviewer` subagent per `work/qa/review/bNNN.txt` (`pairs.py`), compact TSV report appended
  to `docs/review/reports.tsv`; `tools/review_fixes.py bNNN` turns C/I rows into a merge batch (later row per id
  wins; fix width failures with an override row), `review_fixes.py --polish` regenerates polish.md.
  Codex is quota-blocked until 2026-11-26.
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
- **Next (phase 8), in order:** (a) done (bugs 1-3 above); (b) warp + zoom the unverified graphics screens above
  (map command menu + map confirm now seen clean in `work/play/confirm`), fix; (c) EN tour + qa_gate + visual-QA
  verdicts on every sheet (UI warp scenes too: add their scene.png sheets to the manifest); (d) the left-JP tiles
  and FMV mov01; (e) inkbox on choices/centred menus; (f) stress saves (needs `save.py` / unit record layout);
  (g) `textcover.py` (strings.lua logs STR <ram ptr>; build must emit build/strings.tsv with RAM addresses).
  Exe px widths are unmeasured for most menus (lint "unmeasured exe 885"): judge them on the sheets. exe_B60F4
  ("...Tiger's Tail") is pointer-reached, so its polish.md suggestion can now apply (it moves); ov_ECE34 / ov_ECE54
  are fixed 31-byte fields.
  Free exe space left for moved strings is small (0x8016DA60-0x8016DC3F + slot tails); if a polish pass makes more
  exe lines longer and insert reports "no exe free space left", trap-test another run first (not 0x80170935+).
- **Open questions for later phases:** the exe 「…」 quotes
  (no reference found, maybe unused: not seen on the marker tour); the u16
  table before each intro scroll (not per page; insert keeps each page's line count); the save-slot list copy of the
  chapter label (needs a save made by the patched build: measure in phase 8); whether the dev
  loading card BAT_TIM 0x45A000 is ever shown; the chapter-card picker / branch flags for cards 1 and 5 (debug.md);
  unit record layout (GOD mode, stress values) and a save editor (`save.py`), deferred to phase 8 stress saves: the
  warps reach every stage without saves; a forced intermission has zeroed stats, so menu stress values need RAM
  writes or the editor then.
- **Open bugs:** none known. Closed 2026-11-22: (1) the fixed-slot screen 0x8011C178 (slots 0x180-0x1FF) is a
  battle-test setup screen (labels 味方 右側 / 敵 左側, mode 11 state 0 of 0x8011A4F8); the real map confirm and
  enemy-phase counter screens use the running counter (0x800C6Bxx) and slots 0x180-0x1FF stayed empty through a
  whole battle (`work/qa/confirm_battle`): left as is. (2) map after a battle: clean (`work/play/confirm/0014.png`).
- **Waiting on the user:** nothing.

Warp sweep (original disc, 2026-11-21): `warp_all.py --states` 123/123 scenes reached from a cold boot, every
proof shot non-blank and eyeballed by sheet (events show dialogue, all 37 chapter cards incl. branch cards 1/5,
battle maps, battle VS intro, intermission pages, save/load, option, game over, staff roll, title menu); 56
states in `work/states/`. PCSX-Redux exited 1 mid-run on 2 of 51 runs with 3 parallel instances: `--retry`
(default 2) re-runs those; `--resume` keeps passed runs. A full sweep takes ~40 min at `--jobs 3`.
