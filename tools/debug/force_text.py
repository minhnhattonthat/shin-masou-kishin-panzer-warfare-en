"""Forced text display: show strings the tours never reached in the game's own box, for textcover and visual QA.

    python -X utf8 tools/debug/force_text.py KIND [--ids FILE | ID..] [--rom build/smk_en.cue] [--jobs 2]
                                            [--chunk 150] [--hold 90] [--out work/qa/force]
KIND picks the base savestate (a few frames before the game draws the string at ADDR, from a cold-boot warp on the
current build: make it with tools/lua/state_at.lua) and the string set:
    msg  event messages (ev*), state work/states/force_msg.sstate (ev01 f3480), ADDR 0x801C3960 (ev000_1444)
    bq   battle quotes set A (bqA*; the set-B twin has the same text and box), state work/states/force_bq.sstate
         (tour.py's ev05 run, warp.lua KEEP=1 --debugger, f15082), ADDR 0x801CB1C0 (drawn f15087)
    wpn  weapon names, state work/states/force_wpn.sstate (ev01_map_p1.sstate + tools/lua/press_seq.lua
         SEQ={{10,'circle'},{50,'down'},{70,'circle'}} STATE_AT=80: the weapon list draws at f84)
Without ids it takes every string of the kind that textcover reported NEVER SHOWN in work/qa/textcover.txt.
For each chunk, tools/debug/force_text.lua loads the state, writes the string's built bytes (build/<rom>.strings.tsv)
at ADDR, runs --hold frames with no input and shoots s_<id>.png. Then per chunk: OUT/<kind>_NNN/ (shots, log),
work/qa/cover/force_<kind>_NNN/log.txt (TEXT keys of the shown ids and their quote twins, for textcover.py) and
contact sheets of the box crop in OUT/sheets/<kind>_NNN*.png (sheet.py --crop) for the visual-QA gate.
Exit 1 if a chunk failed or showed fewer strings than it was given. Regenerate states after engine/font changes.
Text types in: at --hold 90 a message over ~70 bytes is still fading in on its last line, so re-run those with
--hold 180 --out work/qa/force_long --ids-file work/qa/force/msg_long.txt, then --replace work/qa/force_long.
Check the shots with tools/debug/force_check.py KIND."""
import argparse
import concurrent.futures as cf
import glob
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402
import cover  # noqa: E402

