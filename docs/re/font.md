# Font and text renderer

## Dialogue/menu renderer (exe) — verified
- Read watch on the event-1 text pool (`work/states/event1_start.sstate`, `watch.lua` read on 0x801C3938-0x801C6BA0,
  `--debugger`) hits PCs 0x80102E44, 0x801032C8, 0x801032F0, 0x80103128: the string loop is the function around
  0x80102E00-0x80103170 (exe file = RAM - 0x800A5800).
- 0x8010329C decodes one character:
  - lead byte 0x81-0x98 → two-byte Shift-JIS code; 0x8140 (　) and 0x8240 are spaces (advance only);
  - codes > 0x879C take another path (0x801035C0, kanji);
  - single bytes: 0x00 end, 0x0A newline (y += 12), and the control letters `b h m r w z` (0x62 0x68 0x6D 0x72
    0x77 0x7A; effect not yet traced: colour or wait/pause guesses). Any other single byte is **skipped** (not drawn).
  - So **half-width ASCII does not render**; English needs a renderer patch (phase 5: map ASCII to new narrow glyphs,
    VWF advance). The event script uses none of the single-byte codes (scan of all 7640 strings); they occur in
    exe/menu text.
- Glyph lookup: binary search (0x80103174) over the table at **RAM 0x8015711C** (exe 0xB191C), 164 entries of 6 bytes
  `u16 first_code, u8 0, u8 row, u16 page`; each entry covers 21 consecutive codes (one font row of 21 glyphs),
  0x8140 … 0x986A (亘): all of JIS level 1. Pages 0-3 (42 rows each). After the table: `00000000 000011CE 00001C9B
  0000275F` (guess: per-page offsets/sizes of a font file).
- Glyph cell **12x12**, column = (code - first_code) * 12, drawn as textured sprites (SPRT via 0x80144684).
  Fixed advance 12 px (full-width); a 17-19 glyph line fills the ~250 px dialogue box.

## Renderer detail (phase 5) — verified by disassembly
- One string function **0x80102D90** (113 callers: dialogue, menus, everything font-drawn) loops: decoder
  0x8010329C(state=sp+0x38, sprite=sp+0x48, ptr) → type; type < 0xA: no draw; else draw sprite at
  (fp + state.x, y) via 0x80103B44; then advance: types 0xA/0xB +12, 0x14-0x17 +8. Returns glyphs drawn.
- Pen state (sp+0x38): +0 font mode (0 = 12 px, 1 = 8 px font: full-width digits, A-Z, katakana and a table at
  0x801570D4 drawn from 8x12 cells at v = 0x12*12+), +1 bytes consumed, +4 CLUT row offset (colour), +6 x, +8 y.
- Control letters (single bytes): `b` colour 4, `m` colour 0xC, `r`/`w` colour (0 / other), `h` mode 1 (8 px
  font), `z` mode 0. Codes 0x8140/0x8240 advance 12 (8 in mode 1) without drawing.
- Sprite: +0 tpage (font info word +8 + entry.tpage), +2 CLUT id (x 0x100, y 0x1E0 + entry.page + colour),
  +4 u = (code - first) * 12, +5 v = row * 12, +6 w 12, +8 h 12.
- **The font TIM is 4 glyph pages in one 4bpp image**: each CLUT row 0x1E0+page maps only bit `page` of a pixel
  to white (CLUT 0 = 0,FFFF,0,FFFF…). So the "4 pages x 42 rows" are the 4 bit planes of the two TIMs at VRAM
  x 896/960; page 0 holds symbols, digits, Latin, kana. Undefined SJIS cells (0x8259-0x825F, 0x827A-0x8280, …) are
  filled solid.

## VWF (phase 5, `asm/vwf.asm`, `tools/font.py`)
- English is single bytes: ASCII printable as itself, lowercase a-z at 0xA1-0xBA (+0x40; 0x61-0x7A keep the control
  letters), `…` 0xBF. Hook at 0x8010365C (single-byte path): byte < 0xC0 with VWF_WIDTH[byte] ≠ 0 → draw page-0
  cell VWF_CODE[byte] (SJIS code; full-width Latin/digits/punctuation) and return type 0x18 + width; the caller's
  advance (0x801030F4) adds type - 0x18. Code 0 (space) advances only. Code + tables at RAM 0x8016D740
  (exe zero run, free up to 0x8016DC3F; write-trap: `tools/debug/trap.py`).
- Glyphs: the game's own full-width Latin cells with their ink moved to the cell's left edge (bit 0 only, so the
  other 3 pages stay intact), width = ink + 1 px. Patched in BAT_TIM.BIN 0x480000 and its copy GRA5.BIN 0x0.
  Average lowercase ≈ 6.5 px. Full-width Latin in leftover Japanese text draws narrow with the old 12 px advance.

## Font data — partly verified
- 4bpp, JIS-ordered, 21 glyphs per 256-px row. TIMs: BAT_TIM 0x480000 (symbols, full-width digits, Latin A-Z a-z,
  kana, Greek, Cyrillic) and 0x488800 (kanji from 諸); byte-identical copies at GRA5 0x0 / 0x8800.
- During event 1, VRAM x=896-959 and 960-1023 (y 0-255) hold exactly those two TIMs (row bytes matched in the dump
  `work/qa/vram_ev1/ppu_000399.vram.bin`). Where the other kanji pages come from (4 pages x 42 rows in the table vs
  2 TIMs of 21 rows) is **not yet known**: guess, a font file streamed per string (see the size words after the
  table). Trace in phase 5 before replacing glyphs.
- Full-width Latin letters exist in the font (rows 0x8260-0x829A), so a first marker build can show `[id]` in
  full-width ASCII with no engine change.
- Other fonts: 8px font sheets BAT_TIM 0x43F000 (kana/ASCII), 0x447000 (ASCII 128x128), 0x451800 (kanji) — used
  by small labels (map info?), not traced.
- No BIOS Krom calls (no B0:51 stub in the exe).
