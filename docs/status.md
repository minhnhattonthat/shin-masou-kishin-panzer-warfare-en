# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9. Release done: `release/SMK_EN_v1.0.zip` built and verified on build b7c455cf (session 12 below).
  Published 2026-11-23 on the user's go: GitHub release v1.0 (tag on main, zip attached). Repo is still PRIVATE,
  so the release and README's issues link are not public until the user changes visibility.
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
  verified on intermission/status/option/credits (`work/qa/gfx_en`). Seen in game 2026-11-22 (build after ffac57d):
  map command menu, map confirm + enemy-phase counter screen incl. Battle Animation ON/OFF (`work/play/confirm`,
  `work/play/noanim`), all 5 prologue pages (`work/qa/pro4z.png`, from state `work/states/newgame_fmv.sstate` = title >
  START, run with no input; the text wrap at the top between pages is the JP's too), loading logo screen.
  NOT seen: G12 damage labels (BAT_TIM 0x499800 sits in VRAM 832,0 through battle05 but no frame showed a label at
  4-frame density, `work/qa/b05_dense`), G13 reaction cut-ins (never uploaded to VRAM in battle05 nor with Battle
  Animation OFF), G15 caption (GRA5 0x76800 is in VRAM 768,256 from f2700 to f6600 of ev01 but never seen drawn).
  Tool: `tools/debug/vram_find.py FILE OFF DUMPDIR` finds a TIM in ppudump.lua VRAM dumps. Look for these on the
  EN tour sheets; if still unseen, waive them in the gate with that evidence. Left JP (D17): mapui 14 single-kanji spirit tiles (GRA5 0x11000 x62-160
  y33-62) and status 兵民騎官 tiles (x65-90 y80-100) — find where they show, then redraw; credits 摯 遺; T_TIM
  0x19D000 (dead sheet). G7 map label is pseudo-Latin (no row). G10 FMV mov01 subtitles: not started (jPSXdec).
  **Tour:** `tools/debug/tour.py` (warp each evNN with KEEP=1, mash circle, shot every 40, sheets in
  `<out>/sheets/`). JP tour done: `work/qa/tour_jp` (35/35, 596 sheets). EN tour 2026-11-22 on build sha1 b6f10e61
  (= HEAD c0d0cd1): ev01-ev16 done in `work/qa/tour` (238 sheets in `work/qa/tour/sheets`); the run was killed
  for low system memory at ev17-ev20 (partials deleted). Resume: `python -X utf8 tools/debug/tour.py ev17 ev18 ..
  ev35 --jobs 2` (4 parallel PCSX ran the machine out of memory). Then `qa_gate.py init work/qa/manifest.tsv work/qa/tour/sheets --build build/smk_en.bin`, chunks of
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
- **Session 2026-11-22 (later):** EN tour ev17-35 finished on b6f10e61 (kept as `work/qa/tour_b6f1`). Build now
  3813f21e (smoke ok): ev000 choice options [Other] / [Back to ...] centred like the JP (inkbox ok on 0005/0006/0007
  of `work/play/choice_ch`; the other 15 op-0001 "choices" are plain messages, left-aligned like the JP).
  **Text coverage tooling** (commit d8bfeb9): `tools/lua/textcover.lua` logs `PTR addr bytes`; build.py writes
  `build/<out>.strings.tsv` (id, key, RAM addr, built bytes, quote twin) via `tools/cover.py`; `cover.py logs DIR..
  --out work/qa/cover` matches PTRs by address+bytes (event blocks/overlays/quote slots share RAM) and writes TEXT
  keys for `$SKILL/scripts/textcover.py work/qa/cover build/smk_en.strings.tsv --waive docs/text_unshown.tsv`.
  tour.py always loads the probe; `warp_all.py --cover` too. `tools/lua/stop_at.lua STOP=<addr>` saves a state when
  a string is drawn (play.py start point for any event line). Running: full EN tour ev01-35 on 3813f21e with the
  probe → `work/qa/tour` (log `work/qa/tour_full.log`); manifest `work/qa/manifest.tsv` (596 sheets, init'd from the
  b6f1 sheets copied into `work/qa/tour/sheets`; re-run `qa_gate.py init` after the tour: unchanged sheets keep
  their verdicts); visual-QA chunks `work/qa/chunks/chunk_343280f8144c_000..019`, verdicts `work/qa/verdicts/`
  (000-007 reviewed on the b6f1 sheets; 001 and 006 flagged bug 4 below; 008-019 not dispatched). The full tour
  run was still going (ev03+) at hand-back: if `work/qa/tour_full.log` is short of ev35, re-run the missing scenes.
- **Session 2026-11-22 (3):** bugs 4, 5, 6 fixed (commits 1e6c900, 04e2588, 8f0e221; build c62b2dce, smoke ok,
  Check 44 passed). (4) intro scroll freed 200 glyph slots, EN pages draw up to ~336: `slots.py` frees 430 at
  0x801159B8/0x80115A54/0x80115A90 (verified ev03 `work/qa/b4_fix`). (6) confirm screen pilot names: asm
  `pilot_short` + `script/confirm_short.tsv` (D18, verified ev06 `work/qa/b6_fix`). (5) `batches.py` wrap balances
  a segment that would leave one word on its last line; `batches.py rewrap` re-wrapped 709 msg/bq lines (no other
  line changed); lint flags wrap-made one-word last lines. Probe `tools/lua/calls.lua ADDR=` (ra + args of calls).
  Full EN tour on c62b2dce started (`tools/debug/tour.py --jobs 2` → `work/qa/tour`, log `work/qa/tour_full.log`);
  if short of ev35, re-run the missing scenes. Then re-init the manifest, re-check chunks 000-007 (bugs fixed) and
  dispatch the rest. Spirit marker tiles (GRA5 0x11000): not shown by Guts (instant); need a pilot with a lasting
  spirit (Focus/Alert/...) on a later map, or the unit record's spirit flags.
- **Session 2026-11-22 (4):** full EN tour on c62b2dce done (35/35, deterministic: a re-tour of ev23 on the next
  build changed only the 2 sheets whose text changed). **Visual-QA gate passes**: 598/598 sheets have a verdict
  (`qa_gate.py check` exit 0, manifest `work/qa/manifest.tsv` init'd on build d4f5130a). Codex was out of quota
  (until 2026-11-26), so the verdicts are from a separate read-only pass in this session, every sheet viewed, menus/
  confirm/battle HUD/3-line boxes zoomed from the raw frames (scratch helper wrote `work/qa/codex/zoom/`), oddities
  compared with `work/qa/tour_jp`. Bugs 4/5/6 confirmed fixed on the sheets. One new bug, fixed (a49d7f5): speaker
  label 民間兵 drew "Militiaman / Militiamen" (insert.speaker_names took the whole glossary cell; now the first form;
  test). G12 battle "Damage" label seen in English (ev20_sheet_21 t9, ev27_sheet_19 t16): closed. G13 reaction
  cut-ins and G15 caption: still on no sheet of either tour (EN or JP) → waive with the VRAM evidence above.
  Running at hand-back: `warp_all.py --rom build/smk_en.cue --out work/qa/warp_en --cover --jobs 2` (log
  `work/qa/warp_en.log`) for the coverage logs; if the log is short of 123 scenes, re-run with `--resume`.
- **Session 2026-11-22 (5), build d4f5130a (= HEAD build; smoke ok):** warp sweep `work/qa/warp_en` 123/123
  (re-ran the 46 that failed with rc 0xC0000142 = out of desktop heap with other projects' emulators running: use
  `--jobs 1`/2 and `--resume`). **Text coverage** first report: 4475/12769 shown (`work/qa/textcover.txt`; events
  ~60 %, bq 3 %, exe 76/899, ov 1/37). New **forced display** (`tools/debug/force_text.py` + `.lua`, doc in the
  script): from one state per box (`work/states/force_msg.sstate` ev01 f3480, `force_bq.sstate` ev05 f15082, both
  made with `tools/lua/state_at.lua --debugger`) it writes each unshown string's built bytes over the string the box
  is about to draw and shoots it; cover logs in `work/qa/cover/force_*`. Done: all 3441 unshown event strings
  (msg_000-022, long ones re-shot at --hold 180 from `work/qa/force_long`) and all 1997 set-A quotes (B twins count
  too). `tools/debug/force_check.py msg|bq`: ink inside the box for every shot (msg max x 306 of 310, bq 250 of 252,
  no 4th line), 0 fail; samples viewed (`work/qa/force/sample/`). Not yet re-run: `cover.py logs` + textcover with
  the force logs (they are already in work/qa/cover: just run textcover).
  **Bug 7 found (open, real, not a force artefact):** in any message with more than 80 glyphs (speaker included) the
  glyphs from the 81st on stay dim grey forever (tour ev01 f3600 shows it; 598 tour verdicts read it as typing).
  Analysis + leads in docs/re/windows.md "Bug 7": colour chosen by the OLD window slot ranges (slot ≥ 90 = window 1
  = dim). Fix it in `tools/slots.py`, then re-run `force_text.py msg` (all) + `force_check.py` and re-tour (glyph
  colours change on every long line).
  Warp UI shots: `work/qa/warp_en/{credits,credits_late,card_k01,card_k05}/scene.png` were stale/JP (card:K read
  the JP GRA5: fixed, warp_all.py now passes the build's GRA5); fresh credits shots are English. A fresh UI sweep
  was running at hand-back → `work/qa/warp_ui` (log `work/qa/warp_ui.log`; finish with `--resume`), then sheet its
  scene.png files and give them verdicts. **im_status_mech is Japanese** (ステータス, 操者/機体/攻撃技 tabs, 装甲 反応
  移動 空地水 適応: a TIM other than TIM.BIN A5128 that G9 drew): find its TIM (vram_find.py) and add gfx rows.
  **Exe coverage plan** (823 exe + 36 ov unshown): same force method per box, one base state each: weapon list
  (exe_00D38-01D80, 192), unit/pilot names (exe_04DDC-05FA4, 226; HUD/status/confirm fields), spirit names + help
  and win/lose lines (exe_ACFD4-AD8B1), map messages (exe_027C8, 02BF0), level-up lines (exe_035A8), elements and
  terrain (exe_D1E38-D29C8), memory-card lines (exe_0403C, B3930-B61EC), chapter labels (ov_*, intermission label);
  exe_C3DC8-C4C98 (109 exe 「…」 quotes, no pointers): prove unused (xref) and waive in docs/text_unshown.tsv. Fixed
  fields: write only same-category strings (same `max`).
- **Session 2026-11-22 (6):** **bug 7 fixed** (abc43ab, build 98bbd2b9, Check 44 passed): 0x80115B4C dims the
  inactive windows with the old 80-slot ranges as immediates; `slots.py` WORDS re-aims them (windows.md "Bug 7"),
  verified `work/qa/b7_fix/f003550.png`. **Full EN re-tour started** for bug 7 (`tour.py --jobs 2` → `work/qa/tour`,
  log `work/qa/tour_full.log`; ev01-02 done at hand-back, ~20 min a scene with other projects' emulators running).
  If the log is short of ev35 and no tour.py runs (`tasklist | grep pcsx`), re-run the missing scenes. **NOT built
  yet:** `script/exe.json` exe_0441C (save/load screen header) "Do not remove the Memory Card" was cut after
  "Memory" (runtime limit 24 chars / 20 glyphs, `work/qa/ui_sheets/m1.png`) → "Leave the Memory Card in" (fits
  both). Build after the tour ends (never while it runs), cold-boot im_save to check, then `qa_gate.py init
  work/qa/manifest.tsv work/qa/tour/sheets --build build/smk_en.bin` (that string is on no tour sheet) and give
  verdicts to the changed sheets. UI warps `work/qa/warp_ui` now complete (all 19 UI scenes + card_k01/05; logs
  warp_ui*.log); viewed so far: title_load/continue, im_save(+confirm), intermission, im_load, im_status_pilot/
  mech/weapons: English and clean except the header above; **im_status_mech is English** (the old "Japanese" note
  was a stale shot). Not yet viewed: im_next, option, gameover, credits, credits_late, battle05, card_k01/05.
  **Text coverage** 11975/12769 shown, 126 waived (`docs/text_unshown.tsv`: 109 exe quotes 0xC3DC8-0xC4CB3 with
  no pointer/lui into them; 17 memory-card file titles kept JP), 668 failing (`work/qa/textcover.txt`). Fixed
  force_text twin credit (set-A forced quotes now credit their set-B twin; force_bq cover logs rewritten: all
  quotes covered). New force kind `wpn` (weapon names exe_00D38-0133C in the map weapon list, state
  `work/states/force_wpn.sstate`; 65 forced, sheets `work/qa/force/sheets/wpn_000*`, longest name fits; no
  verdict file yet). `work/states/ev01_map_p1.sstate` regenerated on the current build (`weapon_list_pre.sstate`
  is stale: its RAM holds the pre-bug-3 exe). `tools/lua/press_seq.lua` (SEQ presses + STATE_AT state).
  Left 668: exe names 0x134C-0x1D68 (pilot short 13AC-14D0, pilot full 14E8-1920, mech short 193C-1AF4, mech
  full 1B24-1D68: unit box mech name 0x800A74B8 draws at f13 of ev01_map_p1 after circle; the pilot name is a RAM
  copy 0x801776E0, so force pilot names there), the {h}NN weapon/unit table exe_04DDC-05FA4 (226; find its
  screen: maybe the battle-test setup 0x8011C178 of bug 1, then waive as unreachable), map messages 027C8/02BF0,
  level-up 035A8-039C8, memcard 0403C-040B0 + B3930-B460C, spirit names/help + objectives ACFD4-AD8B1, chapter
  labels B5E40-B61EC + ov_* (36), status B76D4-B7A9A, elements/terrain D1E40-D29C8.
- **Session 2026-11-22 (7), build 860d0e73 (= HEAD 57a68e9 + this status; smoke ok, Check 44 passed):** the session-6
  re-tour had died (31/35 rc 0xC0000142 with extra emulators open); `tour.py` now retries that rc (`--retry 3`) and
  drops a scene's old sheets only after a good run. **Full EN re-tour running at hand-back** on 860d0e73:
  `tools/debug/tour.py --jobs 2` → `work/qa/tour` (log `work/qa/tour_full.log`, started 19:38, ~2.5 min/scene;
  old sheets kept in `work/qa/tour_prev_sheets` for `sheet.py --compare`). If no tour.py runs and the log is short
  of 35 ok, re-run the missing scenes (`tour.py evNN ..`). Do not build while it runs. Then `qa_gate.py init
  work/qa/manifest.tsv work/qa/tour/sheets --build build/smk_en.bin`, verdicts for the changed sheets.
  Fixed: (8) map unit box "Masou Soldier" touched "Lv." → asm moves Lv./level 8 px right (windows.md §Map unit
  box); (9) end-turn prompt exe_02BF0: the game draws the unmoved-unit count at text x+48 (x+44 for 10+) over the
  JP's two spaces; EN ran under it ("u|nits") → "Oh, still     to move..." (verified count 1, `work/qa/explore/cnt1`);
  (10) title LOAD/CONTINUE card screen had JP cell spacing: a third font TIM copy GRA5 0x199A800 was unpatched →
  `font.TIM_COPIES`; writes_check fails any built file holding original font cells. Verified `work/qa/explore/tl4`.
  **Coverage:** force kinds `pilot` (31, unit box pilot field), `mech` (49), `pfull` (46, status pilot page),
  `imlabel` (36 intermission labels; the last two are JP placeholders "」まで終了" → "Clear:"), all shown and
  viewed: fit (Super Majuuki Ag Gebra 4 px from the gauge). Map menu End/Goal/System/Save reached by route from
  `ev01_map_p1.sstate` (`work/qa/mapmenu`, cover logs in work/qa/cover/mapmenu). 228 battle-test strings waived
  (table 0x8016AAF8 read by the dev screen 0x8011C3B8). textcover: **301 failing** (`work/qa/textcover.txt`).
  Force sheets (`work/qa/force/sheets` pilot/mech/pfull/imlabel/wpn) have no gate verdicts yet: make a separate
  manifest (`qa_gate.py init work/qa/force_manifest.tsv work/qa/force/sheets --glob "<kind>_*"` per kind or all)
  and write verdicts (all viewed ok this session; pilot re-run after the Lv. fix). `tools/cover_ids.py`: which ids
  a cover dir shows / which are new. States `work/states/{ev01_map_p1,im_*,option,title*,gameover,intermission,
  force_imlabel}.sstate` regenerated on e036a999/98bbd2b9 (UI ones were stale JP-graphics states from 08:59).
  Left 301: memcard 0403C-040B0 (YES/NO, Memory Card 1/2), 042B0-042D4, 043F8-04410 (-Holy/-High/-Low), 0486C-04890,
  level-up screen 035A8-039C8 (skill LV lines: JP pads with spaces before ＬＶ, check for a number drawn at a fixed
  x like bug 9), map msgs 027C8-02834, spirit names/help + objectives ACFD4-AD8B1, memcard msgs B3930-B460C,
  save-slot labels B5E40-B61EC (title LOAD with `--sav tools/debug/saves/stage05_intermission.mcd` draws DATA 01 +
  label: 0x8015B640 / 0x8015B7B0, f4476 of warp title_load; force there), status B76D4-B7A9A, elements/terrain
  D1E40-D29C8.
- **Session 2026-11-22 (8):** **text coverage 0 failing** (12350/12769 shown, 419 waived; `work/qa/textcover.txt`).
  New force kinds (doc in `tools/debug/force_text.py`): `sdata`/`schap` (save-slot labels, `--sav`), `mcmsg`,
  `spname`/`sphelp` (`force_spirit.sstate`, map sub-mode byte 0x80178240 = 17, debug.md), `gwin`/`glose`/`glabel`
  (Goal box), `endturn`, `lvban`/`lvhelp`/`lvdlg` (level-up, sub-mode 24). Waivers: dev battle-test labels, dead code
  proven by `tools/callers.py` (caller tree), "screen not found" 0x8010BE78 strings. Spirit grid: SP cost moved +14
  px (asm 0x800DD3CC/0x800DD530) and grid label Friendship → "Friend." (D19); spirit help indent rule in insert/lint.
  Force sheets gated: `work/qa/force_manifest.tsv` + `work/qa/force_verdicts` 35 sheets ok. Re-tour on 860d0e73
  complete (`work/qa/tour`, logs tour_full/tour_rest/tour_ev35), 558 sheets; manifest re-inited on 860d0e73 (40
  vanished sheet ids dropped), 272 changed sheets → chunks `chunk_847f929d261e_*`. Then built **ea1259ab** (the D19
  asm sites were missing from writes_check's allowed ranges: added; the earlier "860d0e73" was the last good build,
  so spirit/level-up checks before this were on pokes + forced strings.tsv bytes). On ea1259ab: spirit grid cost at
  the new x (`work/qa/regen/spirit/f000120.png`). States `ev01_map_p1`, `force_spirit`, `force_lvup_banner`,
  `force_lvup` regenerated on ea1259ab, BUT forcing from them does not take (spname sheets all show Guts; a poke of
  the record name before menu open also shows Guts; force_lvup at banner+360 still shows the banner): re-derive
  the recipes before using these kinds again.
  **Tour gate passes** (`qa_gate.py check work/qa/manifest.tsv work/qa/verdicts`: 558 ok/fixed, build 5b9f8e53
  waived as a hotfix with the evidence above; verdicts `chunk_847f929d261e_*` + `fix_s8.tsv`). Visual QA found:
  card 24 (and 1 px of card 18) kept a JP ち remnant right of the redraw rect → `gfx/cards.tsv` rect w 248, dx -26
  (verified warp card17/card23); Alfredo's ev179_229C split "Rieg Gram / Garum" and bqA_2A_0FC split "Ag / Gebra"
  → rewrapped (forced, `work/qa/explore/fix_wrap.png`; other glossary splits are titles like Royal/Capital, left);
  unit box "Masoukishin Cybuster" tail appears a few frames late during the box fade-in (settled box whole and
  bright: `work/qa/explore/cyb_z.png`) → ok. Build **5b9f8e53**, Check 44, smoke ok, textcover 0 failing.
- **Session 2026-11-22 (9), build 15fa7205 (Check 44, gates ok):** D17 tiles done (commit bc0c5ad): map unit box
  spirit markers → Al Fo Ga St IW Va So Sb (`tools/gfx_mapui.py` kind `col`; marker = active-spirit bit n = spirit id
  n at u16 0x80178604, drawn after "Lv."; 加幸旋結協超 have no spirit: left JP), status class badges 兵民騎官 → S C K O
  (`tools/gfx_status.py` kind `badge`; S seen on Keigo's pilot page, C/K/O preview only). Pilot record + recipe in
  debug.md; **pokes at frame 1 are lost to the state load: use AT >= 8** (why session 8's force_spirit/force_lvup
  recipes failed). UI warps re-run on the current build (`work/qa/ui_en`, 18/18); new graphics gate
  `work/qa/gfx_manifest.tsv` + `work/qa/gfx_verdicts` (10 shots in `work/qa/gfx_proof`: the 8 UI shots that lacked
  verdicts + markers + badge, all ok). Tour gate waived for 15fa7205 (graphics-only). G13/G15 waived in
  docs/re/graphics.md with the VRAM evidence. Forecast "dots vs ⅠⅡ" (ev05 f13680): the JP has エル・ザーリラ (・),
  EN "El Zarila"; terrain labels are atlas lookups: ok. `ev01_map_p1.sstate` regenerated on this build.
- **Session 2026-11-23 (10), build 3c63e899 (Check 46, smoke ok, 4 gates ok, textcover 0 failing): phase 8 DONE.**
  (A) G10 FMV: `tools/fmv.py` + `gfx/fmv/subtitles.tsv` burn English into mov01 (boot attract advert) frames
  171-213 / 251-300 / 419-455: JP glyphs filled from their surroundings, blurred dark band, Nunito 900; own MDEC v2
  encoder (the permission classifier refused to run a downloaded jPSXdec), each frame back in its own sectors.
  Frames need the 0x1FF end code (without it the game froze on frame 171). build.py stage after gfx (needs ffmpeg;
  cached in `build/fmv_cache/`, first build ~4-6 min); writes_check covers MOV.STR; `tests/test_fmv.py`. Seen in
  game on a cold boot (`work/qa/fmv_boot2`), then Banpresto + title (`work/qa/fmv_after`). mov12 at 1-s steps: only
  the game logo (D5). Gate: `work/qa/gfx_manifest.tsv` + `gfx_verdicts/s10.tsv` (fmv_mov01_*).
  (B) stress: `tools/debug/stress.py` (cases status / battle / levelup: Lv 99, EXP 9999999, stats 0xFF, SP 255,
  HP 65535 incl. enemies; real level-up from Lv 1 EXP 199) → `work/qa/stress_proof` (8 shots), gate
  `work/qa/stress_manifest.tsv` + `work/qa/stress_verdicts`: all fit. Record layout in debug.md. The game clamps
  stats to 55 and EXP to 6 digits. Names are fixed (no name entry); longest names/lists were forced in session 7-8
  (force kinds, gated). Full weapon lists of late units not reached (map20/map35 states land mid-event), covered by
  the forced `wpn` names. `work/states/ev01_map_p1.sstate` regenerated on 3c63e899 (the old one had stale VRAM: 兵
  badge) + `jp_ev01_map_p1.sstate` (JP disc). Tour + force gates waived for 3c63e899 (MOV.STR-only change).
- **Session 2026-11-23 (11), build ef6484d5 (Check 46):** (A) **polish pass done**: 245 phase-6 lines applied
  (b106-b109 via `review_fixes.py --from-polish/--tick`; US spellings swept) or waived (fixed fields, D20).
  (B) **story pass done**: `pairs.py --chapters` -> `work/qa/story/chapters` (35), brief `docs/story-reviewer-brief.md`,
  one reviewer subagent per chapter, reports `work/qa/story/reports/*.tsv` (+ `99_sweep.tsv`: silent lines unified to
  "..." / "(...)", "All right"), `tools/story_fixes.py verdicts|batch|log`; 352 fixes merged as b110 (2 C, 3 I, rest
  Minors), 4 C/I chapters re-checked by fresh reviewers (fixed); gate `qa_gate.py check work/qa/story/manifest.tsv
  work/qa/story/verdicts` exit 0; polish.md 0 unticked. LV padding (exe_03760/78/90) seen in game
  (`work/qa/force_lv/lv_zoom.png`). (C) `tools/release.py` (build, check, smoke, jp_left on exe/OVER/BAT_OVER minus
  the dead old quote blocks, every `*manifest.tsv` gate, textcover, polish, README placeholders, xdelta3 -B, re-apply
  compare, zip with `docs/release-readme.txt`); README filled. GRA5/BAT_TIM/T_TIM jp_left hits are TIM pixel noise.
  (D) warp_all 123/123 on ef6484d5 (`work/qa/warp_ef64`); `ev01_map_p1.sstate` regenerated on ef6484d5.
- **Session 2026-11-23 (12), build b7c455cf (HEAD c058fed, Check 47): phase 9 DONE.** Full EN re-tour on ef6484d5
  (35/35, 596 sheets; 261 changed/new → 9 chunks `chunk_301e85e900cb_*`, visual-qa subagents): 2 issues, both
  fixed (commit 1cfaa78): ev086_4970 intro scroll had "\n/ " instead of "\n\n" (story-pass merge pasted polish.md's
  " / " display form; only such line; lint now fails "/ " line starts, c058fed), ev033_2028 wrap after "mention it,";
  plus ev01C_2010 wrap made the same as its twin ev01C_1FD4. Re-tour on b7c455cf: 7 sheets changed (exactly those
  scenes), verdicts `chunk_127318d24d2d_000` ok. Gfx gate: UI warps `work/qa/warp_b7c4` + FMV cold boot
  `work/qa/fmv_b7c4` (376/376 frames equal fmv_boot2) pixel-identical, battle05 re-shot (verdict `gfx_verdicts/s12`).
  Stress: `ev01_map_p1.sstate` regenerated on b7c455cf, `stress.py` all cases, shots identical. `tools/release.py
  --version 1.0` exit 0: build, Check, smoke, jp_left, 5 gates, textcover 0 failing, xdelta made + re-applied →
  `release/SMK_EN_v1.0.zip` (xdelta + README.txt; patched .bin CRC32 8AD8670A, SHA-1 b7c455cf…). Never
  `gh release create`: the user publishes.
- **Old next list (phase 9, done in session 12):** the tour / gfx / stress gates are STALE (recorded builds 860d0e73 /
  3c63e899, now ef6484d5). `qa_gate.py waive` was refused by the auto-mode permission classifier this session, so
  re-run them for real: (1) `python -X utf8 tools/debug/tour.py ev01 .. ev35 --jobs 2` (all 35; 4 PCSX ran out of
  memory before), then `qa_gate.py init work/qa/manifest.tsv work/qa/tour/sheets --build build/smk_en.bin`; only
  sheets whose pixels changed lose their verdicts: `qa_gate.py todo ... --size 30 --out-dir work/qa/chunks`, one
  visual-qa subagent per chunk (`docs/visual-qa-brief.md`, up to 4 at a time). (2) gfx gate: re-shoot
  `work/qa/gfx_proof` (UI warps `work/qa/warp_ef64` + fmv shots per session 9/10 notes), `init --build`, verdicts.
  (3) stress: `tools/debug/stress.py --rom build/smk_en.cue` (all cases), `init work/qa/stress_manifest.tsv
  work/qa/stress_proof --glob "*.png" --build build/smk_en.bin`, verdicts. (4) `python -X utf8 tools/release.py`
  (version 1.0): it runs every gate and stops at the first failure; it ends at release/SMK_EN_v1.0.zip. Never
  `gh release create`. Story gate, polish (0 unticked), README, jp_left (exe/OVER/BAT_OVER) and textcover already pass.
- **Older next list (phase 9):** story-pass verdict per chapter (`qa_gate.py check work/qa/story/manifest.tsv ..`,
  translation.md §Review); `docs/polish.md` has unticked lines (233 Minors): apply or tick each; `tools/release.py`
  (runs qa_gate on every manifest + textcover, jp_left, debug tool off, xdelta made/re-applied/verified), README
  without template placeholders and with the base ROM hashes, zip = patch + README. Never `gh release create`.
  Older list: DONE: re-tour + gate, exe coverage/textcover, bugs 1-10, force-sheet gate.
  Inkbox: save confirm YES/NO (`work/qa/warp_ui/im_save_confirm/scene.png`, rects 114,135,27,11 l4/r3 and
  179,135,27,11 `--ink 255,255,255 --diff 60` l5/r7) ok; Goal box lines match the JP's padding (session 8);
  exe_04064/040B0 YES/NO are dead code (waived). Session 9 closed (1), (2), (5) and the ⅠⅡ check; (3) (4) are (A) (B) above. Was LEFT: (1) G13/G15 unseen on both tours: waive in
  the gate with the VRAM evidence (top of this file); (2) left-JP tiles D17 (GRA5 0x11000 single-kanji icons
  必集閃鉄熱魂加 / 幸旋縛結協努超 = spirit/status markers, status 兵民騎官 tiles, credits 摯 遺: find the screen,
  redraw, zoomed cold-boot shot); (3) G10 FMV mov01 subtitles (jPSXdec; not started); (4) stress saves (needs
  `save.py` / unit record layout; longest names, full lists, max numbers) with menu sheets passed; (5) UI warp shots
  not yet given verdicts: im_next, option, gameover, credits, credits_late, battle05, card_k01/05. Still unconfirmed from the
  b6f1 chunk 002: battle forecast row 2 dots where the JP has ⅠⅡ (ev05_sheet_16 t4): check at full resolution.
  Visual QA: read sheets via the visual-qa subagent or `codex exec` (quota back 2026-11-26) where the dispatch
  allows; a main-thread pass costs ~600 images of context.
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
- **Open bugs:** none open. Fixed 2026-11-22: (8) unit box Lv., (9) end-turn count overdraw, (10) title card-screen
  font copy (session 7); (7) glyphs past the 80th drawn dim (session 6); (4) intro scroll left on screen, (5) one-word last lines, (6) class
  over "Lv." (session 3), militiaman speaker label (session 4); all re-checked on the tour sheets. Closed 2026-11-22: (1) the fixed-slot screen 0x8011C178 (slots 0x180-0x1FF) is a
  battle-test setup screen (labels 味方 右側 / 敵 左側, mode 11 state 0 of 0x8011A4F8); the real map confirm and
  enemy-phase counter screens use the running counter (0x800C6Bxx) and slots 0x180-0x1FF stayed empty through a
  whole battle (`work/qa/confirm_battle`): left as is. (2) map after a battle: clean (`work/play/confirm/0014.png`).
- **Waiting on the user:** nothing.

Warp sweep (original disc, 2026-11-21): `warp_all.py --states` 123/123 scenes reached from a cold boot, every
proof shot non-blank and eyeballed by sheet (events show dialogue, all 37 chapter cards incl. branch cards 1/5,
battle maps, battle VS intro, intermission pages, save/load, option, game over, staff roll, title menu); 56
states in `work/states/`. PCSX-Redux exited 1 mid-run on 2 of 51 runs with 3 parallel instances: `--retry`
(default 2) re-runs those; `--resume` keeps passed runs. A full sweep takes ~40 min at `--jobs 3`.
