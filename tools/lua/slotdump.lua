-- Glyph-slot entries (base u32 *0x801B7184, 0x44 bytes each, see slots.lua; entry +0 = 0 when free, +16/+18 = x/y).
--   --var AT=F           "SLOTDUMP <i> <hex>" for slots LO..HI-1 at frame F
--   --var EVERY=N        "SLOTUSE f<frame> <map>" every N frames from FROM (default 0): one char per slot LO..HI-1,
--                        '.' free, else '#'; shows which slot ranges a screen uses at the same time
--   emu.py CUE --script tools/debug/warp.lua --var "SCENE='battle05'" --var KEEP=1 --script tools/lua/slotdump.lua
--          --var EVERY=30 --var FROM=12000 --var LO=0 --var HI=96
local lo, hi, at, every, from = LO or 0, HI or 40, AT or -1, EVERY or 0, FROM or 0
L.on_frame(function()
  local m = PCSX.getMemPtr()
  local base = m[0x1B7184] + m[0x1B7185] * 256 + m[0x1B7186] * 65536 + m[0x1B7187] * 16777216 - 0x80000000
  if base < 0 then return end
  if L.frame == at then
    for i = lo, hi - 1 do
      local t = {}
      for k = 0, 0x43 do t[#t + 1] = string.format("%02X", m[base + i * 0x44 + k]) end
      L.log(string.format("SLOTDUMP %d %s", i, table.concat(t)))
    end
  end
  if every > 0 and L.frame >= from and (L.frame - from) % every == 0 then
    local t = {}
    for i = lo, hi - 1 do
      local a = base + i * 0x44
      t[#t + 1] = (m[a] == 0 and m[a + 1] == 0) and "." or "#"
    end
    L.log(string.format("SLOTUSE f%d %s", L.frame, table.concat(t)))
  end
end)
