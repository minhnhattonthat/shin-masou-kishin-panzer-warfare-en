# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-21 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's standing answer for one-shot runs. |
| D2 | 2026-11-21 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist (Super Robot Wars / Cybuster official romanizations), else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-21 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-21 | Abbreviations | engine work first (default), abbreviate | Engine work first (default); abbreviate only as a flagged last resort. |
| D5 | 2026-11-21 | Graphics text left in Japanese | none (default), list | Translate all (titles, menus, banners, cards); keep the Japanese logo only if no official English version exists. |
| D6 | 2026-11-21 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. |
| D7 | 2026-11-21 | Existing saves / memory cards | use user's, none | None provided; build the debug tool as usual. |
| D8 | 2026-11-22 | Dialogue quote marks (the font has only closing ” ’) | keep "..." (looks closing-only), drop 「」 | Drop 「」 in dialogue (speaker label shows who talks); thoughts in (); 『』 terms capitalised, no quotes. Default chosen under D6 pre-approval. |
| D9 | 2026-11-22 | Names with no official English | Hepburn, Akurasu wiki forms | Akurasu wiki forms where it has them (Vartzpheem, A-Zeluth, Zeldna, Thodd, Kurtz/Zants middle names), SRW official mecha names (Cybuster, Zamzeed, Granveil, Gaddess), else Hepburn. Extends D2. |
| D10 | 2026-11-22 | Register | modern, archaic | Natural modern English, light medieval-military flavour; no thee/thou unless the JP is archaic. |
| D11 | 2026-11-22 | Bulk consistency rewrite (`tools/harmonise.py`, commit bf76a07) | leave variants, harmonise | Harmonised under D6: one EN per repeated JP line + speaker by majority (204 ids, `work/tl/b101.tsv`). It spread two misreads (Toto's アリ cry, HQ caption) that review caught and fixed. Any re-run goes through the batch check and a reviewer. |
| D12 | 2026-11-22 | Translation pilot (insert + boot one English batch before wave 1) | pilot, skip | Skipped under D6; the wide-marker tour covered box widths. Style-reference samples are translator-written, not user-approved. |
| D14 | 2026-11-22 | Memory-card save titles 真・魔装機神ＤＡＴＡ０１-１５ (BIOS card manager, Shift-JIS, 24-byte field = 12 full-width chars) | ASCII English (garbage in the BIOS), full-width abbreviation (Masou DATA01), keep JP | Keep Japanese (`script/keep_jp.txt`): "Masoukishin" + two digits doesn't fit and the glossary forbids the short form; only the BIOS shows it. Default under D6. |
| D13 | 2026-11-22 | Same weapon, two names in exe lists | Blast/Havoc Beam, Caloric V/Buoy | Havoc Beam, Caloric Buoy (no official forms; Buoy reads as an object next to Caloric Bomb). Default under D6. |
