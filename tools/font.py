"""English VWF built from the game's own full-width Latin glyphs (docs/re/font.md §VWF).

The dialogue font TIM (BAT_TIM.BIN 0x480000, copy at GRA5.BIN 0x0) is 4bpp, 21 cells of 12x12 per row; each of the
4 bits of a pixel is a separate glyph page (the CLUT picked by the glyph table selects the bit). English text is
single bytes; the renderer hook (asm/vwf.asm) maps each byte to a page-0 SJIS cell through CODE and advances the
pen by WIDTH. This module moves the ink of those cells to the cell's left edge (bit 0 only, other pages untouched)
and computes the widths.

Encoding (`encode`): printable ASCII as itself, except lowercase a-z at 0xA1-0xBA (byte + 0x40), because the
renderer keeps 0x62 0x68 0x6D 0x72 0x77 0x7A as colour / font-mode control letters (`{b}` ... in script text).

Usage: font.py --preview OUT.png [TEXT]   (renders TEXT with the patched cells, 2x)
Library: patch_tim(data, off) -> bytes, tables(data, off) -> (code[256], width[256]), encode(str) -> bytes."""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sjis  # noqa: E402
import tim  # noqa: E402

TIM_OFFS = {"BAT_TIM.BIN": 0x480000, "GRA5.BIN": 0x0}
GLYPH_TABLE = 0xB191C  # exe file offset: 164 x (u16 first, u8 tpage, u8 row, u16 page)
CELL = 12
SPACE = 4  # advance of ' '
GAP = 1  # blank columns after a glyph's ink
EXTRA = "…"  # characters beyond ASCII that get a cell (…)

