"""Forced text display: show strings the tours never reached in the game's own box, for textcover and visual QA.

    python -X utf8 tools/debug/force_text.py KIND [--ids FILE | ID..] [--rom build/smk_en.cue] [--jobs 2]
                                            [--chunk 150] [--hold 90] [--out work/qa/force]
KIND picks the base savestate (a few frames before the game draws the string at ADDR, from a cold-boot warp on the
current build: make it with tools/lua/state_at.lua) and the string set:
    msg  event messages (ev*), state work/states/force_msg.sstate (ev01 f3480), ADDR 0x801C3960 (ev000_1444)
    bq   battle quotes set A (bqA*; the set-B twin has the same text and box), state work/states/force_bq.sstate
         (tour.py's ev05 run, warp.lua KEEP=1 --debugger, f15082), ADDR 0x801CB1C0 (drawn f15087)
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
    if a.press:
        cmd += ["--var", "PRESS=%d" % a.press]
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
    a = p.parse_args()
    k = KINDS[a.kind]
    if a.replace:
        return replace(a, k)
    rows = cover.read_strings(os.path.splitext(a.rom)[0] + ".strings.tsv")
    byid = {i: b for i, _, _, b, _ in rows}
    keyrows = {i: (key, twin) for i, key, _, _, twin in rows}
    ids = a.ids or (open(a.ids_file, encoding="utf-8").read().split() if a.ids_file else
                    [i for i in never_shown("work/qa/textcover.txt") if i.startswith(k["prefix"])])
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
