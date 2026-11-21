"""Draws the img-row PNGs of gfx/menus.tsv into gfx/out/menus/ (run from anywhere; rerun after changing this file).

GRA5.BIN 0x1740800 character-name buttons: the 12 JP names are letters (palette indices 7-c) over a blue/cream
marbled plate (indices 1-6, d). The letters are inpainted from their neighbours (seeded, so the output is stable), then
the English name is drawn in the same gold (c) with a dark (7) shadow. Pure palette-index work, no colour round trip.
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
from PIL import Image  # noqa: E402

OUT = ROOT / "gfx/out/menus"
FILE, TIM = "GRA5.BIN", 0x1740800
NAMES = ["Keigo", "Alma", "Yen", "Toto", "Beumer", "Furcas", "Helena", "Drawbi", "Blacky", "Shess", "Alfredo", "???"]
X, W, H = 6, 38, 12            # button interior: x 6..43, rows Y+1..Y+12 (Y = 24 + 16 * i)
LETTER = set(range(7, 13))     # indices the JP letters use; the plate uses 1-6, d-f
INK, EDGE = 0xE, 0x7
FONT = "tiny5"


def rect(i):
    return X, 25 + 16 * i, W, H


def button(px, i, name):
    x, y, w, h = rect(i)
    cell = [row[x:x + w] for row in px[y:y + h]]
    todo = {(i2, j) for j in range(h) for i2 in range(w) if cell[j][i2] in LETTER}
    rng = random.Random(i)
    while todo:
        done = {}
        for (a, b) in sorted(todo):
            nb = [cell[b + dj][a + di] for di in (-1, 0, 1) for dj in (-1, 0, 1)
                  if (di or dj) and 0 <= a + di < w and 0 <= b + dj < h and (a + di, b + dj) not in todo]
            if nb:
                done[(a, b)] = rng.choice(nb)
        for (a, b), v in done.items():
            cell[b][a] = v
            todo.discard((a, b))
    m = gfx.mask(name, FONT)[0]
    mh, mw = len(m), len(m[0])
    x0, y0 = (w - mw) // 2, (h - mh) // 2
    on = {(x0 + a, y0 + b) for b in range(mh) for a in range(mw) if m[b][a]}
    for (a, b) in {(a + p, b + q) for a, b in on for p in (-1, 0, 1) for q in (-1, 0, 1)} - on:
        if 0 <= a < w and 0 <= b < h:
            cell[b][a] = EDGE
    for a, b in on:
        cell[b][a] = INK
    assert mw + 2 <= w and mh + 2 <= h, (name, mw, mh)
    return cell


def main():
    d = gfx._file(str(ROOT / "work/disc/tree"), FILE)
    px = gfx.values(d, TIM)
    OUT.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(NAMES):
        cell = button(px, i, name)
        im = Image.new("P", (W, H))
        im.putpalette([v for k in range(256) for v in (k, k, k)])
        im.putdata([v for r in cell for v in r])
        im.save(OUT / ("btn%02d.png" % i))


if __name__ == "__main__":
    main()
