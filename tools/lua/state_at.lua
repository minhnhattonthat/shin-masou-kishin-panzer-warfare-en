-- Save emu.py's --state-out at frame AT and stop (e.g. a few frames before a string draws, for force_text.lua):
--   emu.py CUE --out D --script tools/debug/warp.lua --var "SCENE='ev01'" --var KEEP=1 \
--     --script tools/lua/state_at.lua --var AT=3480 --state-out work/states/x.sstate --frames 4000
L.on_frame(function(n)
  if n == AT then
    L.shot("at.png")
    L.save_state(STATE_OUT)
    L.log("STATE saved frame " .. n)
    L.finish(0)
  end
end)
