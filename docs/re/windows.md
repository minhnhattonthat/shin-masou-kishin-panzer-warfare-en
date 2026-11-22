# Text windows and width budgets (width gate, phase 5)

Budgets are pen advance in px of the English VWF (`tools/font.py width_px`, includes each glyph's 1 px gap) and
sprite glyphs (`font.glyphs`: drawn characters, spaces excluded). Tag: measured (shot) or guess. `tools/lint.py`
checks the measured rows (msg, scroll, choice, battle quotes); exe/overlay fields are checked against their byte
`max` and counted as unmeasured px.

| Variant | Budget | Lines | Glyphs | Status / evidence |
|---|---|---|---|---|
| Event dialogue, portrait box (msg with speaker) | 240 px per line from x=68 (interior to x=311) | speaker + 3 (a 4th line is cut by the box bottom) | 140 per message incl. speaker | measured 2026-11-22: `build.py --marker --only battle` + `--qa ev000_1444=` lines of 237/244 px; 244 touches the border; `work/qa/w_z.png`. Wide marker (every line filled to 240 px, `marker3`) renders in all 35 stages |
| Location caption / narration (empty speaker, emblem icon) | 240 px (same box, x0=68) | 3 | 140 | measured (caption ev000_1420 with 2 × 50 n: same x0 and right edge) |
| Chapter-intro scroll pages (68, shown after intermission NEXT) | 256 px, centred by insert.py (axis x=160, left x=32) | the JP page's line count (13/14 incl. blanks); insert pads | 499 drawn fine | measured 2026-11-22: `--qa ev03E_520C=` 13 lines of 256 px + "\|ABC" (272 px): all 13 lines and the ABC tail show (`work/qa/qa_next/f004080.png`); 256 keeps a 32 px margin each side |
| Choices (21, op 0x0001) | 228 px per option from x=68 (the highlight bar ends at x≈296) | the JP's option count (2-3) | 140 | measured 2026-11-22 on the original: same box as dialogue, `work/qa/ch3/final.png` (state `work/states/ev01_choice1.sstate` + one circle); `{h}【…】` lines are centred by full-width spaces in the JP |
| Battle quotes (battle_A/B), box between the two portraits | 188 px per line from x=64 (right portrait frame at x≈260) | 2 (a 3rd line touches the box bottom) | — | measured 2026-11-22: `--qa bqA_31_098=` 3 rulers of 192 px + "\|ABC" (`work/qa/qa_bq/f015300.png`): the \| sits at x≈250, ABC runs into the portrait |
| Intermission header: chapter label (overlay.json `ov_*`, 「…」まで終了) | 200 px from x=115 (the box runs to the screen edge) | 1 | — | measured: marker `[ov_ECBF4]The quick brown fox j` (207 px) clips the j at x=320; ≤ 31 bytes in place. Save-slot list copy of the label: not measured (needs a save made by the patched build) |
| Save/Load Information box (exe_B3BA4 etc.) | 268 px from x=25 | 1 (JP) | — | measured from the marker shot (box interior x 25-295); the byte `max` (27) binds first |
| Status page: pilot name (exe_01900, 31 bytes) | 188 px from x=83 | 1 | — | measured: marker fills the field to x≈272 (`im_status_pilot`) |
| Status page: mech name (exe_01D80, 23 bytes) | 168 px from x=36 | 1 | — | measured: field divider at x≈207 (`im_status_mech`) |
| Status page: weapon name (exe_01310, 11 bytes) | 157 px from x=42 | 1 | — | measured: inner field ends x≈199, PRANA label after (`im_status_weapons`) |
| Battle screen: name labels (top bar: mech tables exe 0xC52F8 / 0xC539C; bottom bar: pilot tables 0xC5440 right, 0xC5554 left) | mech 100 px; pilot 60 px (bottom-right box x=250-310, the binding one); 12 glyphs each | 1 | — | measured 2026-11-22 (`battle05`, `work/qa/hud_probe`). §Battle HUD slots. lint.py `TABLES` |
| exe menus in general (700 pointer strings, spirit / objective / status records) | ≤ `max` bytes in place; px per field as above | — | — | the in-place byte `max` (the JP length) binds before px for most fields; English names longer than the JP bytes need relocation (pointers and lui pairs are known: `ptrs`/`lui` in exe.json) |
| mcard titles (exe region `mcard`) | keep Shift-JIS full-width | — | — | shown by the BIOS card manager: kept Japanese (D14, `script/keep_jp.txt`: DATA01-15, the system title, the save-data line) |

Notes
- Glyph torture line (`tools/debug/torture.py`, boxes ev000_1444 + ev000_1478, 2026-11-22, `work/qa/torture_z1.png`,
  `torture_z.png`): all 95 printable ASCII render, distinct, with double spaces kept. Quirks from the game's
  full-width cells: `"` draws as a closing ” and `'` as ’ (no opening forms), `` ` `` as ‘, `_` is 12 px wide,
  `...` draws compact. Style choice for phase 6: straight quotes look closing-only.
- Glyph slots: each window frees only its slot count on close; text over the count leaves stray glyphs that stay on
  screen (seen as grey "er the l" in the first marker build). `tools/slots.py` raised the count 80 → 140.
- **Battle HUD slots** (2026-11-22): 0x80102D90's a0 is the first glyph slot; each drawn glyph takes the next one
  (spaces and control letters take none). Battle labels (0x80119100-0x801191B0) drew at bases 0x10 (top-right mech,
  x=+16), 0x18 (top-left, x=-112), 0 (bottom-right pilot, x=+90), 8 (bottom-left, x=-150): 8 slots each, so "Tilwes"
  lost "Tilw" to the bottom-left label's 9th-12th glyphs. Quote box: base 0x20, freed 0x20 at a time
  (0x80119540, 0x80119684). `tools/slots.py` WORDS moves the mechs to 0x70 / 0x7C, the bottom-left pilot to 0x0C and
  frees 0x48 quote slots. Same pattern still open (phase 8, no warp scene yet): 0x801167DC/0x8011681C (mech names at
  0x10/0x18) and the attack-confirm screen 0x8011C35C-0x8011C620 (pilot 0x188, mech 0x180, weapon 0x190 x16, right
  side 0x1A0/0x1A8/0x1B0, items 0x1C0-0x1F8; each FREE(base, n) before its DRAW): English pilots up to 10 glyphs,
  mechs 10, weapons 19 overflow there.
- **Confirm screen** (map attack confirm, 2026-11-22): pilot names via table 0x8014E010 (exe 0xA8810, index = unit
  byte +0x4C) drawn at x=-142 (left, 0x800C6BFC) / x=+10 (right, 0x800C6C2C), y=-62; the "Lv." graphic sits at
  screen x=82 / 242, so 64 / 72 px. asm/vwf.asm `pilot_short` (0x8016DB80) swaps long class names for
  `script/confirm_short.tsv` forms there only (D18). The table's other user, the map unit-info box (0x800E2DF4,
  x=-38), has ~81 px.
- **Intro scroll slots**: pages draw from slot 0 (0x80115998 / 0x80115A10, renderer x=-128 y=-88) and freed 0xC8;
  English pages draw up to ~336 glyphs, so `slots.py` frees 430 there (bug 4).
- Glyphs fade in during the typewriter (late glyphs look grey in mid-typing shots): judge a box on its last frame.
- **Bug 7 (fixed 2026-11-22): glyph 81+ of a message stayed grey.** Slot records (*0x801B7184 = 0x8017BC78, 0x44
  each), colour bytes +0x0C/+0x20. Layout (0x80103B44, from the renderer 0x80102D90) writes 0x80; right after,
  0x80115B4C(active window) dims the other windows via 0x80103AA8(start, end exclusive, 0x404040) →
  0x80104388, with the OLD ranges as immediates (10/0x5A/0xAA/0xFA). `slots.py` WORDS re-aims them at the new ranges
  10/150/290/430. Found with `who_writes.lua` on slot 90's colour (ALL=1, cold boot ev01 KEEP=1). Verified ev01
  ev000_14C0 "...face your final exam" (`work/qa/b7_fix/f003550.png`). Other 0x80104388 callers (0x800C5710,
  0x800DD1D0/368, 0x800FB900/914) take their ranges from records, not constants.
- **Event pools: solved by block growth** (scripts.md §Block growth): strings past a pool's end go after the block,
  blocks move to the end of OVER.BIN, max 0xF800 per block. The wide marker (each body line 240 px) needs at most
  25 sectors (0xC800). So translators get px/line budgets only, no byte budget for events.
- **Battle quote areas are full** (RAM slot 0xC60 bytes: the exe's slot table at 0x800AB7B8 = 0x801D79EC,
  0x801D864C, 0x801D8800, 0x801DA5A0; set A's slot is 0x801D79EC-0x801D864C). Markers stay ≤ JP bytes. Engine task
  before phase 7: move the quote slots to bigger free RAM during battle (candidate: the event slot tail
  0x801CB118-0x801D1D18, which the battle-transition image (0x8C00 bytes from 0x801C2518, code 0x800E95B8) leaves
  alone; trap-test it) and relayout BAT_OVER like OVER.
- Text drawn as graphics seen on the marker tour (not font text, phase 8 redraws): status tabs and labels, skills
  (せりあい Lv. …) and spirit grid (G9), option screen labels and help (G6), staff roll (G18).
