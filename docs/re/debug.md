# Debug tool: game state variables

Addresses for the dump in `rom.sha1`. `$gp` = 0x801775C0 (set at 0x80129DA8: `lui gp,0x8017; addiu gp,0x75C0`).

## Verified
- **Stage byte** 0x801775E4 (`gp+0x24`), 1-based, 1..35. The event-block loader (0x800F1F48, mode 4 init) reads
  OVER.BIN sectors from the u16 table at 0x801557E4 + 2*stage (stage N = block N-1). Pinning it from boot through
  New Game makes the game load stage N's event block, its chapter card and its battle map the normal way (warp
  `ev05`: block header 0x0D at 0x801C2518, card 転げ落ちる石, battle map, enemy battle animation; `work/qa/flow5`).
- **Game mode** u32 0x801781F0 (`gp+0xC30`): the main loop (0x800AC91C) calls the handler at 0x8014BAC4 + 4*mode
  every frame. Mostly init/update pairs (init in the exe sets up and loads an overlay, then bumps the mode).
  Seen in play: 0/1 boot, 18/19 boot logos + opening, 3 title, 16/17 new-game FMV (Start skips), 4/5 event,
  8/9 battle map, 10/11 battle animation. Forced (written while the event mode 5 starts; from the title the
  display setup is wrong and draws garbage): 12 Game Over, 14/15 intermission (label 「<stage card>」まで終了
  follows the stage byte; ~800 frames to fade in), 21/22 option screen, 23/24, 25/26, 27/28 memory-card
  screens, 29/30 ending staff roll. 20 = re-inits the battle map (garbled).
- **Intermission menu**: cursor starts on SAVE; down = LOAD, STATUS, NEXT. STATUS: character select, circle = pilot
  page (操者), right = 機体, 攻撃技. A forced intermission has zeroed stats (no party set up); stress values need
  RAM writes or a save editor later.
- **Memory card**: SAVE > NEW DATA > YES asks to create SYSTEM data first (YES), then writes `BISLPS-02319MASOU`
  (system) + `MASOU00` (game, 「…」まで). Title LOAD reads it ("データの読み込みが終了しました") and lands in the
  intermission. Fixture: `tools/debug/saves/stage05_intermission.mcd` (game-written, from a forced stage-5
  intermission; boot with `emu.py --sav`, title > LOAD).
- **Chapter card**: a 4bpp 0x8800-byte TIM from GRA5 0x1860000 + k*0x8800, loaded at 0x80075FF0 shortly before it
  shows; all 37 cards share the header `10000000 08000000 0c020000 0000e001 10001000`. Stage 5 shows card 6.
- New-game FMV (mode 17) skips on Start; text boxes advance on circle; Start does nothing on the battle map;
  circle on an empty map tile opens 終了/目的/システム/セーブ (終了 = end turn, the default).

- **Stage → card** (full sweep, card identified by 64 bytes at TIM +0x1D80, the first run unique to each card):
  stage 1 → 0, 2 → 2, 3 → 4, 4 → 3, 5..35 → stage+1 (5 → 6 … 35 → 36). Cards 1 (再試験) and 5 are never shown by
  a stage warp: story branches (guess: a failed exam / a route choice set a flag the pinned new game lacks). The
  card picker was not found (not a table indexed by stage; not an event-command operand in all blocks). warp.lua
  `card:K` shows any card by copying its TIM over the load buffer while stage 1's card loads (verified: 再試験).
- **Battle**: mashing circle on the map ends the player's turn (cursor starts on an empty tile); stage 5's enemies
  attack within ~6000 frames (mode 11, battle quotes). Stage 1's never engage within 24000 frames.

## Guess / open
- Unit records near 0x178670 (stride guess 0x2D0, HP u16 at +0x16A): layout and team field not confirmed (stage 1:
  Keigo's ミッダスト shows HP 660 on screen; 5760/2760/910/660×3/550 in that range). Needed for GOD / stress values.
- No save editor yet: the game-written fixture `tools/debug/saves/stage05_intermission.mcd` loads clean; layout and
  checksum unmapped (save = `BISLPS-02319MASOU00`, system = `BISLPS-02319MASOU`).
