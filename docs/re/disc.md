# Disc layout (SLPS-02319)

Raw MODE2/2352, one data track; `build.py` unpacks with `dumpsxiso -x tree -s layout.xml` and repacks with
`mkpsxiso -y layout.xml` (both run in `build/disc`): byte-identical (sha1 e0b0a78b…), held by `tests/test_identity.py`.
`tools/disc_ls.py IMAGE` lists LBAs.

| File | LBA | Size | Contents |
|---|---|---|---|
| SYSTEM.CNF | 23 | 0x44 | BOOT = SLPS_023.19 |
| SLPS_023.19 | 24 | 0xD3000 | main exe, t_addr 0x800A6000 (file 0x800), so RAM = 0x800A5800 + file offset. Menu/unit/weapon names, 8.9 KB of Shift-JIS at 0xA0000-0xD0000 plus 8 KB at 0x0-0x10000 |
| OVER.BIN | 446 | 0x10C800 | sectors 0x000-0x19F: 35 event-script blocks (story text, see scripts.md); 0x1A0+: code/data overlays (some text: chapter "…まで終了" save labels at 0xECB74) |
| T_TIM.BIN | 983 | 0x259800 | TIM images (52 headers); prologue scroll text is pre-rendered (guess: here) |
| BAT_OVER.BIN | 2186 | 0xB8800 | battle overlays + battle quotes (~79 KB Shift-JIS, see battle.md) |
| BAT_TIM.BIN | 2555 | 0x166A000 | battle TIMs (148 headers) |
| SOUND.BIN | 14031 | 0x176000 | sound |
| TIM.BIN | 14779 | 0xEC2000 | TIMs (451 headers) |
| GRA5.BIN | 22335 | 0x1BBE000 | TIMs (615 headers) |
| MTEST.XA | 36539 | mixed | XA audio (voices/music) |
| MOV.STR | 60219 | mixed | FMVs; opening has burned-in Japanese subtitles |
| DUMMY.DA | 146020 | | padding |

Files are found with CdSearchFile (names in exe); inside OVER.BIN / BAT_OVER.BIN the exe holds **u16 sector
tables** (relative sector, 0xFFFF-terminated lists) around exe file offset 0xAE058-0xB0100. The event-block list is
at exe file 0xAFFE2 (RAM 0x801557E2): `0 10 1C 27 … 18D 1A0 FFFF` (**verified**: matches the 35 block headers and
RAM dump of block 0 at 0x801C2518). Growing a block means shifting OVER.BIN sectors and every table entry after it.

Space: OVER.BIN ends 3 sectors short of the last table entry (0x21C vs 0x219 sectors); the loader reads into T_TIM
(contiguous on disc). Don't append to OVER.BIN without checking that read.
