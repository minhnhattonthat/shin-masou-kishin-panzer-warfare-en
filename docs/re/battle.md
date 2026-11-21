# Battle text and exe text

## BAT_OVER.BIN battle quotes — verified (static)
- Quote blocks are listed by two u16 sector tables in the exe (0xFFFF-terminated, consecutive entries = [start, end)
  sectors): **set A** at exe 0xAFD20 (RAM 0x80155520): sectors 0x0-0x4A, 65 blocks; **set B** at exe 0xAFE66
  (RAM 0x80155666): sectors 0xB6-0x100, 65 blocks. Each block is 1-2 sectors (max used 0xC5E bytes).
- Block layout: `u32 block id` (0x41.. in A, 0x90.. in B; 0x45 / 0x94 = a shared 64-string default block used by
  many slots), then NUL-terminated Shift-JIS strings padded to 4 bytes (`\n` = line break), then 12-byte records
  `u32 kind, u32 RAM pointer to string, u32 quote id` (e.g. 0x3F6, 0x61F).
- **Load addresses**: set A blocks at RAM **0x801D79EC**, set B at **0x801DA5A0** (two slots, attacker/defender
  guess). Proof: every record pointer lands on a string start with these bases (2062 records per set, 1 odd record,
  0 unreached strings; `python -X utf8 tools/batquote.py` re-checks it and exits 1 on any unreached string).
- 2061 strings per set; 52 of 65 blocks have the same text in A and B.
- So a block can be repacked freely: rewrite strings, recompute record pointers. Size limit per block: the sector
  table (growing past its sectors shifts every later entry) and the RAM gap 0x801DA5A0 - 0x801D79EC = 0x2BB4 for set
  A; what follows set B's slot is not yet known.
- Not yet traced at runtime (needs a battle from the debug tool, phase 2): which code picks the record by quote id.
- Other sector lists near it (exe 0xAFD02 `0 43 86 9B …`, 0xAFDA6 `4A … 8B`, 0xAFE2C `8B … B6`, 0xAFF72
  `141 … 171`) are battle code/data overlays.

## Exe (SLPS_023.19) — verified for direct pointers
- Strings (unit, weapon, attack names, menus) are Shift-JIS, NUL-terminated, 4-byte aligned. `tools/re.py` counts
  which strings are reached by u32 pointers (RAM = 0x800A5800 + file offset) and which by lui+addiu/ori pairs:
  - 0x800-0x10000: 452 strings: 402 u32 pointer, 45 lui pair, 1 neither (`　ＹＥＳ　` at 0x4064).
  - 0xA0000-0xD0000: 240 strings: 103 pointer, 6 lui pair, 131 neither. The "neither" are **fixed-size record
    fields** reached as base + index * stride: spirit names (0xBC stride, 0xAD090…), stage objectives (0x94 stride,
    0xAD684…), save names 真・魔装機神ＤＡＴＡ０１.. (0x64 stride, 0xB4980…), status labels (0x5C stride, 0xB7730…).
    Write only the string bytes inside each field (flag bytes may share the record).
  - **109 battle quotes 「…」 in the exe** at 0xC3DC8-0xC4CB0 with no pointer or lui reference: reader unknown (index
    table or sequential scan): trace in phase 4.

## OVER.BIN overlays (sector 0x1A0+) — guess
- Code/data overlays. Text: ~1.1 KB, e.g. save-slot chapter labels 「魔装騎士」まで終了 at 0xECB74 (30-byte fixed
  fields).
- During event 1, OVER.BIN 0xDD800-0xE8800 (sector 0x1BB+, mostly data) sits at RAM 0x801CA518-0x801D5518, i.e.
  directly after the 0x8000-byte event block 0 (see scripts.md §Free space).
