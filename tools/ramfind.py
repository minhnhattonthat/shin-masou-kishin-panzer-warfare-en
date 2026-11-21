"""Recon: which sectors of a disc file sit in a RAM dump, and where. Usage: ramfind.py RAM.bin FILE [--chunk 2048]
Prints runs of consecutive file chunks found at consecutive RAM addresses (0x80000000-based)."""
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("ram")
ap.add_argument("file")
ap.add_argument("--chunk", type=int, default=2048)
a = ap.parse_args()
ram = open(a.ram, "rb").read()
f = open(a.file, "rb").read()
hits = []
for off in range(0, len(f), a.chunk):
    c = f[off:off + a.chunk]
    if c.count(0) > len(c) * 0.9:
        continue
    r = ram.find(c)
    if r >= 0:
        hits.append((off, r))
run = None
for off, r in hits:
    if run and off - run[1] == a.chunk and r - run[3] == a.chunk:
        run[1], run[3] = off, r
    else:
        if run:
            print(f"file {run[0]:07X}-{run[1] + a.chunk:07X} -> RAM {0x80000000 + run[2]:08X}")
        run = [off, off, r, r]
if run:
    print(f"file {run[0]:07X}-{run[1] + a.chunk:07X} -> RAM {0x80000000 + run[2]:08X}")
