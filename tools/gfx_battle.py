"""Draws the img-row PNGs of gfx/battle.tsv into gfx/out/battle/ (rerun after editing; output is deterministic).

BAT_TIM.BIN 0x15E2000 + k * 0x8800 (k = 0..15): the battle reaction labels. Each TIM is 8 bpp with its own CLUT, a
one-hue ramp from black (index 0000 = transparent) to the label colour, so the antialiased letters are ramp indices. The
English is rendered antialiased (4x supersample of Nunito Black), outlined with a dark halo, and each pixel's brightness
is mapped to the nearest ramp index the original TIM already uses. Pure palette-index work.
"""
import collections
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
import tim  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

OUT = ROOT / "gfx/out/battle"
FILE = "BAT_TIM.BIN"
RECT = (46, 16, 156, 94)           # covers every JP pixel of the 16 TIMs (x 51-194, y 21-104)
LIMIT = (51, 21, 194, 104)         # English stays inside the union of the Japanese extents
SIZE, SS, PITCH = 26, 4, 30        # font px, supersample, line pitch
FONT = ROOT / "fonts/nunito/Nunito[wght].ttf"
LABELS = ["Evade", "Parry", "Clash", "Defend", "Barrier", "Hit",
          "Melee|Evade", "Melee|Defend", "Melee|Barrier", "Melee|Hit",
          "Rear|Evade", "Rear|Barrier", "Rear|Hit",
          "Rear Melee|Evade", "Rear Melee|Barrier", "Rear Melee|Hit"]


def tim_off(k):
    return 0x15E2000 + 0x8800 * k


def text_cov(lines):
    """Coverage (0..1) of the lines, each centred, as rows of floats; (W, H) canvas of RECT size, centred on the
    Japanese ink's centre later by the caller."""
    f = ImageFont.truetype(str(FONT), SIZE * SS)
    f.set_variation_by_axes([900])
    ws = [f.getbbox(t)[2] - f.getbbox(t)[0] for t in lines]
    W = max(ws) // SS + 4
    im = Image.new("L", (W * SS, (PITCH * len(lines) + 8) * SS), 0)
    dr = ImageDraw.Draw(im)
    for i, t in enumerate(lines):
        l, top, r, b = f.getbbox(t)
        dr.text(((W * SS - (r - l)) // 2 - l, (4 + i * PITCH) * SS + 6 * SS), t, font=f, fill=255)
    im = im.reduce(SS)
    return im.crop(im.getbbox())


def render(k):
    d = gfx._file(str(ROOT / "work/disc/tree"), FILE)
    off = tim_off(k)
    fl, cl, n, po, w, h, _ = tim.parse(d, off)
    px = gfx.values(d, off)
    raw = lambda v: struct.unpack_from("<H", d, cl + 2 * v)[0]
    bg = collections.Counter(v for r in px for v in r).most_common(1)[0][0]
    assert raw(bg) == 0
    x0, y0, rw, rh = RECT
    ink = [(x, y) for y, r in enumerate(px) for x, v in enumerate(r) if raw(v)]
    assert all(x0 <= x < x0 + rw and y0 <= y < y0 + rh for x, y in ink), "JP ink outside RECT"
    cx = (min(p[0] for p in ink) + max(p[0] for p in ink)) / 2
    cy = (min(p[1] for p in ink) + max(p[1] for p in ink)) / 2
    # ramp: used palette entries by brightness (sum of the 5-bit channels), one index per distinct value
    bright = lambda c: (c & 31) + (c >> 5 & 31) + (c >> 10 & 31)
    ramp = {}
    for v in {v for r in px for v in r}:
        if raw(v):
            ramp.setdefault(raw(v), v)
    ramp = sorted((bright(c), v) for c, v in ramp.items())
    top = ramp[-1][0]
    cov = text_cov(LABELS[k].split("|"))
    cw, ch = cov.size
    ox, oy = round(cx - cw / 2), round(cy - ch / 2)
    c = [[0.0] * rw for _ in range(rh)]
    for j in range(ch):
        for i in range(cw):
            x, y = ox + i - x0, oy + j - y0
            if 0 <= x < rw and 0 <= y < rh:
                c[y][x] = min(1.0, max(0.0, (cov.getpixel((i, j)) / 255 - 0.12) / 0.6))
    out = [[bg] * rw for _ in range(rh)]
    for y in range(rh):
        for x in range(rw):
            halo = any(c[yy][xx] > 0.3 for yy in range(max(0, y - 2), min(rh, y + 3))
                       for xx in range(max(0, x - 2), min(rw, x + 3)) if (xx - x) ** 2 + (yy - y) ** 2 <= 5)
            b = max(c[y][x], 0.1 if halo else 0.0)
            if b > 0.02:
                out[y][x] = min(ramp, key=lambda t: abs(t[0] - b * top))[1]
            if c[y][x] > 0.02:
                assert LIMIT[0] <= x + x0 <= LIMIT[2] and LIMIT[1] <= y + y0 <= LIMIT[3], (k, LABELS[k], x + x0, y + y0)
    return out


UI_TIM = 0x499800
UI_LABELS = ["Damage", "Critical", "Defense Damage", "Parry", "Clash"]   # rows y = 49 + 16 * i, 13 rows each
UI_X, UI_W, UI_H = 190, 66, 13
UI_CX, UI_FILL = 223, [15, 14, 13, 12, 11, 10]   # label centre x; fill index by row (light gradient: 6 px letters); outline index 2


def ui(i):
    d = gfx._file(str(ROOT / "work/disc/tree"), FILE)
    px = gfx.values(d, UI_TIM)
    y0 = 49 + 16 * i
    assert all(v == 0 for r in px[y0:y0 + UI_H] for v in r[:UI_X]) or True
    m = gfx.mask(UI_LABELS[i], "tiny5")[0]
    mh, mw = len(m), len(m[0])
    assert mw + 2 <= 61 and mh + 2 <= UI_H, (UI_LABELS[i], mw, mh)
    out = [[0] * UI_W for _ in range(UI_H)]
    tx, ty = UI_CX - UI_X - mw // 2, (UI_H - mh) // 2
    on = {(tx + a, ty + b) for b in range(mh) for a in range(mw) if m[b][a]}
    for (a, b) in {(a + p, b + q) for a, b in on for p in (-1, 0, 1) for q in (-1, 0, 1)} - on:
        out[b][a] = 2
    rows = sorted({b for _, b in on})
    for a, b in on:   # gradient spread over the label's rows
        out[b][a] = UI_FILL[round((b - rows[0]) * (len(UI_FILL) - 1) / max(1, rows[-1] - rows[0]))]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for i in range(len(UI_LABELS)):
        out = ui(i)
        im = Image.new("P", (UI_W, UI_H))
        im.putpalette([v for k in range(256) for v in (k, k, k)])
        im.putdata([v for r in out for v in r])
        im.save(OUT / ("ui%02d.png" % i))
    for k in range(16):
        out = render(k)
        im = Image.new("P", (RECT[2], RECT[3]))
        im.putpalette([v for i in range(256) for v in (i, i, i)])
        im.putdata([v for r in out for v in r])
        im.save(OUT / ("react%02d.png" % k))


if __name__ == "__main__":
    main()
