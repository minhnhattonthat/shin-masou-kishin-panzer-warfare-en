-- Warp to a scene from a cold boot. Usage (from repo root):
--   python -X utf8 $SKILL/scripts/emu.py build/smk_en.cue --out work/qa/warp --script tools/debug/warp.lua
--          --var "SCENE='ev05'" --frames 4000 --sheet
-- Or all scenes: python -X utf8 tools/debug/warp_all.py. Scene list: tools/debug/scenes.tsv
-- (name, stage, how, wait, frames, keys, note). RAM facts: docs/re/debug.md.
--   how = event  stage N's opening event (block loaded), circle mashed through the text
--         card   stage N's chapter card (card TIM in its load buffer)
--         card:K stage N's card slot showing GRA5 card K (cards 1 and 5 no stage shows; GRA5= the disc tree)
--         map    stage N's battle map (game mode 9)
--         battle a battle animation in stage N (mode 11): circle ends turns, the enemy attacks
--         title  the title menu (mode 3)
--         force:M  as stage N's event starts, game mode M (12 game over, 14 intermission, 21 option,
--                  23/25/27 memory-card screens, 29 ending credits)
-- After `wait` frames the `keys` column (route steps "6 down;40 -;6 circle") is pressed, then the log gets
-- "SCENE <name> reached frame F" and the shot scene.png; the run fails (exit 2) if not reached by --frames.
-- The run ends 30 frames after the scene (saving --state-out there). Opt-in: KEEP=1 runs on to --frames
-- (mashing circle in story scenes unless HOLD=1); KEYS='<route>' overrides the keys column.
local m = PCSX.getMemPtr()
local function u8(a) return m[a % 0x200000] end
local function u32(a) return u8(a) + u8(a + 1) * 256 + u8(a + 2) * 65536 + u8(a + 3) * 16777216 end
local function w32(a, v) for i = 0, 3 do m[(a + i) % 0x200000] = math.floor(v / 256 ^ i) % 256 end end
local STAGE_B, MODE, BLK, CARD = 0x1775E4, 0x1781F0, 0x1C2518, 0x75FF0

