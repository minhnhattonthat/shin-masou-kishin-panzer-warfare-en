-- Forced text display (tools/debug/force_text.py writes ITEMS and runs this). From a savestate taken a few frames
-- before the game draws the string at ADDR, for each item: load the state, write the item's built bytes at ADDR
-- (the box then draws them with the game's own code), run HOLD frames with no input, save s_<id>.png and log
-- "FORCED <id>". Needs ITEMS = {{id, hex}, ..}, STATE, ADDR, HOLD (default 90). Not --debugger: no hooks.
local i, t = 0, 0
local function start()
  i = i + 1
  if i > #ITEMS then L.log("FORCE done " .. #ITEMS); L.finish(0); return end
  PCSX.loadSaveState(Support.File.open(STATE))
  t = 0
end
local function poke()  -- one frame after the load: a write in the same callback is lost to the state load
  local m = PCSX.getMemPtr()
  local o = ADDR % 0x200000
  local hex = ITEMS[i][2]
  local n = #hex / 2
  for k = 0, n - 1 do m[o + k] = tonumber(hex:sub(2 * k + 1, 2 * k + 2), 16) end
  for k = n, n + 3 do m[o + k] = 0 end
end
L.on_frame(function()
  if i == 0 then start(); return end
  t = t + 1
  if t == 1 then poke() end
  if PRESS and t == PRESS then L.press("circle", 4) end  -- complete the text reveal (it stalls without input)
  if t == (HOLD or 90) then
    L.shot("s_" .. ITEMS[i][1] .. ".png")
    L.log("FORCED " .. ITEMS[i][1])
    start()
  end
end)
