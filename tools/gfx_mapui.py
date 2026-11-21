"""mapui group (GRA5 0x11000, the map command / info atlas): draws every label's English into gfx/out/mapui/<name>.png
(palette indices only); --tsv also writes gfx/mapui.tsv.

    python -X utf8 tools/gfx_mapui.py [--tsv]

Every label is an `img` row because the sheet needs per-label baselines (tiny5 caps all share one cap line per row of
labels) and gradient/bar backdrops that the text rows can't keep. Index values: 15 = white text, 1 = dark outline and
button text (CLUTs invert it per palette, the relation to the backdrop stays the same)."""
import argparse
import collections
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402

FILE, OFF, CLUT = "GRA5.BIN", 0x11000, 9
OUT = ROOT / "gfx/out/mapui"

# name, x, y, w, h, text, font, kind, ink, align, jp
# kind: w = on transparent (0), btn = gradient button, bar = dim bar under the text (rows from the left column),
#       ol = text with a 1-index outline.  align: l | c | r, optional ",dx=N"
W, OLK = 15, 1
BTN1 = [("移動", "Move"), ("飛行", "Fly"), ("着陸", "Land"), ("精神", "Spirit"), ("待機", "Wait"), ("データ", "Data"),
        ("システム", "System")]
BTN2 = [("攻撃", "Attack"), ("浮上", "Surface"), ("潜水", "Dive"), ("能力", "Ability"), ("終了", "End"),
        ("目的", "Goal"), ("セーブ", "Save")]
SPEC = []
for r, (y, names) in enumerate(((65, BTN1), (81, BTN2))):
    for k, (jp, en) in enumerate(names):
        SPEC.append(("btn_%d_%d" % (r, k), 32 * k + 1, y, 29, 13, en, "tiny5", "btn", 1, "c", jp))
