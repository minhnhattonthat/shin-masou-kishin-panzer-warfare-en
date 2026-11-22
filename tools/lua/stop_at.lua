-- Stop when the string renderer 0x80102D90 draws RAM address STOP (from build/<out>.strings.tsv), after WAIT more
-- frames (default 60), saving emu.py's --state-out and a shot. Needs --debugger. With warp.lua KEEP=1 it makes a
-- state of any event line on the current build, e.g. a choice to start a play.py session from:
--   emu.py build/smk_en.cue --out D --script tools/debug/warp.lua --var "SCENE='ev01'" --var KEEP=1 \
--     --script tools/lua/stop_at.lua --var STOP=0x801C471C --state-out work/states/x.sstate --debugger
local at
L.on_exec(0x80102D90, function()
  if not at and PCSX.getRegisters().GPR.n.a3 == STOP then at = L.frame end
end)
L.on_frame(function(n)
  if at and n >= at + (WAIT or 60) then
    L.shot("stop.png")
    if STATE_OUT then L.save_state(STATE_OUT) end
    L.log("STOP reached frame " .. n)
    L.finish(0)
  end
end)
