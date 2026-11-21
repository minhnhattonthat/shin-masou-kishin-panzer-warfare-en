"""Bug 3 detector (status.md): cold boot ev01 KEEP=1 to the first weapon list (~f10200) and score the garbage
column right of the list (saturated pixels in x 203-223, y 70-200; clean ~0-40, garbage ~800+).

    python -X utf8 tools/debug/bug3_check.py build/bisect_0.cue build/bisect_1.cue ...   (runs in parallel)
"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

FRAME = 10500


def score(png):
    im = Image.open(png).convert("HSV").crop((203, 70, 223, 200))
    return sum(1 for h, s, v in im.getdata() if s > 150 and v > 120)


def run(cue):
    out = os.path.join(ROOT, "work/qa/bug3check", os.path.splitext(os.path.basename(cue))[0])
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), cue, "--out", out,
                    "--script", os.path.join(ROOT, "tools/debug/warp.lua"), "--var", "SCENE='ev01'", "--var", "KEEP=1",
                    "--frames", str(FRAME), "--shots", str(FRAME), "--timeout", "3000"], capture_output=True)
    png = os.path.join(out, "f%06d.png" % FRAME)
    return cue, score(png) if os.path.exists(png) else None


def main():
    with ThreadPoolExecutor(4) as ex:
        for cue, s in ex.map(run, sys.argv[1:]):
            print("%s score=%s %s" % (cue, s, "GARBAGE" if s is not None and s > 300 else "clean" if s is not None else "NO SHOT"))


if __name__ == "__main__":
    main()
