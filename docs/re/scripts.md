# Event scripts (OVER.BIN sectors 0x000-0x19F)

Tool: `tools/over.py OVER.BIN` (block list, message commands).

## Blocks — verified
- 35 blocks; sector list in the exe (disc.md). Each block header: byte 0 small, bytes 1-3 = 0, bytes 8-11 = `06 00 00 00`.
- Every block loads at RAM **0x801C2518** (verified: RAM dump during the first event, block 0 = file 0x0-0x8000 at
  0x801C2518; state `work/states/event1_start.sstate`). Largest block 0x18D-0x1A0 = 0x9800 bytes. What lies after the
  slot in RAM (the hard size limit) is not yet known: check before growing a block.

## Text pool — verified
- Encoding: plain **Shift-JIS** (cp932), full-width; decoded strings match the screen (Zeldona's lecture, frame
  `work/qa/ng4/f000400.png`).
- Each block has one contiguous text pool after the command header area (block 0: 0x1420-0x4688). Strings are
  `speaker\n` + `　line\n` (up to 2-3 lines, each starting with a full-width space) + `\n` terminator(s), then NUL
  padding to a 4-byte boundary. Narration has an empty speaker (string begins with `\n`). Thought lines use （…）.
- `【…】` appears in choice text (e.g. `【最初の選択にもどる】`).
- 7640 strings in the 35 pools, ~338 KB.

## Pointers — verified
- Commands are 16 bytes: u16 op, u16 a, u32 b, u32 c, u32 d. Strings are referenced by absolute RAM pointer
  (0x801C2518 + offset in block) in word c:
  - op 0x0384 (high half 0/1/2 = variant, e.g. portrait side): message; word b = flags (0x80 seen). 7619 strings.
  - op 0x0001: choice / alternate message (21 strings), pointer also in word c.
- So the whole pool can be repacked and every pointer rewritten; nothing else points into the pool (coverage script:
  every string start in every pool is reached by one of the two ops).
- Two pointer words sit just before each pool (block 0: 0x1418 → 0x801C38B0, 0x801C38E0, into the command area):
  not text; leave them. The first string after them (the location caption, e.g. `\n　バルツフィーム王国\n　　王都`)
  is a normal op 0x384 message but has **no NUL before it** (it follows the pointer word): don't look for strings
  only after a NUL (31 of the 7640 messages are like that).

## All text in an event block — verified (phase 4, `tools/extract.py`, `tests/test_extract.py`)
Every aligned u32 word in a block that holds a RAM pointer to a text string, grouped by what precedes it:
- 7619 messages (op 0x384, word c) + 21 choices (op 0x0001) = 7640 distinct strings, one pool per block. All end
  `\n`; the box is speaker line + 3 body lines (empty lines pad), up to 6 for choices. 45 speaker names (98 narration
  strings have an empty speaker). `h` (highlight start, see font.md) appears in two choices.
- **Chapter-intro scroll**: 2 pages per block (68 strings), each one multi-line string near the block end, reached by
  a 2-word pointer table right after them (block 0x10: pages at 0x5AAC/0x5C10, table 0x5DA0). A u16 table just
  before the first page (0x5A92: `0 FA 122 12C 140 …`) looks like per-line timing/positions (guess): check it in
  phase 5 if English changes the line count. So the prologue scroll is font text, not a picture.
- 3 `ダミー` (dummy) strings in block 0 (0x7E5C-0x7E6C, table 0x7E74): placeholders, keep as is.
- After the message pool comes more command data (`9C FF 0E 00 …` with pointers to 0x801C251C): the pool can't grow
  in place past its end; repacking within it is free. Pool bounds per block are in each `script/events/*.json`.

## Free space — candidates (guess until a trap test passes)
- Event slot: RAM dump during event 1 (`work/qa/ev_ram`, block 0 = 0x8000 bytes) shows OVER.BIN 0xDD800-0xE8800
  (sector 0x1BB+, mostly data, few `jr ra`) loaded right after the block at 0x801CA518-0x801D5518, then zeros to
  ~0x801E2000 (where battle quote slots 0x801D79EC / 0x801DA5A0 live during battles). Guess: a load heap that
  follows the event block, so a block may grow if that follow-on load is placed by size; else the hard limit is the
  largest block (0x9800). **Test in phase 4/5**: pad block 0 by 0x1000, rebuild, boot event 1, compare shots.
- Repacking a pool never moves the command area: pools come after the commands and only op 0x384/0x0001 words
  point into them.
- Exe zero runs (candidates only, may be live BSS-like buffers): file 0xC7F40-0xC8580 (0x640), 0xCB135-0xCC1A0
  (0x106B), tail 0xD29DC-0xD3000 (0x624, RAM 0x801781DC-0x80178800 = end of exe image).
- Disc: OVER.BIN / BAT_OVER.BIN blocks are addressed by u16 sector tables in the exe (disc.md), so a grown block
  means rewriting the tables; files can grow on disc because mkpsxiso relays the layout (LBA-based states go stale).

## Box size (from screenshots)
- Dialogue box: speaker line + up to 2-3 body lines, ~17-19 full-width glyphs (~12 px each) per line in a ~250 px box.
  Width gate still to be measured in phase 5.
