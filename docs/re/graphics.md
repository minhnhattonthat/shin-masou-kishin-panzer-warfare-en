# Graphics-text survey

Tools: `tools/tim.py FILE --out work/gfx/tim/FILE` (finds + decodes every TIM, first CLUT), then
`tools/montage.py work/gfx/tim/FILE --out work/gfx/usheets/FILE --per 40 --cols 8 --thumb 200x150 --unique`
(labelled contact sheets of byte-distinct TIMs; label = file offset). TIM counts (unique): T_TIM 52 (49),
TIM 441 (230), BAT_TIM 146 (107), GRA5 615 (422). None in OVER.BIN / BAT_OVER.BIN / exe.
VRAM dumps: `emu.py ... --script $SKILL/scripts/lua/probes/ppudump.lua`, render with `tools/vram.py` (`--mode 4`
for 4bpp pages). Movies: `tools/str_movies.py --every 3` (cuts MOV.STR out of the .bin, ffmpeg frames).

**Static sweep done 2026-11-21** (every unique TIM of the four files read in sheets; GRA5's 239 128x128 TIMs at
0x904800-0xD69800 are all character portraits, skipped after one sheet). Duplicates: an edit must be applied to
every byte-identical copy (TIM.BIN repeats per-stage bundles; GRA5 0x0-0x22000 repeat BAT_TIM / TIM sheets).

