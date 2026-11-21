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
- 2061 strings per set; **all 65 blocks have the same text in A and B** (same strings in the same order; only the
  record pointers differ by the base), checked by extract.py: set B lines carry `same` = the set-A id.
- **Runtime (verified 2026-11-22, `battle05` + watch.lua)**: per battle the game CD-loads, in order, set A's block
  to 0x801D79EC, unit data to 0x801D864C and 0x801D8800, set B's block to 0x801DA5A0, more to 0x801DB200 (load
  addresses = the exe's word table 0x800AB7B8, file 0x5FB8..). A 2-sector block spills past 0xC60 and is overwritten
  by the next load, so each slot really holds 0xC60 bytes. Records are not found by scanning: the quote picker
  (0x801194C0-0x801195E0) reads a **static exe table of 65 x 12-byte entries per set, +4 = the block's first record**:
  set A RAM 0x8016B1D8 (file 0xC59D8), set B 0x8016B4E4 (file 0xC5CE4); record = kind (lh), string ptr, quote id (lh
  at +8). Odd record: block 0x20/0xD6 +0xA10 (kind 0) aims past the strings at bytes `02 00`.
- **§Relocation (phase 7, tools/insert.py `BQ`)**: every quote block is rebuilt (id, strings, records) for a new
  slot in the event-slot tail, A 0x801CB118, B 0x801CE718 (≤ 0x3600 each), appended to the end of BAT_OVER.BIN set
  by set; the sector lists, the two load-address words and the record-pointer tables follow. That RAM has no writes
  from map load through a battle and back (trap f7700-f20000); the event block is CD-reloaded after every battle
  (the transition image already overwrites 0x801C2518-0x801CB118). English quotes render from both sets (shots
  `work/qa/bq_en/zoom.png`).
- **Exe strings longer than their slot** (insert.py `_relocate`): a pointer/lui string gets only the JP string's own
  4-aligned slot (the zero bytes extract's `max` counts past it may be zero-init variables); longer ones best-fit
  into slot tails, the old slots of moved strings and 0x8016DA60-0x8016DC3F (after asm/vwf.asm). **Not** the exe
  zero run 0x80170935-0x801719A0: live BSS (library code 0x80137xxx writes it at boot); strings there gave a black
  screen from frame 0. `tools/writes_check.py` (run by build.py) checks every changed byte is in a planned range.
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
    table or sequential scan). Phase 4: no u32 word and no lui pair points anywhere in 0xC3C00-0xC4D00, and one
    quote names しんご, who is not in this cast: guess, unused leftover. The marker build (phase 5) shows whether any
    appears.

## Exe extraction (phase 4) — verified by tests/test_extract.py
- 900 strings in `script/exe.json`: 700 reached by u32 pointer or lui pair, 200 in record regions with no pointer
  (`EXE_REGIONS` in extract.py: yes 5, spirit 32, objective 16, mcard 17, status 21, quote 109).
- Strings are not always 4-aligned and don't always follow a NUL: some start right after a pointer table (e.g.
  0xD38 アストラルカノン) or after one NUL inside a packed list. Text bytes: SJIS pairs, `\n`, half-width space 0x20
  (objectives pad with it), control letters `b h m r w z` (`h`…`z` = highlighted span, `b` prefixes some menu lines).
- Record regions: spirit = 0x5E-byte records from 0xACFD0 (name +4, 11 bytes; description +0xF, 0x4F bytes);
  status labels = 0x2E-byte records from 0xB7702 (text 0x20 bytes, then layout data). `max` in exe.json is the
  field size (grid) or the zero run after the string (packed lists), minus the NUL.
- Not text (waived in the coverage test): code bytes at 0x15AA8-0x162E0, u16 SJIS-code tables 0xCAB80-0xCB040,
  a mirrored-kanji data table 0xCF390-0xCFE60, 0xE0E0 fill (珥珥珥).
- OVER.BIN overlay: 37 chapter save labels at 0xECB74-0xED024 (`script/overlay.json`), reached by the u32 table at
  0xED024 (RAM 0x801C708C… = file + 0x800DA518, so guess: this overlay loads at sector 0x1D0 → 0x801C2518, the event slot).

## OVER.BIN overlays (sector 0x1A0+) — guess
- Code/data overlays. Text: ~1.1 KB, e.g. save-slot chapter labels 「魔装騎士」まで終了 at 0xECB74 (30-byte fixed
  fields).
- During event 1, OVER.BIN 0xDD800-0xE8800 (sector 0x1BB+, mostly data) sits at RAM 0x801CA518-0x801D5518, i.e.
  directly after the 0x8000-byte event block 0 (see scripts.md §Free space).