KINDS = {
    "msg": dict(prefix="ev", state="work/states/force_msg.sstate", addr=0x801C3960, crop="0,150,320,90"),
    "bq": dict(prefix="bqA", state="work/states/force_bq.sstate", addr=0x801CB1C0, crop="0,184,320,56"),
    # weapon names exe_00D38-0133C into the map weapon list's first row (Seal Prod, exe_011E0); a longer name runs
    # into the strings after it, which this list does not show
    "wpn": dict(prefix="exe_", lo=0xD38, hi=0x133C, state="work/states/force_wpn.sstate", addr=0x800A69E0,
                crop="0,20,320,90"),
    # map unit box (ev01_map_p1, circle on Keigo at f10 draws at f13): pilot field reads the unit record's name copy
    # 0x801776E0, mech field the exe name exe_01CB8 (0x800A74B8); short names (No Pilot .. Zeldna) go in the pilot
    # field, mech short + full names in the mech field
    "pilot": dict(prefix="exe_", lo=0x134C, hi=0x14E0, state="work/states/ev01_map_p1.sstate", addr=0x801776E0,
                  press=(10, "circle"), crop="0,170,320,70"),
    "mech": dict(prefix="exe_", lo=0x193C, hi=0x1D68, state="work/states/ev01_map_p1.sstate", addr=0x800A74B8,
                 press=(10, "circle"), crop="0,170,320,70"),
    # status pilot page name (exe_01900 at 0x800A7100), redrawn by left from the mech page (warp im_status_mech)
    "pfull": dict(prefix="exe_", lo=0x14E8, hi=0x1920, state="work/states/im_status_mech.sstate", addr=0x800A7100,
                  press=(10, "left"), crop="0,0,320,110"),
    # intermission chapter label (overlay fields ov_ECB74.., 31 bytes each; stage 5 reads ov_ECBF4 at 0x801C710C,
    # drawn f3306 of warp intermission --debugger; state at f3295)
    "imlabel": dict(prefix="ov_", state="work/states/force_imlabel.sstate", addr=0x801C710C, crop="0,0,320,60"),
    # title LOAD slot info box (warp title_load + --sav tools/debug/saves/stage05_intermission.mcd, state f4300,
    # drawn ~f4470: run with --hold 220): DATA NN line 0x8015B640 (exe_B5E40), chapter label 0x8015B7B0 (exe_B5FB0)
    "sdata": dict(prefix="exe_", lo=0xB5E40, hi=0xB5F20, state="work/states/force_slabel.sstate", addr=0x8015B640,
                  sav="tools/debug/saves/stage05_intermission.mcd", crop="0,170,320,70"),
    "schap": dict(prefix="exe_", lo=0xB5F6C, hi=0xB61EC, state="work/states/force_slabel.sstate", addr=0x8015B7B0,
                  sav="tools/debug/saves/stage05_intermission.mcd", crop="0,170,320,70"),
    # memory-card messages (table 0x80159E48): the same state's card check draws "Checking..." (exe_B3BC0) at
    # 0x801593C0 ~f4340 (ra 0x80110EA0) until the slot list draws: run with --hold 100
    "mcmsg": dict(prefix="exe_", lo=0xB3930, hi=0xB460C, state="work/states/force_slabel.sstate", addr=0x801593C0,
                  sav="tools/debug/saves/stage05_intermission.mcd", crop="0,0,320,240"),
    # map Spirit menu (ev01_map_p1 + press_seq SEQ={{10,'circle'},{40,'down'},{55,'down'},{70,'down'},{90,'circle'}}
    # STATE_AT=98, drawn f103): spirit records 0x5E apart from 0xACFD4 (name +0, help +0xB); first cell Guts
    # (exe_AD090 at 0x80152890), help line at the top from its help 0x8015289B
    "spname": dict(prefix="exe_", lo=0xACFD4, hi=0xAD5B4, step=0x5E, state="work/states/force_spirit.sstate",
                   addr=0x80152890, crop="0,150,320,90"),
    "sphelp": dict(prefix="exe_", lo=0xACFDF, hi=0xAD5BF, step=0x5E, state="work/states/force_spirit.sstate",
                   addr=0x8015289B, crop="0,0,320,50"),
    # map menu Goal (ev01_map_p1 + press_seq SEQ={{10,'right'},{34,'right'},{58,'right'},{82,'circle'},
    # {146,'down'}} STATE_AT=160 = cursor on Goal; circle at t10 draws it ~t22: --hold 40): 36-byte objective
    # fields, victory line 0x80152E84 (exe_AD684), defeat line 0x80152FF8 (exe_AD7F8)
    "gwin": dict(prefix="exe_", lo=0xAD684, hi=0xAD7F7, state="work/states/force_goal.sstate", addr=0x80152E84,
                 press=(10, "circle"), crop="0,40,320,170"),
    "glose": dict(prefix="exe_", lo=0xAD7F8, hi=0xAD8B1, state="work/states/force_goal.sstate", addr=0x80152FF8,
                  press=(10, "circle"), crop="0,40,320,170"),
    # Goal box heading 勝利条件 (exe_02C60 at 0x800A8460) for its variant 勝ち抜き条件 (exe_02C6C)
    "glabel": dict(prefix="exe_", lo=0x2C6C, hi=0x2C6C, state="work/states/force_goal.sstate", addr=0x800A8460,
                   press=(10, "circle"), crop="0,40,320,170"),
    # end-turn prompt (map mode 22; ev01_map_p1 + poke.lua POKE={[0x80178240]=22} AT=2, STATE_AT=5, drawn f11):
    # line 0x800A83F0 (exe_02BF0)
    "endturn": dict(prefix="exe_", lo=0x2C2C, hi=0x2C2C, state="work/states/force_endturn.sstate",
                    addr=0x800A83F0, crop="0,0,320,240"),
    # level-up flow (map mode index byte 0x80178240 = 24 opens it for the selected unit; force_spirit.sstate +
    # tools/lua/poke.lua POKE={[0x80178240]=24,[0x8014D098]=0} AT=2, state 58 frames later; docs/re/debug.md):
    # Information box "Level Up -> LV" 0x800A8DA8 (exe_035A8, ~f12 from force_lvup_banner.sstate); the learned
    # skill / spirit lines and Max HP / Armor go in the same box
    "lvban": dict(prefix="exe_", lo=0x35A8, hi=0x39C8, state="work/states/force_lvup_banner.sstate",
                  addr=0x800A8DA8, crop="0,80,320,60"),
    # level-up screen (force_lvup.sstate = banner state + 360 frames): stat help bar 0x800A8DD0 (exe_035D0, f22),
    # circle at f150 opens the "Finish allocating?" dialog 0x800A8EEC (exe_036EC, f158)
    "lvhelp": dict(prefix="exe_", lo=0x35D0, hi=0x3688, state="work/states/force_lvup.sstate", addr=0x800A8DD0,
                   crop="0,190,320,50"),
    "lvdlg": dict(prefix="exe_", lo=0x36C0, hi=0x3718, state="work/states/force_lvup.sstate", addr=0x800A8EEC,
                  press=(150, "circle"), crop="0,40,320,100"),
}


