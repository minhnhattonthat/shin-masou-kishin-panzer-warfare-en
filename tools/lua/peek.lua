-- Log RAM bytes at frame AT (default 2): --var "PEEK={{0x801775D9,1},{0x801786C0,0x40}}" ({address, length} pairs).
local at = AT or 2
L.on_frame(function()
  if L.frame ~= at then return end
  local m = PCSX.getMemPtr()
  for _, p in ipairs(PEEK) do
    local t = {}
    for i = 0, p[2] - 1 do t[#t + 1] = string.format("%02X", m[p[1] - 0x80000000 + i]) end
    L.log(string.format("PEEK %08X %s", p[1], table.concat(t, " ")))
  end
end)
