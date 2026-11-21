-- Who writes glyph-slot entries? The renderer's sprite slots: u32 *0x801B7184 = base, 0x44 bytes each, count at
-- 0x801B7188 (600). Logs "SLOT pc=<pc> slot=<i> off=<byte in entry> f<frame>" once per (pc, slot / 8).
--   emu.py CUE --script tools/debug/warp.lua --var "SCENE='ev01'" --script tools/lua/slots.lua --debugger
--          [--var LO=300 --var HI=340]
local lo, hi = LO or 0, HI or 600
local seen, armed = {}, false
L.on_frame(function()
  if armed then return end
  local m = PCSX.getMemPtr()
  local base = m[0x1B7184] + m[0x1B7185] * 256 + m[0x1B7186] * 65536 + m[0x1B7187] * 16777216
  if base < 0x80000000 then return end
  armed = true
  L.log(string.format("SLOTS base=%08X f%d", base, L.frame))
  L.on_write(base + lo * 0x44, base + hi * 0x44 - 1, function(addr)
    local pc = L.pc()
    local i = math.floor((addr - base) / 0x44)
    local k = pc * 1024 + math.floor(i / 8)
    if seen[k] then return end
    seen[k] = true
    L.log(string.format("SLOT pc=%08X slot=%d off=%d f%d", pc, i, (addr - base) % 0x44, L.frame))
  end)
end)
