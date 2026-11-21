# Battle text and exe text

## BAT_OVER.BIN — partly guessed
- Starts with battle quotes: u32 0x41 at 0x0 (guess: count), then NUL-terminated (4-byte padded) Shift-JIS lines,
  e.g. 0x4 「も、もう、動けねぇ…クッソォッ！」. Quote text in 0x0-0x28000 and 0x58000-0x80000 (~79 KB total).
- No direct u32 RAM pointer table found by `tools/ptrbase.py` (no base explains more than noise): quotes are likely
  indexed (count + sequential scan or offset table). Find the reader with a read watch in phase 4.
- Exe u16 sector table for BAT_OVER just before the event table (…16E 16F 170 171 FFFF).

## Exe (SLPS_023.19) — verified for direct pointers
- Strings (unit, weapon, attack names, menus) are Shift-JIS, NUL-terminated, 4-byte aligned.
- 368 of 406 string starts in 0x0-0x10000 are hit by u32 pointers with base 0x800A5800 (= t_addr - 0x800).
  The rest are likely `lui/addiu` pairs: check with capstone in phase 4.
- More text at 0xA0000-0xD0000 (~8.9 KB).

## OVER.BIN overlays (sector 0x1A0+) — guess
- Code/data overlays (sector 0x1A0 block loads at 0x801C2518 too, seen in the new-game RAM dump). Text: ~1.1 KB,
  e.g. save-slot chapter labels 「魔装騎士」まで終了 at 0xECB74 (30-byte fixed fields).
