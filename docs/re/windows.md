# Text windows and width budgets (width gate, phase 5)

Budgets are pen advance in px of the English VWF (`tools/font.py width_px`, includes each glyph's 1 px gap) and
sprite glyphs (`font.glyphs`: drawn characters, spaces excluded). Tag: measured (shot) or guess.

| Variant | Budget | Lines | Glyphs | Status / evidence |
|---|---|---|---|---|
| Event dialogue, portrait box (msg with speaker) | 240 px per line from x=68 (interior to x=311) | speaker + 3 (a 4th line is cut by the box bottom) | 140 per message incl. speaker | measured 2026-11-22: `build.py --marker --only battle` + `--qa ev000_1444=` lines of 237/244 px; 244 touches the border; `work/qa/w_z.png` |
| Location caption / narration (empty speaker, emblem icon) | 240 px (same box, x0=68) | 3 | 140 | measured (caption ev000_1420 with 2 × 50 n: same x0 and right edge) |
| Choices (21, op 0x0001, up to 6 lines) | — | — | — | not measured |
| Chapter-intro scroll pages (68) | — | — | — | not measured; u16 table before page 1 may time lines |
| Battle quotes (battle_A/B) | — | — | — | not measured (battle box, other renderer path?) |
| exe menus: weapon / spirit / status / objectives / mcard | in place ≤ `max` bytes; px not measured | — | — | not measured. mcard titles are shown by the BIOS card manager: keep them Shift-JIS (full-width) |
| Save labels (overlay.json, "…まで終了") | ≤ 31 bytes | 1 | — | not measured |

Notes
- Glyph slots: each window frees only its slot count on close; text over the count leaves stray glyphs that stay on
  screen (seen as grey "er the l" in the first marker build). `tools/slots.py` raised the count 80 → 140.
- Glyphs fade in during the typewriter (late glyphs look grey in mid-typing shots): judge a box on its last frame.
- Event pools have **no slack**: ev000's pool is full with the original Japanese, so English must not exceed each
  pool's JP byte size, or the pool must move (block growth / relocation, scripts.md §Free space). Measure the
  English-vs-pool budget before phase 6 dispatch.
