"""Free-space trap: warp to scenes with a write watch on a RAM range; any logged write means the range is live.

    python -X utf8 tools/debug/trap.py LO HI [SCENE..] [--rom CUE] [--out work/qa/trap]

Runs each scene (default: a spread over events, battle, menus, save, credits) with warp.lua + the skill's
watch.lua under --debugger (interpreter, slow), in parallel. Prints each scene's write lines; exit 1 if any.
Result 2026-11-22: 0x8016D740-0x8016DC3F no game writes in the 8 default scenes (asm/vwf.asm lives there)."""
import argparse
import concurrent.futures as cf
import csv
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

DEFAULT = ["ev05", "map05", "battle05", "im_status_weapons", "im_save_confirm", "option", "gameover", "credits"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lo")
    ap.add_argument("hi")
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--rom", default=os.path.join(ROOT, "rom", "Shin Masou Kishin - Panzer Warfare (Japan).cue"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "trap"))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--read", action="store_true", help="watch reads instead (does the game read the range?)")
    a = ap.parse_args()
    rows = {r["name"]: r for r in csv.DictReader(open(os.path.join(ROOT, "tools", "debug", "scenes.tsv"),
                                                      encoding="utf-8"), delimiter="\t")}
    names = a.scenes or DEFAULT

    def run(n):
        out = os.path.join(a.out, n)
        cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), a.rom, "--out", out,
               "--script", os.path.join(ROOT, "tools", "debug", "warp.lua"), "--var", f"SCENE='{n}'",
               "--script", os.path.join(SKILL, "scripts", "lua", "probes", "watch.lua"),
               "--var", f"WATCH_LO={a.lo}", "--var", f"WATCH_HI={a.hi}", "--debugger",
               *(["--var", "WATCH_MODE='read'"] if a.read else []),
               "--frames", rows[n]["frames"], "--timeout", "3000"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=ROOT)
        log = open(os.path.join(out, "log.txt"), encoding="utf-8", errors="replace").read() \
            if os.path.exists(os.path.join(out, "log.txt")) else ""
        # BIOS PCs (0xBFC0xxxx) are the boot RAM clear and the exe load itself, not the game using the range
        mode = "read" if a.read else "write"
        return n, "SCENE %s reached" % n in log, [ln for ln in log.splitlines()
                                                    if f" {mode} pc=" in ln and f" {mode} pc=BFC" not in ln]

    bad = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for n, ok, hits in ex.map(run, names):
            print(n, "reached" if ok else "NOT REACHED", len(hits), "writes", *hits[:5], sep="\n  " if hits else " ")
            bad += bool(hits) or not ok
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
