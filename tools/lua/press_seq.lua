-- Press buttons at given frames (from --state-in or a warp), e.g. --var "SEQ={{10,'down'},{30,'circle'}}".
-- Optional STATE_AT=<frame>: save emu.py's --state-out then (a base state for force_text.py).
L.on_frame(function(n)
  for _, s in ipairs(SEQ) do
    if n == s[1] then L.press(s[2], s[3] or 4) end
  end
  if STATE_AT and n == STATE_AT then L.save_state(STATE_OUT); L.log("STATE saved frame " .. n) end
end)
