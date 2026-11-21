"""Thumbnail montage of a folder of PNGs, labelled by file stem. Usage: montage.py DIR --out PREFIX [--per 48]
[--cols 8] [--thumb 160x120] -> PREFIX_01.png ... (graphics-text survey of extracted TIMs)."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--out", required=True)
ap.add_argument("--per", type=int, default=48)
ap.add_argument("--cols", type=int, default=8)
ap.add_argument("--thumb", default="160x120")
ap.add_argument("--unique", action="store_true", help="skip byte-identical copies (first offset kept)")
a = ap.parse_args()
tw, th = map(int, a.thumb.split("x"))
files = sorted(Path(a.dir).glob("*.png"))
if a.unique:
    seen = set()
    files = [f for f in files if not (f.read_bytes() in seen or seen.add(f.read_bytes()))]
for page in range(0, len(files), a.per):
    chunk = files[page:page + a.per]
    rows = (len(chunk) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (a.cols * tw, rows * (th + 10)), (60, 0, 60))
    dr = ImageDraw.Draw(sheet)
    for k, f in enumerate(chunk):
        im = Image.open(f).convert("RGBA")
        im.thumbnail((tw, th))
        x, y = (k % a.cols) * tw, (k // a.cols) * (th + 10)
        sheet.paste(im, (x, y + 10), im)
        dr.text((x + 2, y), f.stem, fill=(255, 255, 0))
    out = f"{a.out}_{page // a.per + 1:02d}.png"
    sheet.save(out)
    print(out, len(chunk))
