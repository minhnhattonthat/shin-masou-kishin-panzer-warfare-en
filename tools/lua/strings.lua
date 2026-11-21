-- Log every distinct string the font renderer draws. Needs --debugger. With warp.lua: which script id a box or
-- label comes from.
--   "STR <ptr> ra=<caller> x= y= f<frame>"   string function 0x80102D90 (exe), first time each pointer is seen
--   "DEC <ptr> ra=<caller> f<frame>"          glyph decoder 0x8010329C called from anywhere but 0x80102D90's
--                                             loop (overlay copies of the loop), first time each caller/ptr pair
--   emu.py CUE --out D --script tools/debug/warp.lua --var "SCENE='ev01'" --script tools/lua/strings.lua --debugger
local seen, dec = {}, {}
L.on_exec(0x80102D90, function()
  local r = PCSX.getRegisters().GPR.n
  local p = r.a3
  local k = string.format("%x %x %x %x", p, r.a1, r.a2, r.ra)
  if seen[k] then return end
  seen[k] = true
  local m = PCSX.getMemPtr()
  local slots = m[0x1B7188] + m[0x1B7189] * 256
  L.log(string.format("STR %08X ra=%08X slot=%d/%d x=%d y=%d f%d", p, r.ra, r.a0, slots, r.a1, r.a2, L.frame))
end)
L.on_exec(0x8010329C, function()
  local r = PCSX.getRegisters().GPR.n
  if r.ra == 0x80102E74 then return end
  local k = r.ra * 4096 + r.a2 % 4096
  if dec[k] then return end
  dec[k] = true
  L.log(string.format("DEC %08X ra=%08X f%d", r.a2, r.ra, L.frame))
end)