SPEC += [
    # unit info row
    ("pos", 83, 17, 27, 12, "Place:", "tiny5", "w", W, "l", "位置:"),
    ("spirit_p", 112, 17, 31, 12, "Spirit P:", "tiny5", "w", W, "l", "精神P:"),
    ("air", 147, 17, 24, 12, "Air", "tiny5", "w", W, "c", "空中"),
    ("ground", 179, 17, 24, 12, "Ground", "tiny5", "w", W, "c", "地上"),
    ("water", 211, 17, 24, 12, "Water", "tiny5", "w", W, "c", "水中"),
    # terrain window
    ("terrain_info", 194, 33, 61, 14, "Terrain Info", "tiny5", "ol", W, "c", "地形情報"),
    ("terrain_fx", 194, 49, 61, 14, "Terrain Effects", "tiny5", "ol", W, "c", "地形効果"),
    ("height", 225, 65, 30, 13, "Height:", "tiny5", "w", W, "l", "高さ:"),
    ("movecost", 225, 81, 30, 13, "Move:", "tiny5", "w", W, "l", "移動:"),
    # date strip: の between the bold digits, 月, 日, 光の日, 闇の日
] + [("no_%d" % k, 9 + 16 * k, 100, 7, 8, "/", "slash", "w", W, "c", "の") for k in range(7)] + [
    ("month", 113, 97, 11, 14, "Mo", "tiny5", "w", W, "c", "月"),
    ("day", 129, 97, 10, 14, "Dy", "tiny5", "w", W, "c", "日"),
    ("lightday", 168, 97, 29, 12, "Lightday", "tiny5", "w", 13, "l", "光の日"),
    ("darkday", 200, 97, 29, 12, "Darkday", "tiny5", "w", 12, "l", "闇の日"),
    # time of day, turns, terrain effect heads
    ("t_morning", 1, 113, 21, 13, "/Dawn", "tiny5", "w", W, "l", "/朝"),
    ("t_noon", 25, 113, 21, 13, "/Noon", "tiny5", "w", W, "l", "/昼"),
    ("t_dusk", 49, 113, 20, 13, "/Dusk", "tiny5", "w", W, "l", "/夕"),
    ("t_night", 73, 113, 21, 13, "/Night", "tiny5", "w", W, "l", "/夜"),
    ("t_dark", 97, 113, 21, 13, "/Dark", "tiny5", "w", W, "l", "/闇"),
    ("turns", 120, 113, 39, 13, "Turns:", "tiny5", "w", W, "l", "ターン数:"),
    ("h_fly", 162, 113, 11, 13, "Air", "tiny5", "w", W, "l", "飛"),
    ("h_ground", 178, 113, 12, 13, "Gnd", "tiny5", "w", W, "l", "地"),
    ("h_dive", 194, 113, 12, 13, "Sea", "tiny5", "w", W, "l", "潜"),
    ("h_def", 208, 113, 15, 13, "Def:", "tiny5", "w", W, "r", "防:"),
    ("h_eva", 224, 113, 15, 13, "Eva:", "tiny5", "w", W, "r", "回:"),
    ("h_spc", 240, 113, 15, 13, "Spc:", "tiny5", "w", W, "r", "特:"),
    # spirit points, hit rate, adaptation row
    ("spirit_pts", 162, 130, 53, 13, "Spirit Points", "tiny5", "w", W, "l", "精神ポイント"),
    ("hitrate", 161, 177, 46, 16, "Hit Rate", "vwf", "bar", W, "c", "命中率"),
    ("a_ground", 164, 194, 12, 11, "Gnd", "tiny5", "w", W, "l", "地"),
    ("a_air", 180, 194, 24, 11, "Air", "tiny5", "w", W, "c", "空中"),
    ("a_water", 212, 194, 24, 11, "Water", "tiny5", "w", W, "c", "水中"),
    # yes / no
    ("yes", 0, 189, 32, 16, "YES", "vwf", "w", W, "c", "はい"),
    ("no", 0, 209, 32, 13, "NO", "vwf", "w", W, "c", "いいえ"),
    # battle confirm
    ("attack", 1, 226, 25, 12, "Attack", "tiny5", "w", W, "l", "攻撃"),
    ("target", 34, 226, 24, 12, "Target", "tiny5", "w", W, "l", "受け"),
    ("front", 69, 226, 25, 12, "Front", "tiny5", "w", W, "l", "正面"),
    ("side", 100, 226, 26, 12, "Side", "tiny5", "w", W, "l", "側面"),
    ("rear", 132, 226, 26, 12, "Rear", "tiny5", "w", W, "l", "背面"),
    ("anim", 161, 226, 38, 12, "Battle|Animation", "tiny5", "w", W, "l", "戦闘アニメ"),
    ("start", 5, 241, 55, 13, "Start Battle", "tiny5", "w", W, "c", "戦闘開始"),
    ("weapon", 80, 241, 31, 13, "Weapon", "tiny5", "w", W, "c", "武器"),
    ("evade", 145, 241, 30, 13, "Evade", "tiny5", "w", W, "c", "回避"),
    ("defend", 208, 241, 31, 13, "Defend", "tiny5", "w", W, "c", "防御"),
]


def _render(text, font):
    """(rows, cap_top, cap_h): bitmap rows (0/1) of text, columns trimmed, rows keep the font's own vertical layout."""
    if font == "slash":  # a tall 7 x 8 slash, as high as the の it replaces
        return [[int(c == round(5 - r * 4 / 7)) for c in range(7)] for r in range(8)], 0, 8
    if font == "vwf":
        m = gfx._mask_vwf(text)
        h = gfx._mask_vwf("H")
    else:
        f = ImageFont.truetype(str(ROOT / "fonts/tiny5/Tiny5.ttf"), 8)

        def bm(t):
            asc = f.getmetrics()[0]
            img = Image.new("1", (max(f.getbbox(t)[2], 1) + 2, asc + 8))
            dr = ImageDraw.Draw(img)
            dr.fontmode = "1"
            dr.text((0, 0), t, font=f, fill=1)
            px = img.load()
            m = [[px[x, y] for x in range(img.width)] for y in range(img.height)]
            cols = [x for x in range(img.width) if any(r[x] for r in m)]
            return [r[cols[0]:cols[-1] + 1] for r in m] if cols else [[]]
        m, h = bm(text), bm("H")
    rows = [i for i, r in enumerate(h) if any(r)]
    return m, rows[0], rows[-1] - rows[0] + 1


