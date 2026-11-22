-- Log every call to ADDR (its ra and a0-a3) between frames FROM and TO, at most MAX lines.
--   emu.py CUE --script tools/debug/warp.lua --var "SCENE='ev03'" --var KEEP=1 --script tools/lua/calls.lua --debugger
--          --var ADDR=0x80103CEC [--var FROM=2000 --var TO=3300 --var MAX=200]
local from, to, max, n = FROM or 0, TO or 1e9, MAX or 200, 0
L.on_exec(ADDR, function()
  if L.frame < from or L.frame > to or n >= max then return end
  n = n + 1
  local r = PCSX.getRegisters().GPR.n
  L.log(string.format("CALL %08X ra=%08X a0=%X a1=%X a2=%X a3=%X f%d", ADDR, r.ra, r.a0, r.a1, r.a2, r.a3, L.frame))
end)
