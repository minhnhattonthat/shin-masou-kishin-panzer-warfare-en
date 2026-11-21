"""Was a TIM ever uploaded to VRAM? Searches VRAM dumps (ppudump.lua: <dir>/ppu_<frame>.vram.bin, 1024x512 u16)
for the TIM's pixel rows: prints each dump where row R of the image sits at some VRAM x, y.

    python -X utf8 tools/debug/vram_find.py build/disc/tree/GRA5.BIN 0x76800 work/qa/vram_ev01 [--rows 3]
"""
import argparse
import glob
import os
import struct


def tim_pixels(d, off):
    flags = struct.unpack_from("<I", d, off + 4)[0]
    p = off + 8
    if flags & 8:  # CLUT block
        p += struct.unpack_from("<I", d, p)[0]
    n, x, y, w, h = struct.unpack_from("<IHHHH", d, p)
    return d[p + 12:p + 12 + w * h * 2], w * 2, h


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("off", type=lambda s: int(s, 0))
    ap.add_argument("dumps")
    ap.add_argument("--rows", type=int, default=3, help="distinct rows that must all match")
    a = ap.parse_args()
    pix, stride, h = tim_pixels(open(a.file, "rb").read(), a.off)
    rows = sorted(range(h), key=lambda r: -len(set(pix[r * stride:(r + 1) * stride])))[:a.rows]
    hits = 0
    for f in sorted(glob.glob(os.path.join(a.dumps, "*.vram.bin"))):
        v = open(f, "rb").read()
        r0 = rows[0]
        i = v.find(pix[r0 * stride:(r0 + 1) * stride])
        while i >= 0:
            base = i - r0 * 2048
            if base >= 0 and all(v[base + r * 2048:base + r * 2048 + stride] == pix[r * stride:(r + 1) * stride]
                                 for r in rows):
                print("%s: at VRAM x=%d y=%d" % (os.path.basename(f), base % 2048 // 2, base // 2048))
                hits += 1
                break
            i = v.find(pix[r0 * stride:(r0 + 1) * stride], i + 1)
    print("%d dumps hold the image" % hits)


if __name__ == "__main__":
    main()
