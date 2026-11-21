"""Story group images (gfx/story.tsv img rows). Palette indices only; run: python -X utf8 tools/gfx_story.py
Prologue pages: T_TIM.BIN 4 bpp 256x256, CLUT 0 = grey ramp (0 transparent, 1..14 dark..bright), 1:1 on screen.
Letters are drawn grey-antialiased (Nunito) and mapped to ramp indices 1..13, like the original mincho strokes."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402

OUT = ROOT / "gfx" / "out" / "story"
FONT = ROOT / "fonts/nunito/Nunito[wght].ttf"
SIZE, WGHT, PITCH = 12, 500, 15
TOP = 8  # y of the first line inside the rect (rect starts at y 16)
RY, RH = 16, 200  # prologue rect y/h (x 0, w 256)
MAXI = 13  # brightest ramp index used by letters (original stems are 0xD)
MAXW = 232  # widest line, px (the original's widest is ~225)
# paragraphs wrap greedily; "" = blank line; "<T>" = bracketed title line; ">T" = right-aligned line
PAGES = {
    "p0": ("T_TIM.BIN:000000", [
        "<A-Zeluth>",
        "",
        "A colossal floating continent, built on alchemy and sorcery, with ten thousand years of history, still "
        "drifting through the rifts between dimensions.",
        "",
        "That history was also one of strife between the people and the misshapen ones who rise from the Abyssal "
        "Pit, “Daus.”",
    ]),
    "p1": ("T_TIM.BIN:008800", [
        "The official histories record that the countless nations of today grew from small settlements "
        "(“communes”) that people built to pool their strength.",
        "",
        "But as if to mock their prosperity, the misshapen ones kept multiplying at a terrifying pace.",
    ]),
    "p2": ("T_TIM.BIN:011000", [
        "Megistus Calendar, Year 10093, Month 3. To a people who had lost every effective means against the "
        "misshapen ones, it fell.",
        "",
        "<The Arm of God>",
        "",
        "A giant mechanical arm, fallen from another world. Later generations would come to call it by this name.",
    ]),
    "p3": ("T_TIM.BIN:019800", [
        "Meanwhile, in the Holy Kingdom of Vartzpheem, where the Arm of God had fallen, the Arm was urgently "
        "analyzed with the backing of A-Zeluth's Alchemy Guild.",
        "",
        "From that technology were born the giant knights “Masouki,” built to stand against the "
        "misshapen ones.",
    ]),
    "p4": ("T_TIM.BIN:022000", [
        "Today, those who pilot Masouki and face the misshapen ones are called “Masou~Knights” because they "
        "carry on the will of the forebears who have stood against the misshapen since ancient times.",
        "", "", "", "", "",
        ">Megistus Calendar, Year 10099",
        ">Rieg Gram Garum",
    ]),
}


def font():
    f = ImageFont.truetype(str(FONT), SIZE)
    f.set_variation_by_axes([WGHT])
    return f


def brackets(d, x, y, h, left):
    """Corner bracket 『 or 』: two nested corners, 1 px strokes, ink 255."""
    s = 1 if left else -1
    for k, n in ((0, 5), (2, 3)):
        a = x + k * s
        d.line([(a, y + k), (a, y + h - 1 - k)], fill=255)
        d.line([(a, y + k), (a + n * s, y + k)], fill=255)
        d.line([(a, y + h - 1 - k), (a + n * s, y + h - 1 - k)], fill=255)


def wrap(paras, f):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    out = []
    for p in paras:
        if not p or p[0] in "<>":
            out.append(p)
            continue
        cur = ""
        for word in p.split(" "):  # "~" in a paragraph = a space that never breaks
            if cur and d.textlength((cur + " " + word).replace("~", " "), font=f) > MAXW:
                out.append(cur.replace("~", " "))
                cur = word
            else:
                cur = (cur + " " + word).strip()
        out.append(cur.replace("~", " "))
    return out


def render(lines, w, h, f):
    """L image w x h: lines centred ('>' = right aligned at w-12, '<..>' = bracketed title)."""
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for n, t in enumerate(lines):
        if not t:
            continue
        y = TOP + n * PITCH
        if t[0] == "<":
            t = t[1:-1]
            tw = d.textlength(t, font=f)
            x = (w - tw) / 2
            d.text((x, y), t, font=f, fill=255, anchor="la")
            brackets(d, int(x) - 10, y, 14, True)
            brackets(d, int(x + tw) + 9, y, 14, False)
        elif t[0] == ">":
            t = t[1:]
            d.text((w - 12 - d.textlength(t, font=f), y), t, font=f, fill=255, anchor="la")
        else:
            d.text(((w - d.textlength(t, font=f)) / 2, y), t, font=f, fill=255, anchor="la")
    return im


def to_index(im):
    return [min(MAXI, max(1, round((v / 255) ** 0.85 * MAXI))) if v > 24 else 0 for v in im.getdata()]


def page(name):
    sel, lines = PAGES[name]
    tmp = ROOT / "work/gfx/tmp_story/_t.png"
    gfx.export(sel, "0,%d,256,%d" % (RY, RH), 0, str(tmp))
    out = Image.open(tmp)
    ls = wrap(lines, font())
    assert TOP + len(ls) * PITCH <= RH, (name, len(ls))
    out.putdata(to_index(render(ls, 256, RH, font())))
    OUT.mkdir(parents=True, exist_ok=True)
    out.save(OUT / (name + ".png"))


# --- 16 bpp loading screens: erase the Japanese by diffusing the surrounding photo into it, then draw 8 px text ------

SHADOW = ((1, 0), (0, 1), (1, 1))  # the original's dark edge: right and below


def inpaint(a, mask, iters=600, seed=1):
    """a: float HxWx3 array, mask: bool HxW (pixels to rebuild). Jacobi diffusion + grain matched to the border."""
    import numpy as np
    a = a.copy()
    a[mask] = a[~mask].mean(axis=0)
    for _ in range(iters):
        p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 4
        a[mask] = avg[mask]
    # grain: std of (pixel - 3x3 mean) over the untouched pixels
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    loc = sum(p[1 + j:p.shape[0] - 1 + j, 1 + i:p.shape[1] - 1 + i] for j in (-1, 0, 1) for i in (-1, 0, 1)) / 9
    r = (a - loc).mean(axis=2)
    ref = np.zeros(mask.shape, bool)
    ref[:2], ref[-2:] = True, True  # the untouched rows above and below the text
    sd = 1.4826 * np.median(np.abs(r[ref] - np.median(r[ref])))
    a[mask] += np.random.default_rng(seed).normal(0, sd, (int(mask.sum()), 1))
    return a.clip(0, 255)


def overlay(sel, rect, name, lines, font_spec, ink, shadow, align, top, gap=1, yellow=False):
    """Rebuild rect of a 16 bpp TIM without its Japanese (light strokes + dark edge) and draw lines over it.
    align: 'right' (flush to the rect's right edge - 2) or 'left' (2 px in). top: y of the first line in the rect."""
    import numpy as np
    x, y, w, h = rect
    tmp = ROOT / "work/gfx/tmp_story/_o.png"
    gfx.export(sel, "%d,%d,%d,%d" % rect, 0, str(tmp))
    a = np.asarray(Image.open(tmp).convert("RGB")).astype(float)
    if yellow:  # the dev card's gold letters on a light sky
        white = (a[..., 0] > 200) & (a[..., 1] > 150) & (a[..., 2] < 130)
        dark = a.max(axis=2) < 115
    else:
        white = a.min(axis=2) > 170
        dark = a.max(axis=2) < 45
    near = np.zeros_like(white)
    for j in (-1, 0, 1):
        for i in (-1, 0, 1):
            near |= np.roll(np.roll(white, j, 0), i, 1)
    mask = white | (dark & near)
    grown = mask.copy()
    for _ in (0, 1):  # two rings: the soft fringe round each stroke
        m0 = grown.copy()
        for j in (-1, 0, 1):
            for i in (-1, 0, 1):
                grown |= np.roll(np.roll(m0, j, 0), i, 1)
    grown[[0, -1], :] = False  # the rect's own border stays original so the fill has something to match
    grown[:, [0, -1]] = False
    a = inpaint(a, grown)
    img = Image.fromarray(a.round().astype("uint8"))
    px = img.load()
    yy = top
    for t in lines:
        m = gfx.mask(t, font_spec)[0]
        mw = len(m[0])
        x0 = w - 2 - mw if align == "right" else 2
        on = {(x0 + i, yy + j) for j, row in enumerate(m) for i, v in enumerate(row) if v}
        for (i, j) in {(i + a_, j + b_) for i, j in on for a_, b_ in SHADOW} - on:
            if 0 <= i < w and 0 <= j < h:
                px[i, j] = shadow
        for i, j in on:
            px[i, j] = ink
        yy += len(m) + gap
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / (name + ".png"))


def loading():
    # BAT_TIM 0x4D5000 "overlay file loading..." (two 8 px lines, right part of the screen)
    overlay("BAT_TIM.BIN:4D5000", (208, 199, 94, 21), "loading", ["Loading overlay", "file..."], "tiny5",
            (248, 248, 248), (0, 0, 0), "right", 3, gap=3)
    # BAT_TIM 0x45A000 dev card (probably never shown): "第1制作チーム" top left, gold with a dark edge
    overlay("BAT_TIM.BIN:45A000", (4, 10, 120, 22), "devcard", ["Production Team 1"], "vwf",
            (248, 192, 64), (72, 72, 88), "left", 6, yellow=True)


if __name__ == "__main__":
    for n in PAGES:
        page(n)
    loading()
