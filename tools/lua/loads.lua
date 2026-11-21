-- Which loads land in a RAM range, and when? Logs every contiguous run of CD-DMA writes (start, end, frames) plus
-- the stage byte, so the order of overlay / event-block loads into the event slot shows (docs/re/scripts.md).
--   emu.py CUE --script tools/debug/warp.lua --var "SCENE='ev05'" --script tools/lua/loads.lua --debugger
--          [--var LO=0x801C2518 --var HI=0x801D4B17]
local lo, hi = LO or 0x801C2518, HI or 0x801D4B17
local run_lo, run_end, run_f, run_last = nil, nil, nil, nil
local function flush()
  if run_lo then
    L.log(string.format("LOAD %08X-%08X f%d-%d", run_lo, run_end, run_f, run_last))
  end
  run_lo = nil
end
L.on_write(lo, hi, function(addr, size, kind)
  if not tostring(kind):find("DMA") then return end
  addr = 0x80000000 + (addr % 0x200000)
  if run_lo and addr == run_end then
    run_end, run_last = addr + size, L.frame
    return
  end
  flush()
  run_lo, run_end, run_f, run_last = addr, addr + size, L.frame, L.frame
end)
L.on_frame(function()
  if run_lo and L.frame > run_last + 30 then flush() end
end)
