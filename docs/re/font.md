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
