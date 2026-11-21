"""PS1 TIM images inside a container file: find, decode, dump PNGs (graphics-text survey).
Usage: tim.py FILE --out DIR [--min-area 1024]   -> DIR/<offset>.png (first CLUT) + DIR/index.tsv
Library: find(data) -> [(offset, bpp_flag, length)], decode(data, off) -> PIL.Image."""
import argparse
import struct
from pathlib import Path

from PIL import Image


def _rgb(c):
    if c == 0:
        return (0, 0, 0, 0)
    return ((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3, 255)


def parse(d, i):
    """(flag, clut_colors, clut_count, pixel_bytes_off, w_px, h, total_len) or None."""
    if d[i:i + 4] != b"\x10\0\0\0":
        return None
    fl = struct.unpack_from("<I", d, i + 4)[0]
    if fl not in (0, 1, 2, 3, 8, 9):
        return None
    o, clut, nclut = i + 8, None, 0
    if fl & 8:
        ln, x, y, w, h = struct.unpack_from("<I4H", d, o)
        if ln != 12 + w * h * 2 or not (0 < w <= 256 and 0 < h <= 256):
            return None
        clut, nclut = o + 12, w * h // (16 if fl & 3 == 0 else 256) or 1
        o += ln
    if o + 12 > len(d):
        return None
    ln, x, y, w, h = struct.unpack_from("<I4H", d, o)
    if ln != 12 + w * h * 2 or not (0 < w <= 1024 and 0 < h <= 512) or o + ln > len(d):
        return None
    wpx = {0: w * 4, 1: w * 2, 2: w, 3: w * 2 // 3}[fl & 3]
    return fl, clut, nclut, o + 12, wpx, h, o + ln - i


def decode(d, i, clut_index=0):
    fl, clut, nclut, po, w, h, _ = parse(d, i)
    bpp = fl & 3
    img = Image.new("RGBA", (w, h))
    px = img.load()
    if bpp in (0, 1):
        n = 16 if bpp == 0 else 256
        pal = [_rgb(struct.unpack_from("<H", d, clut + 2 * (clut_index * n + k))[0]) for k in range(n)] if clut else \
            [(k * 255 // (n - 1),) * 3 + (255,) for k in range(n)]
    for yy in range(h):
        for xx in range(w):
            if bpp == 0:
                b = d[po + yy * (w // 2) + xx // 2]
                px[xx, yy] = pal[(b >> 4) if xx & 1 else (b & 15)]
            elif bpp == 1:
                px[xx, yy] = pal[d[po + yy * w + xx]]
            elif bpp == 2:
                px[xx, yy] = _rgb(struct.unpack_from("<H", d, po + 2 * (yy * w + xx))[0])
            else:
                p = po + 3 * (yy * w + xx)
                px[xx, yy] = (d[p], d[p + 1], d[p + 2], 255)
    return img


def find(d):
    out, i = [], 0
    while i < len(d) - 20:
        r = parse(d, i) if d[i] == 0x10 else None
        if r:
            out.append((i, r[0], r[6]))
            i += r[6] + (-r[6] & 3)
        else:
            i += 4
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-area", type=int, default=1024)
    a = ap.parse_args()
    d = open(a.file, "rb").read()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for off, fl, ln in find(d):
        img = decode(d, off)
        if img.width * img.height < a.min_area:
            continue
        img.save(out / f"{off:08X}.png")
        rows.append(f"{off:08X}\t{fl}\t{img.width}x{img.height}\t{ln}")
    (out / "index.tsv").write_text("offset\tflag\tsize\tbytes\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"{a.file}: {len(rows)} TIMs -> {out}")
