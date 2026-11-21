"""Glyph torture build: every printable ASCII character (+ double spaces) in the first two stage-1 message boxes.

    python -X utf8 tools/debug/torture.py [--out build/smk_torture]   then warp ev01 (the box is ev000_1444)
Prints each line's px (must be <= insert.DIALOGUE_PX)."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import font  # noqa: E402
import insert  # noqa: E402

BOXES = {"ev000_1444": ["!\"#$%&'()*+,-./0123456789:;<=>?", "@ABCDEFGHIJKLMNOPQRSTUVW", "XYZ[\\]^_`  x  y"],
         "ev000_1478": ["abcdefghijklmnopqrstuvwxyz", "{|}~ .,!? 'quote' \"double\" ..."]}
LINES = [t for v in BOXES.values() for t in v]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="build/smk_torture")
    a = ap.parse_args()
    for t in LINES:
        print(font.width_px(t), t)
        assert font.width_px(t) <= insert.DIALOGUE_PX
    assert "".join(sorted(set("".join(LINES)))) == "".join(chr(c) for c in range(0x20, 0x7F))
    qa = [x for k, v in BOXES.items() for x in ("--qa", "%s=%s\\n" % (k, "\\n".join(v)))]
    sys.exit(subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "build.py"), *qa, "--out", a.out], cwd=ROOT))


if __name__ == "__main__":
    main()
