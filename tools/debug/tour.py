"""Dialogue tour: warp to each stage's opening event from a cold boot, mash circle through it (warp.lua KEEP=1),
shoot every --every frames, and page the distinct frames into contact sheets for the visual-QA gate.

    python -X utf8 tools/debug/tour.py [ev01 ev02 ..] [--rom build/smk_en.cue] [--out work/qa/tour] [--jobs 4]
                                       [--frames 20000] [--every 40]
Per scene: OUT/<scene>/f*.png + log.txt, sheets in OUT/sheets/<scene>_sheet*.png (sheet.py --changed 0.01).
Then: qa_gate.py init work/qa/manifest.tsv work/qa/tour/sheets --build build/smk_en.bin. Exit 1 if a run failed."""
import argparse
import concurrent.futures as cf
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402


def run(scene, a):
    out = os.path.join(a.out, scene)
    shutil.rmtree(out, ignore_errors=True)
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), a.rom, "--out", out,
           "--script", os.path.join(ROOT, "tools/debug/warp.lua"), "--var", "SCENE='%s'" % scene, "--var", "KEEP=1",
           "--frames", str(a.frames), "--shot-every", str(a.every), "--timeout", "3000",
           "--script", os.path.join(ROOT, "tools/lua/textcover.lua"), "--debugger"]  # PTR lines: tools/cover.py
    rc = subprocess.run(cmd, capture_output=True, text=True).returncode
    sheets = os.path.join(a.out, "sheets")
    os.makedirs(sheets, exist_ok=True)
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "sheet.py"), out, "--changed", "0.01",
                    "--out", os.path.join(sheets, scene + "_sheet.png")], capture_output=True, text=True)
    return scene, rc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--rom", default=os.path.join(ROOT, "build", "smk_en.cue"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "tour"))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--frames", type=int, default=20000)
    ap.add_argument("--every", type=int, default=40)
    a = ap.parse_args()
    scenes = a.scenes or ["ev%02d" % k for k in range(1, 36)]
    bad = []
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for scene, rc in ex.map(lambda s: run(s, a), scenes):
            print("%-4s %s rc %d" % ("ok" if rc == 0 else "FAIL", scene, rc), flush=True)
            if rc:
                bad.append(scene)
    print("%d/%d runs ok" % (len(scenes) - len(bad), len(scenes)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