def never_shown(path):
    with open(path, encoding="utf-8") as f:
        return [m.group(1) for m in (re.match(r"NEVER SHOWN\s+(\S+)", line) for line in f) if m]


def run_chunk(n, items, a, k, keyrows):
    name = "%s_%03d" % (a.kind, n)
    out = os.path.join(a.out, name)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    lua = os.path.join(out, "items.lua")
    with open(lua, "w", encoding="ascii") as f:
        f.write("ITEMS = {\n%s}\n" % "".join('{"%s","%s"},\n' % (i, b.hex().upper()) for i, b in items))
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), a.rom, "--out", out,
           "--script", lua, "--script", os.path.join(ROOT, "tools/debug/force_text.lua"),
           "--var", "STATE='%s'" % os.path.abspath(k["state"]).replace("\\", "/"), "--var", "ADDR=%d" % k["addr"],
           "--var", "HOLD=%d" % a.hold, "--frames", str((a.hold + 2) * (len(items) + 2)), "--timeout", "3000"]
    if k.get("sav"):  # the state does not hold the memory card the screen reads after the load
        cmd += ["--sav", os.path.join(ROOT, k["sav"])]
    if a.press or k.get("press"):
        cmd += ["--var", "PRESS=%d" % (a.press or k["press"][0]), "--var", "PRESS_KEY='%s'" % k.get("press", (0, "circle"))[1]]
    rc = subprocess.run(cmd, capture_output=True, text=True).returncode
    with open(os.path.join(out, "log.txt"), encoding="utf-8") as f:
        shown = [line.split()[1] for line in f if line.startswith("FORCED ")]
    tag = os.path.basename(os.path.normpath(a.out))  # a re-run in another --out keeps its own cover log
    cov = os.path.join(ROOT, "work/qa/cover", "force_" + name if tag == "force" else "%s_%s" % (tag, name))
    os.makedirs(cov, exist_ok=True)
    keys = set()
    for i in shown:
        key, twin = keyrows[i]
        keys.add(key)
        if twin:
            keys.add(keyrows[twin][0])
    with open(os.path.join(cov, "log.txt"), "w", encoding="ascii") as f:
        f.write("".join("TEXT %X\n" % x for x in sorted(keys)))
    make_sheet(out, a, k)
    return name, rc, len(items), len(shown)


