-- From emu.py --state-in: write POKE (hex bytes) at ADDR on frame 2 (a write on the load frame is lost), then dump
-- main RAM to ram_<frame>.bin at each frame in DUMPS (e.g. DUMPS={60,200}) and stop after the last.
--   emu.py CUE --out D --state-in work/states/force_msg.sstate --script tools/lua/poke_dump.lua \
--     --var ADDR=0x801C3960 --var "POKE='5AA5..'" --var "DUMPS={60,200}" --frames 400
local last = 0
for _, d in ipairs(DUMPS) do last = math.max(last, d) end
L.on_frame(function(n)
  if n == 2 and POKE then
    local m, o = PCSX.getMemPtr(), ADDR % 0x200000
    for k = 0, #POKE / 2 - 1 do m[o + k] = tonumber(POKE:sub(2 * k + 1, 2 * k + 2), 16) end
    for k = #POKE / 2, #POKE / 2 + 3 do m[o + k] = 0 end
  end
  for _, d in ipairs(DUMPS) do
    if n == d then L.dump_ram(string.format("ram_%d.bin", n)); L.shot(string.format("f%d.png", n)) end
  end
  if n == last then L.finish(0) end
end)
