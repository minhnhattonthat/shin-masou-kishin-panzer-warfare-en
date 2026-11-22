"""Machine check of force_text.py shots: the text ink must stay inside the box's text area.

    python -X utf8 tools/debug/force_check.py KIND [--out work/qa/force] [--list N]
Per shot: the bounding box of text ink (grey > 200) inside the box (KINDS[kind]["box"], x0,y0,x1,y1 inclusive,
inside the frame). Fails a shot whose ink reaches past the right limit or below the bottom limit (a line wider than
the box or a line too many), or that shows no ink at all. Prints the counts, the failures and the --list widest shots
(the ones worth a look at full size), and writes OUT/<kind>_check.tsv (id, max x, top, bottom). Exit 1 on any fail.
Limits measured on the 1500 first msg shots: text from x 68, frame at 62/316; speaker line y 173-183, body lines
end y 197/211/225; bq (1997 shots): text from x 64, 188 px budget to 252, lines end y 207/219."""
import argparse
import glob
import os
import sys

from PIL import Image

KINDS = {
    # box = search area (inside the frame), right/bottom = last allowed ink column/row
    "msg": dict(box=(64, 168, 314, 239), right=310, bottom=227),
    # bq: the battle scene behind the box is not flat, so ink = pixels off the chunk's per-pixel median (the
    # state replays the same animation frame for every quote) by more than 60
    "bq": dict(box=(60, 186, 259, 239), right=252, bottom=221, median=True),
}


def median_bg(paths, box):
    ims = [Image.open(f).convert("L").load() for f in paths[:60]]
    x0, y0, x1, y1 = box
    return {(x, y): sorted(im[x, y] for im in ims)[len(ims) // 2]
            for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def ink(path, box, bg=None):
    px = Image.open(path).convert("L").load()
    x0, y0, x1, y1 = box
    mx, top, bot = -1, None, None
    for y in range(y0, y1 + 1):
        row = [x for x in range(x0, x1 + 1) if (abs(px[x, y] - bg[x, y]) > 60 if bg else px[x, y] > 200)]
        if row:
            mx = max(mx, row[-1])
            top = y if top is None else top
            bot = y
    return mx, top, bot


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("kind", choices=KINDS)
    p.add_argument("--out", default="work/qa/force")
    p.add_argument("--list", type=int, default=10)
    a = p.parse_args()
    k = KINDS[a.kind]
    rows, bad = [], []
    bgs = {}
    for f in sorted(glob.glob(os.path.join(a.out, a.kind + "_*", "s_*.png"))):
        i = os.path.basename(f)[2:-4]
        d = os.path.dirname(f)
        if k.get("median") and d not in bgs:
            bgs[d] = median_bg(sorted(glob.glob(os.path.join(d, "s_*.png"))), k["box"])
        mx, top, bot = ink(f, k["box"], bgs.get(d))
        rows.append((i, mx, top, bot))
        if mx < 0 or mx > k["right"] or bot > k["bottom"]:
            bad.append((i, mx, top, bot))
    with open(os.path.join(a.out, a.kind + "_check.tsv"), "w", encoding="utf-8") as f:
        f.write("# id\tmax_x\ttop\tbottom\n")
        f.writelines("%s\t%s\t%s\t%s\n" % r for r in rows)
    print("%d shots, %d fail" % (len(rows), len(bad)))
    for r in bad:
        print("FAIL %s max_x %s top %s bottom %s" % r)
    for r in sorted(rows, key=lambda r: -r[1])[:a.list]:
        print("widest %s max_x %s bottom %s" % (r[0], r[1], r[3]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
