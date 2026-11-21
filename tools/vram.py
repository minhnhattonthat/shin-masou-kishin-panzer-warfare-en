"""Render a PCSX-Redux VRAM dump (L.dump_ppu: 1024x512 16-bit words; extra bytes ignored).
Usage: vram.py DUMP.vram.bin --out PNG [--mode 15|4|8] [--crop x,y,w,h]   (x,w in 16-bit VRAM words)
--mode 15: direct colour; 4/8: each word split into 4-bit/8-bit indices shown as grey (to spot fonts/CLUT images)."""
import argparse
import struct

from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("dump")
ap.add_argument("--out", required=True)
ap.add_argument("--mode", default="15", choices=["15", "4", "8"])
ap.add_argument("--crop", default="0,0,1024,512")
a = ap.parse_args()
x0, y0, w, h = map(int, a.crop.split(","))
d = open(a.dump, "rb").read()
assert len(d) >= 1024 * 512 * 2, "short dump"
words = lambda y: struct.unpack_from("<%dH" % w, d, (y * 1024 + x0) * 2)
if a.mode == "15":
    im = Image.new("RGB", (w, h))
    im.putdata([((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3) for y in range(y0, y0 + h) for c in words(y)])
else:
    n = 4 if a.mode == "4" else 2
    bits, mask, scale = 16 // n, (1 << (16 // n)) - 1, 255 // ((1 << (16 // n)) - 1)
    im = Image.new("L", (w * n, h))
    im.putdata([(c >> (bits * k) & mask) * scale for y in range(y0, y0 + h) for c in words(y) for k in range(n)])
im.save(a.out)
print(a.out, im.size)