local scene
for line in io.lines("../debug/scenes.tsv") do  -- emu.py runs PCSX in tools/pcsx
  local f = {}
  for c in (line .. "\t"):gmatch("([^\t]*)\t") do f[#f + 1] = c end
  if f[1] == SCENE then
    scene = { name = f[1], stage = tonumber(f[2]), how = f[3], wait = tonumber(f[4]) or 0, keys = KEYS or f[6] }
  end
end
if scene and scene.keys == "" then scene.keys = nil end
if not scene then error("unknown SCENE " .. tostring(SCENE) .. " (tools/debug/scenes.tsv)") end
local force = tonumber(scene.how:match("^force:(%d+)$"))
-- card:K = stage N's card slot showing GRA5 card K instead (cards no stage warp shows, e.g. story branches):
-- card K's TIM is copied over the load buffer every frame from when the card starts loading until the shot.
local card_k = tonumber(scene.how:match("^card:(%d+)$"))
local card_tim
if card_k then
  scene.how = "card"
  local f = assert(io.open(GRA5 or "../../work/disc/tree/GRA5.BIN", "rb"))  -- the disc tree being tested
  f:seek("set", 0x1860000 + card_k * 0x8800)
  card_tim = f:read(0x8800)
  f:close()
end

local function block_loaded()  -- event block header: byte 0 = stage + 8, bytes 8-11 = 06 00 00 00
  return u8(BLK) == scene.stage + 8 and u8(BLK + 8) == 6 and u8(BLK + 1) == 0
end
local function card_loaded()   -- all 37 chapter-card TIMs share this header
  return u32(CARD) == 0x10 and u32(CARD + 4) == 8 and u32(CARD + 16) == 0x100010
end
local function tap(k) if L.route_done() then L.press(k, 6); L.press("-", 34) end end

-- Story milestones, logged and shot (m_<kind>.png, `delay` frames later) in every story run, so one `map`
-- run also proves the stage's event and card scenes (tools/debug/warp_all.py relies on this).
local MS = { { kind = "event", delay = 1500 }, { kind = "card", delay = 40 }, { kind = "map", delay = 700 },
             { kind = "battle", delay = 240 } }  -- delays: until the screen has faded in (first text up)
local story = scene.how == "event" or scene.how == "card" or scene.how == "map" or scene.how == "battle"
local phase, at, since, done_at = "boot", nil, nil, nil
local function reached(n)
  phase, at = "wait", n
  L.log(string.format("WARP %s condition met frame %d (mode %d, stage %d)", scene.name, n, u32(MODE), u8(STAGE_B)))
end
local function milestones(n, mode)
  local hit = { event = block_loaded(), card = MS.event_at and card_loaded(), map = mode == 9, battle = mode == 11 }
  for _, ms in ipairs(MS) do
    if hit[ms.kind] and not MS[ms.kind .. "_at"] then
      MS[ms.kind .. "_at"] = n
      L.log(string.format("MILESTONE %s stage %d frame %d", ms.kind, scene.stage, n))
      if DUMP_MS then L.dump_ram("ram_" .. ms.kind .. ".bin") end  -- RAM at each milestone, for ramsearch
      if ms.kind == scene.how and phase == "story" then reached(n) end
    end
    local t = MS[ms.kind .. "_at"]
    if t and ms.kind == "event" and (n == t + 900 or n == t + 2100) then  -- events pass logo transitions:
      L.shot(string.format("m_event_%d.png", n - t))                       -- warp_all.py keeps the busiest
    end
    if t and n == t + ms.delay then
      L.shot("m_" .. ms.kind .. ".png")
      if ms.kind == "card" then  -- warp_all.py maps the signature to the GRA5 card index
        local sig = {}
        for i = 0, 63 do sig[#sig + 1] = string.format("%02x", u8(CARD + 0x1D80 + i)) end  -- unique per card
        L.log("CARDSIG " .. table.concat(sig))
      end
    end
  end
end

L.on_frame(function(n)
  local mode = u32(MODE)
  if n % 300 == 0 then L.log(string.format("%d mode %d stage %d", n, mode, u8(STAGE_B))) end
  if card_tim and MS.card_at and phase ~= "done" then
    for i = 1, #card_tim do m[CARD + i - 1] = card_tim:byte(i) end
  end
  if story then milestones(n, mode) end
  if phase == "boot" then
    if scene.stage then m[STAGE_B] = scene.stage end
    if force then  -- set the mode as stage N's event starts: the title's display setup draws garbage
      if mode == 5 then
        since = since or n
        if n - since >= (FORCE_DELAY or 0) then w32(MODE, force); reached(n) end
      else tap("start") end
    elseif scene.how == "title" then
      if mode == 3 then
        since = since or n
        if n - since >= 120 then reached(n) end
      elseif mode < 3 then tap("start") end
    else
      if mode ~= 5 then tap("start") else tap("circle") end  -- logos, title, New Game, skip FMV; then text
      if MS.event_at then phase = "story"; if scene.how == "event" then reached(n) end end
    end
  elseif phase == "story" then  -- keep the stage pinned, circle through text and end turns
    m[STAGE_B] = scene.stage
    tap("circle")
  elseif phase == "wait" then
    if scene.how == "event" and n - at < scene.wait then tap("circle") end
    if n - at >= scene.wait and L.route_done() then
      phase = "keys"
      if scene.keys then for step in scene.keys:gmatch("[^;]+") do  -- route syntax: "6 down;40 -;6 circle"
        local fr, k = step:match("^%s*(%d+)%s+(%S+)"); L.press(k, tonumber(fr)) end end
    end
  elseif phase == "keys" and L.route_done() then
    phase = "done"
    L.log(string.format("SCENE %s reached frame %d (mode %d, stage %d)", scene.name, n, u32(MODE), u8(STAGE_B)))
    L.shot("scene.png")
  elseif phase == "done" and story and not HOLD and not scene.keys then
    m[STAGE_B] = scene.stage
    tap("circle")
  end
  if phase == "done" then
    done_at = done_at or n
    if not KEEP and n >= done_at + 30 then  -- end early; KEEP=1 runs on to --frames (e.g. to watch what follows)
      if STATE_OUT then L.save_state(STATE_OUT) end
      L.log("final frame " .. n)
      L.finish(0)
      return
    end
  end
  if FRAMES and n >= FRAMES and phase ~= "done" then L.fail("scene " .. scene.name .. " not reached by frame " .. n) end
end)
