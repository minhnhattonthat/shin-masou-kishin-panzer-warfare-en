-- Event/text windows drawn by the exe window code (0x800F1940, s0 = window struct): slot start (+0x10) and slot
-- count (+0x12, glyphs freed on close: text over the count leaves stray glyphs), geometry (+6 x, +8 y, +0xA w,
-- +0xC h; guesses). One line per distinct window state: "WIN s0=… start= count= x= y= w= h= f<frame>".
--   emu.py CUE --script tools/debug/warp.lua --var "SCENE='ev01'" --script tools/lua/windows.lua --debugger
local seen = {}
L.on_exec(0x800F1940, function()
  local r = PCSX.getRegisters().GPR.n
  local m = PCSX.getMemPtr()
  local s0 = r.s0 % 0x200000
  local function h(o) local v = m[s0 + o] + m[s0 + o + 1] * 256; return v >= 32768 and v - 65536 or v end
  local line = string.format("WIN s0=%08X start=%d count=%d x=%d y=%d w=%d h=%d", r.s0, h(0x10), h(0x12), h(6),
                             h(8), h(0xA), h(0xC))
  if seen[line] then return end
  seen[line] = true
  L.log(line .. " f" .. L.frame)
end)
