"""Graphics-text redraws (docs/re/graphics.md): English labels drawn into the game's TIMs in pixel-value space
(palette indices for 4/8 bpp, raw 15-bit colours for 16 bpp), so no colour round trip can pick a wrong index.

gfx/<group>.tsv (cards.tsv is the pilot), one row per label (tab-separated, header line):
  file tim x y w h clut text font ink edge bg align note
  file, tim   disc file and hex offset of the TIM (the original's offset; every copy of its pixel block is written)
  x y w h     clear rect in TIM pixels: covers every original glyph (`gfx.py check` runs rectcover on it)
  clut        CLUT the game draws this rect with (preview only)
  text        English; `|` breaks lines; empty = clear only
  font        vwf (the game's 12 px Latin cells) | tiny5 | silk | <dir/file.ttf>:SIZE[:wght] under fonts/
  ink         value of the letters; auto = commonest non-background value in the original rect
  edge        none | shadow:V (1 px down-right) | outline:V (8-neighbour) | shadow2:V (down-right + right)
  bg          auto (commonest value on the rect's border) | rows (per row: commonest of that row's two side
              pixels, keeps vertical gradients) | V
  align       center | left | right, plus optional `,dy=N` / `,dx=N` nudges
Hex values: 0x..; decimals otherwise.

    python -X utf8 tools/gfx.py preview [FILE:OFF..]   -> work/gfx/preview/<file>_<off>.png (JP | EN, x3)
    python -X utf8 tools/gfx.py check                  rectcover + fit + no change outside rects; exit 1 on a problem
Library: apply(tree, log) is the build stage; ranges(orig_tree) -> {file: [(a, b)]} for tools/writes_check.py."""
import argparse
import collections
import csv
import struct
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import font  # noqa: E402
import rectcover  # noqa: E402
import tim  # noqa: E402

ROWS = ROOT / "gfx"  # one <group>.tsv per redraw group
FILES = ("T_TIM.BIN", "TIM.BIN", "BAT_TIM.BIN", "GRA5.BIN")
FONTS = {"tiny5": ("tiny5/Tiny5.ttf", 8), "silk": ("silkscreen/Silkscreen-Regular.ttf", 8)}


def num(s):
    return int(s, 0)


GROUP = None  # gfx.py --group NAME: only gfx/NAME.tsv


def rows():
    out = []
    for p in sorted(ROWS.glob("*.tsv")):
        if GROUP and p.stem != GROUP:
            continue
        with open(p, encoding="utf-8", newline="") as f:
            rs = list(csv.DictReader(f, delimiter="\t"))
        for r in rs:
            assert None not in r.values() and len(r) == 14, "%s: 14 columns per row: %r" % (p.name, r)
            r["group"] = p.stem
        out += rs
    return out


def by_tim(rs):
    g = collections.defaultdict(list)
    for r in rs:
        g[(r["file"], int(r["tim"], 16))].append(r)
    return g


# --- TIM pixel values ---------------------------------------------------------------------------------------------

def info(d, off):
    fl, clut, nclut, po, w, h, _ = tim.parse(d, off)
    bpp = {0: 4, 1: 8, 2: 16}[fl & 3]
    return bpp, po, w, h, w * h * bpp // 8


def values(d, off):
    bpp, po, w, h, n = info(d, off)
    if bpp == 4:
        flat = [v for b in d[po:po + n] for v in (b & 15, b >> 4)]
    elif bpp == 8:
        flat = list(d[po:po + n])
    else:
        flat = list(struct.unpack_from("<%dH" % (w * h), d, po))
    return [flat[y * w:(y + 1) * w] for y in range(h)]


def pack(px, bpp):
    flat = [v for r in px for v in r]
    if bpp == 4:
        return bytes(flat[i] | flat[i + 1] << 4 for i in range(0, len(flat), 2))
    if bpp == 8:
        return bytes(flat)
    return struct.pack("<%dH" % len(flat), *flat)


