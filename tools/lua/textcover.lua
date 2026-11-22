-- Text coverage probe (tools/cover.py turns these lines into textcover.py TEXT keys). Needs --debugger.
--   "PTR <addr> <up to 16 bytes hex, to the first NUL> f<frame>"  first time each pointer+bytes pair is drawn:
--   string renderer 0x80102D90 (a3 = string), glyph decoder 0x8010329C called from overlay copies of the loop (a2).
-- The bytes let cover.py tell apart strings that share RAM (event blocks, overlays, quote slots).
--   emu.py CUE --out D --script tools/debug/warp.lua --var "SCENE='ev01'" --script tools/lua/textcover.lua --debugger
local seen = {}
local function hit(p)
  local o = p % 0x200000
  if p < 0x80000000 or o > 0x1FFFF0 then return end
  local m = PCSX.getMemPtr()
  local hex = {}
  for i = 0, 15 do
    local b = m[o + i]
    if b == 0 then break end
    hex[#hex + 1] = string.format("%02X", b)
  end
  local k = string.format("%08X %s", p, table.concat(hex))
  if seen[k] then return end
  seen[k] = true
  L.log(string.format("PTR %s f%d", k, L.frame))
end
L.on_exec(0x80102D90, function() hit(PCSX.getRegisters().GPR.n.a3) end)
L.on_exec(0x8010329C, function()
  local r = PCSX.getRegisters().GPR.n
  if r.ra ~= 0x80102E74 then hit(r.a2) end
end)