| # | Element | Where (file offset of TIM) | Seen in game | Action |
|---|---|---|---|---|
| G1 | Prologue scroll text, 5 pages (『ア・ゼルス』…) | T_TIM 0x000000, 0x008800, 0x011000, 0x019800, 0x022000 (verified on screen, `work/qa/newgame/f000720.png`) | new game | redraw |
| G2 | Title logo 真魔装機神 + PANZER WARFARE; also BAT_TIM 0x26000-0x98000 (5 battle-intro backdrops), 0x50C000/0x532000 (NOW LOADING screens), GRA5 0x90800/0x16E2800 | T_TIM 0x079000 / 0x0A1800 | title | keep (D5: no official English logo) |
| G3 | Title buttons START/LOAD/CONTINUE/OPTION, PRESS START BUTTON | T_TIM 0x0CA000 | title | already English |
| G4 | "Game Over" | T_TIM 0x175000 | — | already English |
| G5 | Menu sheet: ユニット能力 … help bar ここまでのデータを保存します | T_TIM 0x19D000 | not yet | redraw |
| G6 | Option screen: Japanese labels + help text | T_TIM 0x1EF000 | not yet | redraw |
| G7 | World map parchment, small label bottom left | T_TIM 0x107800 | event intro map | zoom, redraw label if Japanese |
| G8 | Chapter title cards, 37 TIMs (魔装騎士, 再試験, 神の腕 … 輝ける明日へ, 野望のはてるとき 前編/後編) | GRA5 0x1860000-0x1992000 every 0x8800 (list: 1860000 1868800 … 1992000) | chapter 1 start, `work/qa/ng5/f001350.png` | redraw all |
| G9 | Status / spirit sheet: ステータス 操者 機体 攻撃技, spirit commands 熱血 閃き 集中 根性 努力 必中 信頼 鉄壁 ??? ド根性 P回復 呪縛 魂 撹乱 友情 愛, 格闘 射撃 せりあい 命中 回避 きり払い 運 精神 プラーナ回復, HP 装甲 移動 反応 適応 空 地 水, 残りポイント, ○ボタンで決定 | TIM.BIN 0x0A5128 (+34 identical copies, e.g. 0x103CE0, 0x172928, 0x1D9704) and GRA5 0x22000 | battle weapon menu (`battle_weapon_menu.sstate`) | redraw (all copies) |
| G10 | FMV: only **mov01** (Cybuster TV-series advert, 30 s) has burned-in text: 夢と希望をのせ起ち上がれ、戦士たち！, 熱き想いが未来をかえる！, end card 魔装機神サイバスター VIDEO・LD・DVD シリーズ・スタート!! 発売元:バンダイビジュアル. mov02-mov11 are CG with no text; mov12 (opening, 123 s) has only the game logo (真魔装機神 PANZER WARFARE, kept per D5; 1-s steps checked 2026-11-23) | MOV.STR sectors 0-4554 (12 movies, `tools/str_movies.py`) | boot attract (plays before the Banpresto logo) | **Done 2026-11-23:** `tools/fmv.py` + `gfx/fmv/subtitles.tsv`: frames 171-213, 251-300, 419-455 get the JP glyphs filled from their surroundings, a blurred dark band and the English (Nunito 900), re-encoded by its own MDEC v2 encoder (jPSXdec could not be run here) at the frame's qscale (+1 at most) into the frame's own sectors. Every frame ends with the 10-bit code 0x1FF after the last EOB: without it the game freezes on the frame (ffmpeg doesn't care). `fmv.py parse` checks the VLC table on all 5751 disc frames. Cached in `build/fmv_cache/` (first build ~4 min). Proof `work/qa/gfx_proof/fmv_mov01_*` |
| G11 | Map command / info sheet: 移動 飛行 着陸 精神 待機 データ システム 攻撃 浮上 潜水 能力 終了 目的 セーブ, 地形情報 地形効果, HP:位置:精神P:空中 地上 水中, 朝/昼/夕/夜 ターン数, 光の日 闇の日, 精神ポイント, 命中率, はい いいえ, 攻撃 受け 正面 側面 背面 戦闘アニメ ON OFF, 戦闘開始 武器 回避 防御 | GRA5 0x11000 (in VRAM at x=832,y=256 during events) | map phase | redraw |
| G12 | Battle UI: ダメージ クリティカル 防御ダメージ 斬り払い つばぜりあい (also an 8px ASCII font, VS) | BAT_TIM 0x499800 | battle | redraw |
| G13 | Battle reaction labels, 16 TIMs: 回避 斬り払い つばぜり 防御 バリア 被弾 格闘+回避/防御/バリア/被弾, 後+…, 後、格闘+… | BAT_TIM 0x15E2000-0x1661800 every 0x8800 | battle; **never drawn on either tour** (JP 596 / EN 558 sheets) nor uploaded to VRAM through battle05 or with Battle Animation OFF (ppudump + `tools/debug/vram_find.py`): waived in phase 8 | redrawn (gfx/battle.tsv), preview-checked only |
| G14 | Loading screens: 0x45A000 dev build card (第1制作チーム, Version 0.01 1998/12/7, 真 魔装機神 logo, Now Loading...); 0x4D5000 真・魔装機神 + オーバーレイファイル 読み込み中... | BAT_TIM 0x45A000, 0x4D5000 | not yet (0x45A000 likely unused) | check if shown (phase 8); redraw small text, keep logo |
| G15 | Event location caption: バルツフィーム王国 / 魔装騎士叙任試練 会場 (only one such TIM: other captions may be font-drawn) | GRA5 0x76800 (160x40) | in VRAM 768,256 from f2700 to f6600 of ev01 but **never drawn** on either tour (JP/EN, every event): waived in phase 8 | redrawn (gfx/story.tsv), preview-checked only |
| G16 | Intermission menu: 12 character-name buttons (ケイゴ アルマ イェン? … ), INTERMISSION/SAVE/LOAD/STATUS/NEXT (English), help bar ◁▷選択 ✕戻る ○決定 | GRA5 0x1740800 | intermission | redraw names + help bar |
| G17 | Save/load UI (SAVE LOAD NEW DATA NO OK YES SLOT FREE BLOCK Information GAME DATA SYSTEM): English; check the faint SYSTEM label | GRA5 0x1751800 | save screen | zoom check only |
| G18 | Staff credits, 8 TIMs of Japanese names/roles (+ "Fin", English) | GRA5 0x1B64000-0x1B9F800 every 0x8800, 0x1BA8000 | ending | redraw (D3: English credits) |
| G19 | Font sheets (not graphics text): 12px JIS font pages BAT_TIM 0x480000 / 0x488800 (= GRA5 0x0 / 0x8800); 8px font BAT_TIM 0x43F000, 0x447000 (ASCII), 0x451800 | see `font.md` | everywhere | font work in phase 5 |

Not text: unit sprites (Latin direction letters only), terrain, backgrounds, portraits, mecha cards (GRA5 0x175A000+),
effects, Banpresto logos, BAT_TIM 0x4A2000/0x4B1000 (Gundam Wing art, no text).

Still open: the tour side of the survey (marker build, phase 5/8) and warps to mid-game screens (phase 2) may
show font-drawn or VRAM-built text not in this list.