# --- text masks ---------------------------------------------------------------------------------------------------

@lru_cache(None)
def _vwf():
    t = ROOT / "work/disc/tree"
    d, exe = (t / "BAT_TIM.BIN").read_bytes(), (t / "SLPS_023.19").read_bytes()
    off = font.TIM_OFFS["BAT_TIM.BIN"]
    return d, font._po(d, off), font.tables(d, off, exe), font._cells(exe)


def _mask_vwf(text):
    d, po, (code, width), cells = _vwf()
    cols = []
    for b in font.encode(text):
        if not code[b]:
            cols += [[0] * font.CELL] * width[b]
            continue
        c, r = cells[code[b]]
        x0, y0 = c * font.CELL, r * font.CELL
        ink = [x for x in range(font.CELL) if any(font._pix(d, po, x0 + x, y0 + y) for y in range(font.CELL))]
        for x in range(ink[0], ink[0] + width[b]):
            cols.append([font._pix(d, po, x0 + x, y0 + y) if x < font.CELL else 0 for y in range(font.CELL)])
    while cols and not any(cols[-1]):
        cols.pop()
    return [[c[y] for c in cols] for y in range(font.CELL)] if cols else [[]]


def _mask_ttf(text, spec):
    from PIL import Image, ImageDraw, ImageFont
    path, size, *wght = spec.split(":") if ":" in spec else (FONTS[spec][0], FONTS[spec][1])
    f = ImageFont.truetype(str(ROOT / "fonts" / path), int(size))
    if wght:
        f.set_variation_by_axes([int(wght[0])])
    l, t, r, b = f.getbbox(text)
    asc = f.getmetrics()[0]
    img = Image.new("1", (max(r, 1), asc + 8))
    dr = ImageDraw.Draw(img)
    dr.fontmode = "1"
    dr.text((0, 0), text, font=f, fill=1)
    px = img.load()
    m = [[px[x, y] for x in range(img.width)] for y in range(img.height)]
    while m and not any(m[-1]):
        m.pop()
    top = next((i for i, row in enumerate(m) if any(row)), 0)
    m = m[top:]
    cols = [x for x in range(img.width) if any(row[x] for row in m)]
    return [row[cols[0]:cols[-1] + 1] for row in m] if cols else [[]]


def mask(text, spec):
    lines = [(_mask_vwf(t) if spec == "vwf" else _mask_ttf(t, spec)) if t else [[]] for t in text.split("|")]
    return lines


# --- drawing ------------------------------------------------------------------------------------------------------

def _common(vals):
    return collections.Counter(vals).most_common(1)[0][0]


