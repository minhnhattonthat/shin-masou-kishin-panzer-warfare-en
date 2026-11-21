"""status group (TIM.BIN 0xA5128, the status / spirit sheet; 34 identical copies are written by the build): draws every
label's English into gfx/out/status/<name>.png (palette indices only); --tsv also writes gfx/status.tsv.

    python -X utf8 tools/gfx_status.py [--tsv]

Every label is an `img` row: the sheet's labels sit on stone tiles, gold plates and a teal plate whose backdrop the text
rows can't keep, and one cap line per row of labels needs per-label baselines.
kinds:  plain  transparent (0) backdrop
        tile   stone tile: ink pixels (7 8 9 e f) are filled from the nearest backdrop pixel in their row
        teal   dark plate: every pixel that is not 7 / 9 is filled the same way
        gold   gold plate: backdrop = checkerboard of the plate's own clean top and bottom rows
        box    flat `a` box interior (the controls box)
Values (CLUT 0): e = light label face, 7 = dark shadow, f = white, 6 = pale gold, 3 = dark gold, 9 = box shadow."""
import argparse
import random
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
import tim  # noqa: E402

FILE, OFF, CLUT = "TIM.BIN", 0xA5128, 0
OUT = ROOT / "gfx/out/status"
FONTS = {"tiny5": ("tiny5/Tiny5.ttf", 8, None), "silk": ("silkscreen/Silkscreen-Regular.ttf", 8, None),
         "pix9": ("pixelifysans/PixelifySans[wght].ttf", 9, 500)}

# name, x, y, w, h, text ('|' = new line), font, kind, ink, edge (value of the 1 px down-right shadow, None = none),
# align, jp
SPEC = [
    # title plates
    ("status", 12, 5, 55, 10, "Status", "vwf", "teal", 14, 7, "c", "ステータス"),
    ("pilot", 74, 2, 36, 14, "Pilot", "vwf", "gold", 6, 3, "c", "操者"),
    ("machine", 114, 2, 36, 14, "Unit", "vwf", "gold", 6, 3, "c", "機体"),
    ("attacks_tab", 154, 2, 52, 14, "Attacks", "vwf", "gold", 6, 3, "c", "攻撃技"),
    ("attacks_hd", 88, 117, 50, 11, "Attacks", "vwf", "teal", 14, 7, "c", "攻 撃 技"),
    # pilot stats
    ("melee", 0, 33, 24, 13, "Melee", "tiny5", "plain", 14, 7, "c", "格闘"),
    ("ranged", 24, 33, 25, 13, "Ranged", "tiny5", "plain", 14, 7, "l", "射撃"),
    ("clash", 49, 33, 47, 13, "Clash", "tiny5", "plain", 14, 7, "l", "せりあい"),
    ("aim", 0, 49, 24, 14, "Aim", "tiny5", "plain", 14, 7, "c", "命中"),
    ("evade", 24, 49, 24, 14, "Evade", "tiny5", "plain", 14, 7, "c", "回避"),
    ("parry", 49, 49, 47, 14, "Parry", "tiny5", "plain", 14, 7, "l", "きり払い"),
    ("luck", 1, 65, 13, 13, "Luk", "tiny5", "plain", 14, 7, "l", "運"),
    ("spirit", 25, 65, 24, 13, "Spirit", "tiny5", "plain", 14, 7, "c", "精神"),
    ("prana_heal", 49, 65, 47, 13, "Prana Heal", "tiny5", "plain", 14, 7, "l", "プラーナ回復"),
    # machine stats
    ("armor", 32, 81, 24, 14, "Armor", "tiny5", "plain", 14, 7, "l", "装甲"),
    ("move", 0, 96, 24, 14, "Move", "tiny5", "plain", 14, 7, "c", "移動"),
    ("reflex", 32, 96, 24, 14, "Reflex", "tiny5", "plain", 14, 7, "l", "反応"),
    ("terrain", 0, 110, 24, 16, "Terrain", "tiny5", "plain", 14, 7, "l", "適応"),
    ("air", 34, 113, 12, 13, "Air", "tiny5", "plain", 14, 7, "l", "空"),
    ("ground", 50, 113, 13, 13, "Gnd", "tiny5", "plain", 14, 7, "l", "地"),
    ("sea", 66, 113, 13, 13, "Sea", "tiny5", "plain", 14, 7, "l", "水"),
    # remaining points, controls box
    ("remaining", 4, 130, 51, 13, "Remaining|Points", "tiny5", "plain", 15, None, "c", "残りポイント"),
    ("confirm", 172, 212, 56, 9, "=CONFIRM", "silk", "box", 15, 9, "l", "○ボタンで決定"),
]
# spirit command tiles: (name, tile x, tile y, text, jp); the tile's interior is 29 x 14
TILES = [("valor", 64, 16, "Valor", "熱血"), ("alert", 152, 16, "Alert", "閃き"), ("focus", 184, 16, "Focus", "集中"),
         ("guts", 216, 16, "Guts", "根性"), ("gain", 120, 32, "Gain", "努力"), ("strike", 152, 32, "Strike", "必中"),
         ("trust", 184, 32, "Trust", "信頼"), ("ironwall", 216, 32, "Iron Wall", "鉄壁"),
         ("grit", 152, 48, "Grit", "ド根性"), ("pranaheal", 184, 48, "Prana|Heal", "P回復"),
         ("spellbind", 216, 48, "Spell|bind", "呪縛"), ("soul", 120, 64, "Soul", "魂"),
         ("disrupt", 152, 64, "Disrupt", "撹乱"), ("friendship", 184, 64, "Friend|ship", "友情"),
         ("love", 216, 64, "Love", "愛")]