def draw_one(px, spec):
    name, x, y, w, h, text, font, kind, ink, align, jp = spec
    grid = [[0] * w for _ in range(h)]
    if kind == "btn":  # per-column gradient from the button's own top / bottom edge rows, checkerboard where they differ
        mains = []
        for i in range(w):
            c = collections.Counter(px[j][x + i] for j in range(y, y + h) if 9 <= px[j][x + i] <= 14).most_common(1)
            mains.append(c[0][0] if c else None)
        for i in range(w):  # a column that is all ink takes its left neighbour's value
            if mains[i] is None:
                mains[i] = mains[i - 1] if i else mains[1]
        for i in range(w):
            main = mains[i]
            # an edge row with ink in it (v < 9) or the corner f falls back to the column's commonest value
            t, b = (px[y - 1][x + i], px[y + h][x + i]) if x % 32 + i >= 2 else (main, main)
            t, b = (t if 9 <= t <= 14 else main), (b if 9 <= b <= 14 else main)
            for j in range(h):
                grid[j][i] = t if (i + j) % 2 == 0 else b
    elif kind == "bar":  # dim bar: rows keep the left column's value
        for j in range(h):
            grid[j] = [px[y + j][x]] * w
    lines = text.split("|")
    rend = [_render(t, font) for t in lines]
    cap_h = rend[0][2]
    nl = len(lines)
    total = cap_h * nl + (nl - 1) * (1 if font == "tiny5" else 2)
    pad = 1 if kind in ("ol", "bar") else 0
    cap0 = y + (h - total) // 2 - y  # cap top of the first line, relative to the rect
    for n, (m, ct, ch) in enumerate(rend):
        tw = len(m[0])
        dx = int(align.split("dx=")[1]) if "dx=" in align else 0
        a = align[0]
        x0 = {"l": pad, "c": (w - tw) // 2, "r": w - tw - pad}[a] + dx
        if a == "c" and pad:
            x0 = (w - tw) // 2
        y0 = cap0 + n * (cap_h + (1 if font == "tiny5" else 2)) - ct
        on = {(x0 + i, y0 + j) for j, r in enumerate(m) for i, v in enumerate(r) if v}
        assert all(0 <= i < w and 0 <= j < h for i, j in on), "%s: text %r leaves its %dx%d rect (x %d..%d)" % (
            name, text, w, h, x0, x0 + tw)
        if kind in ("ol", "bar"):
            for i, j in {(i + a_, j + b_) for i, j in on for a_ in (-1, 0, 1) for b_ in (-1, 0, 1)} - on:
                if 0 <= i < w and 0 <= j < h:
                    grid[j][i] = OLK
        for i, j in on:
            grid[j][i] = ink
    return grid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", action="store_true")
    a = ap.parse_args()
    d = gfx._file(str(ROOT / "work/disc/tree"), FILE)
    px = gfx.values(d, OFF)
    import struct
    import tim
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
        for name, x, y, w, h, text, font, kind, ink, align, jp in SPEC:
            lines.append("\t".join([FILE, "%X" % OFF, str(x), str(y), str(w), str(h), str(CLUT),
                                    "gfx/out/mapui/%s.png" % name, "img", "auto", "none", "auto", "center",
                                    "G11 %s -> %s" % (jp, text.replace("|", " "))]))
        (ROOT / "gfx/mapui.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