# ASCII -> page-0 SJIS cell holding its glyph
_FW = {c: chr(ord(c) + 0xFEE0) for c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"}
_FW.update({"!": "！", '"': "”", "#": "＃", "$": "＄", "%": "％", "&": "＆", "'": "’", "(": "（", ")": "）",
            "*": "＊", "+": "＋", ",": "，", "-": "‐", ".": "．", "/": "／", ":": "：", ";": "；", "<": "＜",
            "=": "＝", ">": "＞", "?": "？", "@": "＠", "[": "［", "]": "］", "~": "～", "…": "…",
            "_": "＿", "^": "＾", "`": "‘", "|": "｜", "\\": "＼", "{": "｛", "}": "｝"})
LOWER_SHIFT = 0x40
CONTROL = "bhmrwz"


def byte_of(ch):
    """Encoded byte for one English character (None if it has no glyph)."""
    if "a" <= ch <= "z":
        return ord(ch) + LOWER_SHIFT
    if ch == " " or ch in _FW and ord(ch) < 0x7F:
        return ord(ch)
    if ch == "…":
        return 0xBF
    return None


def encode(s):
    """English script text -> bytes. Escapes as in sjis.encode: \\n, {b}{h}{m}{r}{w}{z}, [XX]; full-width
    characters (Japanese) still go out as Shift-JIS."""
    out, i = bytearray(), 0
    while i < len(s):
        ch = s[i]
        if ch == "{" and s[i + 2:i + 3] == "}" and s[i + 1] in CONTROL:
            out.append(ord(s[i + 1]))
            i += 3
            continue
        if ch == "[" and i + 3 < len(s) and s[i + 3] == "]" and all(c in "0123456789ABCDEF" for c in s[i + 1:i + 3]):
            out.append(int(s[i + 1:i + 3], 16))
            i += 4
            continue
        if ch == "\n":
            out.append(0x0A)
        elif (b := byte_of(ch)) is not None:
            out.append(b)
        else:
            out += sjis.encode(ch)
        i += 1
    return bytes(out)


def _cells(exe):
    """{sjis code: (column, row)} for every page-0 cell of the glyph table."""
    out = {}
    for k in range(164):
        first, tp, row, page = struct.unpack_from("<HBBH", exe, GLYPH_TABLE + 6 * k)
        if page == 0 and tp == 0:
            for c in range(21):
                out[first + c] = (c, row)
    return out


def _po(d, off):
    fl, _, _, po, w, _, _ = tim.parse(d, off)
    assert fl == 8 and w == 256, "font TIM moved?"
    return po


def _pix(d, po, x, y):
    b = d[po + y * 128 + x // 2]
    return (b >> 4 if x & 1 else b) & 1


def tables(tim_data, off, exe):
    """(code, width): 256-entry lists indexed by encoded byte; code 0 = no glyph. Widths are measured on the
    shifted cells, so call with either the original or the patched TIM."""
    po = _po(tim_data, off)
    cells = _cells(exe)
    code, width = [0] * 256, [0] * 256
    width[0x20] = SPACE
    for ch in _FW:
        b = byte_of(ch)
        sj = struct.unpack(">H", _FW[ch].encode("cp932"))[0]
        col, row = cells[sj]
        xs = [x for x in range(CELL) for y in range(CELL) if _pix(tim_data, po, col * CELL + x, row * CELL + y)]
        lo, hi = (min(xs), max(xs)) if xs else (0, -1)
        code[b], width[b] = sj, min(hi - lo + 1 + GAP, CELL)
    return code, width


def patch_tim(d, off, exe):
    """Return d with every mapped page-0 cell's ink moved to the cell's left edge (bit 0 of each pixel only)."""
    d = bytearray(d)
    po = _po(d, off)
    cells = _cells(exe)
    for ch, fw in _FW.items():
        col, row = cells[struct.unpack(">H", fw.encode("cp932"))[0]]
        x0, y0 = col * CELL, row * CELL
        px = [[_pix(d, po, x0 + x, y0 + y) for x in range(CELL)] for y in range(CELL)]
        xs = [x for x in range(CELL) if any(r[x] for r in px)]
        lo = xs[0] if xs else 0
        for y in range(CELL):
            for x in range(CELL):
                v = px[y][x + lo] if x + lo < CELL else 0
                a = po + (y0 + y) * 128 + (x0 + x) // 2
                sh = 4 if (x0 + x) & 1 else 0
                d[a] = d[a] & ~(1 << sh) & 0xFF | v << sh
    return bytes(d)


_WIDTHS = None


def width_px(text, tree="work/disc/tree"):
    """Pen advance of one line of English script text in px (sum of VWF widths; SJIS characters 12)."""
    global _WIDTHS
    if _WIDTHS is None:
        t = Path(tree)
        _WIDTHS = tables((t / "BAT_TIM.BIN").read_bytes(), TIM_OFFS["BAT_TIM.BIN"], (t / "SLPS_023.19").read_bytes())[1]
    b, n, i = encode(text), 0, 0
    while i < len(b):
        if sjis.is_lead(b[i]) and b[i] <= 0xEF:
            n, i = n + 12, i + 2
        else:
            n, i = n + _WIDTHS[b[i]], i + 1
    return n


def glyphs(text):
    """Sprite slots a string takes: every drawn character (spaces, newlines and control letters take none)."""
    b, n, i = encode(text), 0, 0
    while i < len(b):
        if sjis.is_lead(b[i]) and b[i] <= 0xEF:
            n += b[i:i + 2] not in (b"\x81\x40", b"\x82\x40")
            i += 2
        else:
            n += b[i] not in (0x00, 0x0A, 0x20) and chr(b[i]) not in CONTROL
            i += 1
    return n


def tables_asm(code, width):
    """armips source for asm/vwf.asm's TABLES include (bytes 0x00-0xBF)."""
    n = 0xC0
    assert all(width[b] == 0 for b in (0x00, 0x0A) + tuple(range(0x61, 0x7B))), "control bytes must keep width 0"
    rows = ["VWF_WIDTH:"] + ["  .byte " + ",".join("0x%02X" % w for w in width[i:i + 16]) for i in range(0, n, 16)]
    rows += [".align 2", "VWF_CODE:"]
    rows += ["  .halfword " + ",".join("0x%04X" % c for c in code[i:i + 16]) for i in range(0, n, 16)]
    return "\n".join(rows) + "\n"


def preview(tim_data, off, exe, text, out):
    from PIL import Image
    po = _po(tim_data, off)
    code, width = tables(tim_data, off, exe)
    cells = _cells(exe)
    img = Image.new("RGB", (8 + sum(width[b] for b in encode(text)), 20), (24, 24, 72))
    x = 4
    for b in encode(text):
        if code[b]:
            col, row = cells[code[b]]
            for y in range(CELL):
                for xx in range(CELL):
                    if _pix(tim_data, po, col * CELL + xx, row * CELL + y) and x + xx < img.width:
                        img.putpixel((x + xx, 4 + y), (255, 255, 255))
        x += width[b]
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(out)
    return x - 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", required=True)
    ap.add_argument("text", nargs="?", default="The quick brown fox jumps over the lazy dog! 0123456789 (\"Hm?\"), "
                                               "Masaki & Cybuster's 100% #1: <ok> [x] a+b=c; 5-3 @/ *~")
    ap.add_argument("--tree", default="work/disc/tree")
    a = ap.parse_args()
    t = Path(a.tree)
    exe = (t / "SLPS_023.19").read_bytes()
    d = patch_tim((t / "BAT_TIM.BIN").read_bytes(), TIM_OFFS["BAT_TIM.BIN"], exe)
    print("width px:", preview(d, TIM_OFFS["BAT_TIM.BIN"], exe, a.text, a.preview))


if __name__ == "__main__":
    main()