def make_sheet(out, a, k):
    """OUT/sheets/<chunk>_sheet*.png from the chunk's shots, in log order."""
    with open(os.path.join(out, "log.txt"), encoding="utf-8") as f:
        shown = [line.split()[1] for line in f if line.startswith("FORCED ")]
    sheets = os.path.join(a.out, "sheets")
    os.makedirs(sheets, exist_ok=True)
    shots = [os.path.join(out, "s_%s.png" % i) for i in shown]
    if shots:
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "sheet.py"), *shots,
                        "--crop", k["crop"], "--out", os.path.join(sheets, os.path.basename(out) + "_sheet.png")],
                       capture_output=True, text=True)


def replace(a, k):
    """--replace DIR: copy DIR's chunk shots (a re-run of some ids, e.g. a longer --hold) over the same ids' shots
    in OUT and rebuild the sheets of every chunk that changed."""
    src = {os.path.basename(f): f for f in glob.glob(os.path.join(a.replace, a.kind + "_*", "s_*.png"))}
    changed = set()
    for f in glob.glob(os.path.join(a.out, a.kind + "_*", "s_*.png")):
        if os.path.basename(f) in src:
            shutil.copyfile(src[os.path.basename(f)], f)
            changed.add(os.path.dirname(f))
    for out in sorted(changed):
        make_sheet(out, a, k)
    print("%d shots replaced in %d chunks" % (len(src), len(changed)))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("kind", choices=KINDS)
    p.add_argument("ids", nargs="*")
    p.add_argument("--ids-file")
    p.add_argument("--rom", default="build/smk_en.cue")
    p.add_argument("--out", default="work/qa/force")
    p.add_argument("--jobs", type=int, default=2)
    p.add_argument("--chunk", type=int, default=150)
    p.add_argument("--hold", type=int, default=90)
    p.add_argument("--press", type=int, default=0, help="press circle at this frame of each item")
    p.add_argument("--first", type=int, default=0, help="number of the first chunk (to add chunks to a run)")
    p.add_argument("--replace", metavar="DIR", help="copy a re-run's shots over OUT's and rebuild those sheets")
    p.add_argument("--state", help="base savestate instead of the kind's (e.g. one made on another build)")
    a = p.parse_args()
    k = dict(KINDS[a.kind], **({"state": a.state} if a.state else {}))
    if a.replace:
        return replace(a, k)
    rows = cover.read_strings(os.path.splitext(a.rom)[0] + ".strings.tsv")
    byid = {i: b for i, _, _, b, _ in rows}
    back = {twin: i for i, _, _, _, twin in rows if twin}  # set-A quote -> its set-B twin (the tsv lists B -> A)
    keyrows = {i: (key, twin or back.get(i)) for i, key, _, _, twin in rows}
    ids = a.ids or (open(a.ids_file, encoding="utf-8").read().split() if a.ids_file else
                    [i for i in never_shown("work/qa/textcover.txt") if i.startswith(k["prefix"])
                     and k.get("lo", 0) <= int(i.split("_")[-1], 16) <= k.get("hi", 1 << 32)
                     and (int(i.split("_")[-1], 16) - k.get("lo", 0)) % k.get("step", 1) == 0])
    items = [(i, byid[i]) for i in ids]
    chunks = [items[x:x + a.chunk] for x in range(0, len(items), a.chunk)]
    bad = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for name, rc, want, got in ex.map(lambda c: run_chunk(a.first + c[0], c[1], a, k, keyrows),
                                          enumerate(chunks)):
            ok = rc == 0 and got == want
            bad += not ok
            print("%s %-10s rc %s shown %d/%d" % ("ok  " if ok else "FAIL", name, rc, got, want), flush=True)
    print("%d chunks, %d failed" % (len(chunks), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