def draw(px, r):
    """Clear r's rect and draw its text, in place. Returns (text_w, text_h) for the fit check."""
    x, y, w, h = (num(r[k]) for k in "xywh")
    border = [px[y][i] for i in range(x, x + w)] + [px[y + h - 1][i] for i in range(x, x + w)] + \
        [px[j][x] for j in range(y, y + h)] + [px[j][x + w - 1] for j in range(y, y + h)]
    if r["bg"] == "rows":
        bgs = [_common([px[j][x], px[j][x + w - 1]]) for j in range(y, y + h)]
    else:
        bg = _common(border) if r["bg"] == "auto" else num(r["bg"])
        bgs = [bg] * h
    orig = [px[j][x:x + w] for j in range(y, y + h)]
    if r["ink"] == "auto":
        ink = _common([v for j, row in enumerate(orig) for v in row if v != bgs[j]] or [bgs[0]])
    else:
        ink = num(r["ink"])
    for j in range(h):
        px[y + j][x:x + w] = [bgs[j]] * w
    if not r["text"]:
        return 0, 0
    lines = mask(r["text"], r["font"])
    al, *nudge = r["align"].split(",")
    nd = dict(n.split("=") for n in nudge)
    lh = max(len(m) for m in lines)
    gap = int(nd.get("gap", 1))
    tw, th = max(len(m[0]) for m in lines), lh * len(lines) + gap * (len(lines) - 1)
    ek, ev = (r["edge"].split(":") + [None])[:2]
    if ev == "auto":  # commonest original value that is neither background nor ink
        ev = str(_common([v for j, row in enumerate(orig) for v in row if v not in (bgs[j], ink)] or [ink]))
    pad = {"none": (0, 0), "shadow": (1, 1), "shadow2": (1, 1), "outline": (2, 2)}[ek]
    y0 = y + (int(nd["top"]) if "top" in nd else (h - th - pad[1]) // 2) + (1 if ek == "outline" else 0) + \
        int(nd.get("dy", 0))
    for k, m in enumerate(lines):
        mw = len(m[0])
        x0 = {"center": x + (w - mw - pad[0]) // 2 + (1 if ek == "outline" else 0), "left": x + (1 if ek == "outline" else 0),
              "right": x + w - mw - pad[0] + (1 if ek == "outline" else 0)}[al] + int(nd.get("dx", 0))
        yy = y0 + k * (lh + gap)
        on = {(x0 + i, yy + j) for j, row in enumerate(m) for i, v in enumerate(row) if v}
        if ek != "none":
            off = {"shadow": [(1, 1)], "shadow2": [(1, 1), (1, 0)],
                   "outline": [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]}[ek]
            for (i, j) in {(i + a, j + b) for i, j in on for a, b in off} - on:
                if x <= i < x + w and y <= j < y + h:
                    px[j][i] = num(ev)
        for i, j in on:
            if x <= i < x + w and y <= j < y + h:
                px[j][i] = ink
    return tw + pad[0] + abs(int(nd.get("dx", 0))), th + pad[1] + int(nd.get("top", 0)) + abs(int(nd.get("dy", 0)))


def redraw(d, off, rs):
    """(new pixel bytes, [(row, fits)]) for the TIM at off with rows rs."""
    bpp = info(d, off)[0]
    px = values(d, off)
    fit = []
    for r in rs:
        tw, th = draw(px, r)
        fit.append((r, tw <= num(r["w"]) and th <= num(r["h"])))
    return pack(px, bpp), fit


# --- copies, build stage, ranges ----------------------------------------------------------------------------------

@lru_cache(None)
def _file(tree, name):
    return (Path(tree) / name).read_bytes()


def copies(tree, file, off):
    """[(file, pixel offset)] of every copy of this TIM's pixel block in the disc's image files."""
    d = _file(str(tree), file)
    _, po, _, _, n = info(d, off)
    blk, out = d[po:po + n], []
    for name in FILES:
        f, i = _file(str(tree), name), -1
        while (i := f.find(blk, i + 1)) >= 0:
            out.append((name, i))
    assert (file, po) in out
    return out


def apply(tree, log=None):
    """Build stage: every TIM with rows is redrawn (from the original disc in work/disc/tree) into all its copies."""
    import insert
    orig = ROOT / "work/disc/tree"
    new = {}
    for (file, off), rs in by_tim(rows()).items():
        pix, _ = redraw(_file(str(orig), file), off, rs)
        for name, po in copies(orig, file, off):
            new.setdefault(name, []).append((po, pix))
    for name, ws in new.items():
        p = Path(tree) / name
        old = p.read_bytes()
        d = bytearray(old)
        for po, pix in ws:
            d[po:po + len(pix)] = pix
        p.write_bytes(bytes(d))
        if log is not None:
            insert.log_diff(log, name, old, bytes(d), "gfx")
    return sorted(new)


def ranges(orig_tree):
    out = collections.defaultdict(list)
    for (file, off), _ in by_tim(rows()).items():
        n = info(_file(str(orig_tree), file), off)[4]
        for name, po in copies(orig_tree, file, off):
            out[name].append((po, po + n))
    return out


# --- preview / check ----------------------------------------------------------------------------------------------

def image(d, off, px, clut):
    from PIL import Image
    bpp, _, w, h, _ = info(d, off)
    _, cl, _, _, _, _, _ = tim.parse(d, off)
    img = Image.new("RGB", (w, h))
    if bpp == 16:
        pal = None
    else:
        n = 16 if bpp == 4 else 256
        pal = [tim._rgb(struct.unpack_from("<H", d, cl + 2 * (clut * n + k))[0])[:3] for k in range(n)]
    img.putdata([pal[v] if pal else tim._rgb(v)[:3] for row in px for v in row])
    return img


def preview(sel, zoom=3):
    from PIL import Image
    orig = ROOT / "work/disc/tree"
    out = ROOT / "work/gfx/preview"
    out.mkdir(parents=True, exist_ok=True)
    for (file, off), rs in by_tim(rows()).items():
        if sel and "%s:%X" % (file, off) not in sel:
            continue
        d = _file(str(orig), file)
        pix, _ = redraw(d, off, rs)
        bpp, po, _, _, _ = info(d, off)
        nd = d[:po] + pix + d[po + len(pix):]
        clut = num(rs[0]["clut"])
        a, b = image(d, off, values(d, off), clut), image(nd, off, values(nd, off), clut)
        # crop to the union of the rects (+8) so small labels stay readable
        x0 = max(0, min(num(r["x"]) for r in rs) - 8)
        y0 = max(0, min(num(r["y"]) for r in rs) - 8)
        x1 = min(a.width, max(num(r["x"]) + num(r["w"]) for r in rs) + 8)
        y1 = min(a.height, max(num(r["y"]) + num(r["h"]) for r in rs) + 8)
        a, b = a.crop((x0, y0, x1, y1)), b.crop((x0, y0, x1, y1))
        s = Image.new("RGB", (a.width * 2 + 4, a.height), (255, 0, 255))
        s.paste(a, (0, 0))
        s.paste(b, (a.width + 4, 0))
        p = out / ("%s_%X.png" % (file.split(".")[0], off))
        s.resize((s.width * zoom, s.height * zoom), Image.NEAREST).save(p)
        print(p.relative_to(ROOT))


def check():
    orig = ROOT / "work/disc/tree"
    bad = 0
    for (file, off), rs in by_tim(rows()).items():
        d = _file(str(orig), file)
        px = values(d, off)
        pix, fit = redraw(d, off, rs)
        bpp, po, w, h, _ = info(d, off)
        npx = values(d[:po] + pix + d[po + len(pix):], off)
        rects = [tuple(num(r[k]) for k in "xywh") for r in rs]
        for r, ok in fit:
            if not ok:
                print("%s:%X %r: text does not fit its %sx%s rect" % (file, off, r["text"], r["w"], r["h"]))
                bad = 1
        for r, rect in zip(rs, rects):
            if "spill-ok" in r["note"]:
                continue
            le, ri, to, bo, joins = rectcover.spill(px, rect)
            if (le or ri or to or bo) and not joins:
                print("%s:%X %r: original text runs past the rect by l%d r%d t%d b%d" % (file, off, r["text"], le, ri, to, bo))
                bad = 1
        for yy in range(h):
            for xx in range(w):
                if px[yy][xx] != npx[yy][xx] and not any(a <= xx < a + c and b <= yy < b + e for a, b, c, e in rects):
                    print("%s:%X pixel %d,%d changed outside every rect" % (file, off, xx, yy))
                    return 1
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("preview", "check"))
    ap.add_argument("sel", nargs="*")
    ap.add_argument("--group", help="only gfx/GROUP.tsv")
    a = ap.parse_intermixed_args()
    global GROUP
    GROUP = a.group
    if a.cmd == "preview":
        preview(set(a.sel))
    else:
        bad = check()
        print("gfx check", "FAIL" if bad else "ok", "(%d rows)" % len(rows()))
        sys.exit(bad)


if __name__ == "__main__":
    main()
