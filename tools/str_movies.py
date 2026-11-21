"""List the movies in MOV.STR and cut each one out of the raw disc image for ffmpeg (psxstr wants 2352-byte sectors).
Usage: str_movies.py [--bin DISC.bin] [--out work/fmv] [--every 2]
  -> prints sector/frame ranges; writes OUT/movNN.str and, with --every N, OUT/movNN/f%03d.png one frame per N seconds."""
import argparse
import struct
import subprocess
from pathlib import Path

LBA = 60219  # MOV.STR (docs/re/disc.md)
SECTORS = 85801
ap = argparse.ArgumentParser()
ap.add_argument("--bin", default="rom/Shin Masou Kishin - Panzer Warfare (Japan).bin")
ap.add_argument("--out", default="work/fmv")
ap.add_argument("--every", type=float, default=0)
a = ap.parse_args()
out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
movies, prev = [], None
with open(a.bin, "rb") as f:
    f.seek(LBA * 2352)
    raw = f.read(SECTORS * 2352)
for n in range(SECTORS):
    h = raw[n * 2352 + 24:n * 2352 + 56]  # 12 sync + 4 header + 8 subheader
    if h[:4] != b"\x60\x01\x01\x80":
        continue
    fr = struct.unpack_from("<I", h, 8)[0]
    if prev is None or fr < prev:
        movies.append([n, n, fr])
    movies[-1][1], prev = n, fr
for k, (s, e, _) in enumerate(movies, 1):
    print(f"mov{k:02d} sectors {s}-{e} ({e - s + 1})")
    p = out / f"mov{k:02d}.str"
    p.write_bytes(raw[s * 2352:(e + 4) * 2352])  # keep the trailing audio sectors
    if a.every:
        d = out / f"mov{k:02d}"
        d.mkdir(exist_ok=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "psxstr", "-i", str(p),
                        "-vf", f"fps=1/{a.every}", str(d / "f%03d.png")], check=False)
