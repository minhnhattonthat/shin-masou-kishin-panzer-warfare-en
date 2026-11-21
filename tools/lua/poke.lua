-- Poke RAM bytes once at frame AT (default 1): --var "POKE={[0x800A6900]=0}" (address = value). For quick
-- what-if tests from a savestate, e.g. cutting a string short to change how many glyphs a screen draws.
local at = AT or 1
L.on_frame(function()
  if L.frame ~= at then return end
  local m = PCSX.getMemPtr()
  for a, v in pairs(POKE) do
    m[a - 0x80000000] = v
    L.log(string.format("POKE %08X=%02X", a, v))
  end
end)