for n, tx, ty, t, jp in TILES:
    SPEC.append((n, tx + 2, ty + 1, 29, 14, t, "tiny5", "tile", 14, 7, "c", jp))


def _bitmap(f, t):
    asc = f.getmetrics()[0]
    img = Image.new("1", (max(f.getbbox(t)[2], 1) + 2, asc + 8))
    dr = ImageDraw.Draw(img)
    dr.fontmode = "1"
    dr.text((0, 0), t, font=f, fill=1)
    px = img.load()
    m = [[px[x, y] for x in range(img.width)] for y in range(img.height)]
    cols = [x for x in range(img.width) if any(r[x] for r in m)]
    return [r[cols[0]:cols[-1] + 1] for r in m] if cols else [[]]


def _render(text, font):
    """(rows, cap_top, cap_h): bitmap rows (0/1) of text, columns trimmed, rows keep the font's own vertical layout."""
    if font == "vwf":  # the game's own 12 px Latin
        m, h = gfx._mask_vwf(text), gfx._mask_vwf("H")
    else:
        path, size, wght = FONTS[font]
        f = ImageFont.truetype(str(ROOT / "fonts" / path), size)
        if wght:
            f.set_variation_by_axes([wght])
        m, h = _bitmap(f, text), _bitmap(f, "H")
    rows = [i for i, r in enumerate(h) if any(r)]
    return m, rows[0], rows[-1] - rows[0] + 1


def _fill_rows(grid, is_ink, rnd, reach=6):
    """Replace every ink pixel by a random non-ink pixel of its row within `reach` columns (keeps the row's tone and
    noise, no streaks); a row with none takes the column's first non-ink pixel."""
    h, w = len(grid), len(grid[0])
    src = [r[:] for r in grid]
    for j in range(h):
        for i in range(w):
            if not is_ink(src[j][i]):
                continue
            cand = [src[j][k] for k in range(max(0, i - reach), min(w, i + reach + 1)) if not is_ink(src[j][k])]
            while not cand and reach < w:
                reach += 2
                cand = [src[j][k] for k in range(max(0, i - reach), min(w, i + reach + 1)) if not is_ink(src[j][k])]
            grid[j][i] = rnd.choice(cand) if cand else next(src[k][i] for k in range(h) if not is_ink(src[k][i]))


