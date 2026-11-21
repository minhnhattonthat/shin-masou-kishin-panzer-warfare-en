# Graphics-text survey

Tools: `tools/tim.py FILE --out work/gfx/tim/FILE` (finds + decodes every TIM, first CLUT), then
`tools/montage.py work/gfx/tim/FILE --out work/gfx/sheets/FILE --per 60 --cols 10 --thumb 128x96` (labelled
contact sheets; label = file offset of the TIM). TIM counts: T_TIM 52, TIM 441, BAT_TIM 146, GRA5 615.
None in OVER.BIN / BAT_OVER.BIN / exe (headers found there were false hits).

| # | Element | Where | Seen in game | Action |
|---|---|---|---|---|
| G1 | Prologue scroll text, 5 pages (『ア・ゼルス』…) | T_TIM 0x000000, 0x008800, 0x011000, 0x019800, 0x022000 (verified on screen, `work/qa/newgame/f000720.png`) | new game | redraw in English |
| G2 | Title logo 真魔装機神 + PANZER WARFARE | T_TIM 0x079000 / 0x0A1800 | title | keep (no official English logo, D5) |
| G3 | Title buttons START/LOAD/CONTINUE/OPTION, PRESS START BUTTON | T_TIM 0x0CA000 | title | already English |
| G4 | "Game Over" | T_TIM 0x175000 | — | already English |
| G5 | Menu sheet with Japanese labels (ユニット能力 …) and help-bar text (ここまでのデータを…) | T_TIM 0x19D000 | not yet | redraw |
| G6 | Option-screen sheet: Japanese labels and help text | T_TIM 0x1EF000 | not yet | redraw |
| G7 | World map parchment (place names?) | T_TIM 0x107800 | event intro map | check zoomed; redraw names if Japanese |
| G8 | Chapter title cards (e.g. 魔装騎士 over the logo) | unknown file (GRA5/TIM?) | chapter 1 start, `work/qa/ng5/f001350.png` | redraw all chapter cards |
| G9 | Battle weapon-menu header 攻撃技 (labels POWER/HIT/RANGE/AREA/PRANA, NAME/DATA already English) | unknown (BAT_TIM / TIM?) | `work/states/battle_weapon_menu.sstate` | redraw |
| G10 | Opening FMV burned-in subtitles (夢と希望をのせ…, 熱き想いが未来をかえる！) and the Cybuster TV-series ad | MOV.STR | boot attract | subtitle/replace frames (platform-ps1 §FMV) |

**Still to survey (phase 1 not done):** read the contact sheets `work/gfx/sheets/TIM.BIN_01-08.png`,
`BAT_TIM.BIN_01-03.png`, `GRA5.BIN_01-11.png` and zoom any sheet with Japanese; list the MOV.STR movies
(jPSXdec) and which carry text; find G8/G9 sources.
