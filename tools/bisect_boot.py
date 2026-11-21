"""Which script/ files break a boot? Builds `build.py --only PREFIX` per prefix and smoke-boots each.

    python -X utf8 tools/bisect_boot.py exe overlay events/ battle_ [--frames 3600]
Prints `PREFIX ok|FAIL`; exit 1 if any fails. Builds go to build/bisect_<n>."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefixes", nargs="+")
    ap.add_argument("--frames", default="3600")
    a = ap.parse_args()
    bad = 0
    for n, p in enumerate(a.prefixes):
        out = ROOT / "build" / ("bisect_%d" % n)
        subprocess.run([sys.executable, "-X", "utf8", ROOT / "build.py", "--only", *p.split(","), "--out", out],
                       check=True, stdout=subprocess.DEVNULL)
        r = subprocess.run([sys.executable, "-X", "utf8", Path(SKILL) / "scripts" / "emu.py", str(out) + ".cue",
                            "--out", ROOT / "work" / "qa" / ("bisect_%d" % n), "--frames", a.frames, "--smoke"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(p, "ok" if r.returncode == 0 else "FAIL", flush=True)
        bad += r.returncode != 0
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