def draw_one(px, spec):
    name, x, y, w, h, text, font, kind, ink, edge, align, jp = spec
    grid = [px[y + j][x:x + w] for j in range(h)]
    if kind == "plain":
        grid = [[0] * w for _ in range(h)]
    elif kind == "tile":  # ink 7 8 9 e f, plus the b/c/d anti-aliasing touching an e / f pixel
        snap = [r[:] for r in grid]
        for j in range(h):
            for i in range(w):
                if snap[j][i] in (11, 12, 13) and any(
                        snap[b][a] in (14, 15) for b in range(max(0, j - 1), min(h, j + 2))
                        for a in range(max(0, i - 1), min(w, i + 2))):
                    grid[j][i] = 14
        _fill_rows(grid, lambda v: v in (7, 8, 9, 14, 15), random.Random(name))
    elif kind == "teal":
        _fill_rows(grid, lambda v: v not in (7, 9), random.Random(name))
    elif kind == "gold":  # the plate's own clean first and last rows, mixed at random: keeps its horizontal gradient
        top, bot = px[y][x:x + w], px[y + h - 1][x:x + w]
        rnd = random.Random(name)
        grid = [[top[i] if rnd.random() < 0.5 else bot[i] for i in range(w)] for j in range(h)]
    elif kind == "box":
        grid = [[0xA] * w for _ in range(h)]
    lines = text.split("|")
    rend = [_render(t, font) for t in lines]
    cap_h = rend[0][2]
    gap = 1
    total = cap_h * len(lines) + gap * (len(lines) - 1)
    cap0 = (h - total) // 2
    for n, (m, ct, ch) in enumerate(rend):
        tw = len(m[0]) + (1 if edge is not None else 0)
        x0 = {"l": 0, "c": (w - tw) // 2, "r": w - tw}[align]
        y0 = cap0 + n * (cap_h + gap) - ct
        on = {(x0 + i, y0 + j) for j, r in enumerate(m) for i, v in enumerate(r) if v}
        sh = {(i + 1, j + 1) for i, j in on} - on if edge is not None else set()
        for i, j in on | sh:
            assert 0 <= i < w and 0 <= j < h, "%s: %r leaves its %dx%d rect (x %d..%d)" % (name, text, w, h, x0, x0 + tw)
        for i, j in sh:
            grid[j][i] = edge
        for i, j in on:
            grid[j][i] = ink
    return grid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", action="store_true")
    a = ap.parse_args()
    d = gfx._file(str(ROOT / "work/disc/tree"), FILE)
    px = gfx.values(d, OFF)
    cl = tim.parse(d, OFF)[1]
    pal = [c for k in range(16) for c in tim._rgb(struct.unpack_from("<H", d, cl + 2 * (CLUT * 16 + k))[0])[:3]]
    OUT.mkdir(parents=True, exist_ok=True)
    names = set()
    for spec in SPEC:
        name, x, y, w, h = spec[:5]
        assert name not in names
        names.add(name)
        grid = draw_one(px, spec)
        im = Image.new("P", (w, h))
        im.putpalette(pal + [0] * (768 - len(pal)))
        im.putdata([v for r in grid for v in r])
        im.save(OUT / (name + ".png"))
    if a.tsv:
        lines = ["\t".join("file tim x y w h clut text font ink edge bg align note".split())]
        for name, x, y, w, h, text, font, kind, ink, edge, align, jp in SPEC:
            lines.append("\t".join([FILE, "%X" % OFF, str(x), str(y), str(w), str(h), str(CLUT),
                                    "gfx/out/status/%s.png" % name, "img", "auto", "none", "auto", "center",
                                    "G9 %s -> %s%s" % (jp, text.replace("|", " "), " spill-ok row 211 is the line above's"
                                                       " shadow" if name == "confirm" else "")]))
        (ROOT / "gfx/status.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
