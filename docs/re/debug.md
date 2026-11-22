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
- **Map sub-mode** byte 0x80178240 (battle map, game mode 9): index k of the {handler, state byte} table at
  0x8014CFD4 + 8k (dispatcher reads the state byte at +4). Seen: 3 command menu, 10 map idle, 16 battle confirm,
  17 Spirit menu (0x800DD8B8), 22 end-turn prompt (0x800E1198), 24 level-up flow (0x800FAD84: "Level Up -> LV"
  box, then the point-allocation screen, ~370 frames). Poke it from a map state with a unit selected
  (`tools/lua/poke.lua POKE={[0x80178240]=24,[0x8014D098]=0}`) to open that screen; used by force_text.py.
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

- **Pilot records** (verified session 9, spirit menu fn 0x800DCEE4): 0x801786C0 + idx * 0xF0, idx = byte
  0x801775D9 (current pilot); +0x0E SP, +0x0F.. spirit ids (0 Alert 1 Focus 2 Guts 3 Gain 4 Strike 5 Trust 6 Iron
  Wall 7 Valor 8 Grit 9 Prana Heal 10 Spellbind 11 Soul 12 Disrupt 13 Friendship 14 Love 15 ???, 0x10 = empty).
  Active-spirit bits of stage-1 Keigo's unit: u16 0x80178604, bit n = spirit id n; the map unit box draws one marker
  after "Lv." (GRA5 0x11000 tiles). Recipe: `tools/lua/poke.lua --var AT=8 --var "POKE={[0x80178604]=2}"` from
  `ev01_map_p1.sstate`, route "10 -;4 circle;60 -". **Pokes at frame 1 are overwritten by the state load**: use
  AT >= 8 (why session 8's force_spirit / force_lvup recipes "did not take"). `tools/lua/peek.lua` logs bytes.

## Guess / open
- **Unit / pilot fields** (session 10, used by `tools/debug/stress.py`): 0xF0-byte records from 0x801785D0 (stage 1:
  Keigo's unit 0x801785D0, his pilot record 0x801786C0, enemies 0x80178F30 + k*0xF0). Unit part: u16 +0x2A HP,
  +0xBA max HP, +0xB8 (121 = Armor? the Unit page showed 1199 after pokes, so Armor is computed). Pilot part:
  +0x00 Lv, u32 +0x04 EXP, u16 +0x08 NEXT (0xFFFF shows ----), +0x0E SP, +0x15..+0x1A stats (Melee Aim Ranged
  Evade ? Luk; 0xFF shows 55 = the game's cap). Team field and which record is which unit: not mapped.
- No save editor yet: the game-written fixture `tools/debug/saves/stage05_intermission.mcd` loads clean; layout and
  checksum unmapped (save = `BISLPS-02319MASOU00`, system = `BISLPS-02319MASOU`).
