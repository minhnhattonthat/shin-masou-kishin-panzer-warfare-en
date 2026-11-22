-- Log the PC (and ra) of the first writes to [LO, HI] (RAM addresses), one line per distinct PC. Needs --debugger.
--   emu.py CUE --out D --state-in S --script tools/lua/who_writes.lua --var LO=0x8017D3C0 --var HI=0x8017D3C3 --debugger
local seen = {}
L.on_write(LO, HI, function(addr)
  local r = PCSX.getRegisters()
  local k = string.format("%08X", r.pc)
  if ALL or not seen[k] then  -- ALL=1: every write, not just the first per PC
    seen[k] = true
    local v = PCSX.getMemPtr()[(addr % 0x200000)]
    L.log(string.format("WRITE pc %s ra %08X addr %08X f%d old %02X", k, r.GPR.n.ra, addr, L.frame, v))
  end
end)
