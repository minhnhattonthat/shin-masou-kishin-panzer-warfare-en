"""FMV subtitles (G10, docs/re/graphics.md): English burned into the MOV.STR frames that carry Japanese text.

MOV.STR is a mixed-mode file in the unpacked tree (2336-byte sectors: 8-byte subheader, 2048 data, EDC/ECC that
mkpsxiso regenerates). Video sectors start with the STR header 60 01 01 80; frame data is 2016 bytes per sector after
the 32-byte header, MDEC bitstream version 2 (10-bit DC, MPEG-1 table B.14 AC codes, 22-bit escape), macroblocks in
column order, blocks Cr Cb Y1 Y2 Y3 Y4.

gfx/fmv/subtitles.tsv, one row per caption (tab-separated, header line):
  movie first last fade x y w h jp dark text font size ink edge align note
  movie        1-based movie index in MOV.STR (str_movies.py order)
  first last   frame numbers (1-based, as the STR header counts them), inclusive
  fade         frames of fade-in from `first` (the JP text's own fade)
  x y w h      band over the JP text: blurred, darkened (x `dark`), edges feathered
  jp           #rrggbb:tol, colour of the JP glyphs; those pixels (+2 px of outline, any frame of the row) are
               filled from their surroundings first, so no ghost shows through the band
  text         English; `|` breaks lines
  font size    fonts/<file>[:wght] and the largest size; shrunk until every line fits w - 8
  ink edge     text colour and outline colour, #rrggbb
Each listed frame is decoded with ffmpeg (yuvj420p), drawn, re-encoded at the lowest qscale (from the frame's own)
that fits its own sectors, and written back in place; apply() then decodes the patched movie again and fails if a
replaced frame is off from its target (PSNR) or any other frame changed.

    python -X utf8 tools/fmv.py preview [MOVIE]   -> work/fmv/preview/movNN_fXXXX.png (JP | EN after re-encode)
    python -X utf8 tools/fmv.py parse [MOVIE..]   parse every frame with the VLC table (self-check of the table)
Library: apply(tree, log) is the build stage (en mode); ranges(orig_tree) for tools/writes_check.py."""
import argparse
import csv
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TSV = ROOT / "gfx/fmv/subtitles.tsv"  # a subfolder: gfx.py reads every gfx/*.tsv
SEC = 2336
CHUNK = 2016
MAGIC = b"\x60\x01\x01\x80"

# MPEG-1 table B.14 (non-first coefficient form): (run, level) -> (code, bits), sign bit follows. Codes up to 13 bits;
# longer pairs go out as escapes. `parse` checks the table against every frame on the disc.
VLC = {
    (0, 1): (0b11, 2), (0, 2): (0b0100, 4), (0, 3): (0b00101, 5), (0, 4): (0b0000110, 7),
    (0, 5): (0x26, 8), (0, 6): (0x21, 8), (0, 7): (0x0A, 10), (0, 8): (0x1D, 12), (0, 9): (0x18, 12),
    (0, 10): (0x13, 12), (0, 11): (0x10, 12), (0, 12): (0x1A, 13), (0, 13): (0x19, 13), (0, 14): (0x18, 13),
    (0, 15): (0x17, 13),
    (1, 1): (0b011, 3), (1, 2): (0b000110, 6), (1, 3): (0x25, 8), (1, 4): (0x0C, 10), (1, 5): (0x1B, 12),
    (1, 6): (0x16, 13), (1, 7): (0x15, 13),
    (2, 1): (0b0101, 4), (2, 2): (0b0000100, 7), (2, 3): (0x0B, 10), (2, 4): (0x14, 12), (2, 5): (0x14, 13),
    (3, 1): (0b00111, 5), (3, 2): (0x24, 8), (3, 3): (0x1C, 12), (3, 4): (0x13, 13),
    (4, 1): (0b00110, 5), (4, 2): (0x0F, 10), (4, 3): (0x12, 12),
    (5, 1): (0b000111, 6), (5, 2): (0x09, 10), (5, 3): (0x12, 13),
    (6, 1): (0b000101, 6), (6, 2): (0x1E, 12),
    (7, 1): (0b000100, 6), (7, 2): (0x15, 12),
    (8, 1): (0b0000111, 7), (8, 2): (0x11, 12),
    (9, 1): (0b0000101, 7), (9, 2): (0x11, 13),
    (10, 1): (0x27, 8), (10, 2): (0x10, 13),
    (11, 1): (0x23, 8), (12, 1): (0x22, 8), (13, 1): (0x20, 8),
    (14, 1): (0x0E, 10), (15, 1): (0x0D, 10), (16, 1): (0x08, 10),
    (17, 1): (0x1F, 12), (18, 1): (0x1A, 12), (19, 1): (0x19, 12), (20, 1): (0x17, 12), (21, 1): (0x16, 12),
    (22, 1): (0x1F, 13), (23, 1): (0x1E, 13), (24, 1): (0x1D, 13), (25, 1): (0x1C, 13), (26, 1): (0x1B, 13),
}
# the 14-16 bit codes, used only by parse (the encoder escapes these pairs)
VLC_LONG = {
    **{(0, 16 + k): (0x1F - k, 14) for k in range(16)},
    **{(0, 32 + k): (0x18 - k, 15) for k in range(9)},
    **{(1, 8 + k): (0x1F - k, 15) for k in range(7)},
    **{(1, 15 + k): (0x13 - k, 16) for k in range(4)},
    (6, 3): (0x14, 16), (11, 2): (0x1A, 16), (12, 2): (0x19, 16), (13, 2): (0x18, 16), (14, 2): (0x17, 16),
    (15, 2): (0x16, 16), (16, 2): (0x15, 16),
    **{(27 + k, 1): (0x1F - k, 16) for k in range(5)},
}
ESC = (0b000001, 6)
EOB = (0b10, 2)
DECODE = {(c, n): rl for rl, (c, n) in {**VLC, **VLC_LONG}.items()}
ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7,
          14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39,
          46, 53, 60, 61, 54, 47, 55, 62, 63]
QTAB = np.array([2, 16, 19, 22, 26, 27, 29, 34, 16, 16, 22, 24, 27, 29, 34, 37, 19, 22, 26, 27, 29, 34, 34, 38,
                 22, 22, 26, 27, 29, 34, 37, 40, 22, 26, 27, 29, 32, 35, 40, 48, 26, 27, 29, 32, 35, 40, 48, 58,
                 26, 27, 29, 34, 38, 46, 56, 69, 27, 29, 35, 38, 46, 56, 69, 83], float)
_k = np.arange(8)
DCT = np.sqrt(2 / 8) * np.cos((2 * _k[None, :] + 1) * _k[:, None] * np.pi / 16)
DCT[0] /= np.sqrt(2)  # orthonormal


# ---- STR container ----------------------------------------------------------------------------------------------
def movies(data):
    """[(first_sector, last_sector)] per movie, split where the frame number restarts (as str_movies.py)."""
    out, prev = [], None
    for n in range(len(data) // SEC):
        h = data[n * SEC + 8:n * SEC + 40]
        if h[:4] != MAGIC:
            continue
        fr = struct.unpack_from("<I", h, 8)[0]
        if prev is None or fr < prev:
            out.append([n, n])
        out[-1][1], prev = n, fr
    return [tuple(m) for m in out]


def frames(data, mv):
    """{frame_no: [sector, ...] in chunk order} for one movie (sector numbers in the whole file)."""
    s0, s1 = mv
    fr = {}
    for n in range(s0, s1 + 1):
        d = data[n * SEC + 8:n * SEC + 40]
        if d[:4] == MAGIC:
            ch, _, no = struct.unpack_from("<HHI", d, 4)
            fr.setdefault(no, []).append((ch, n))
    return {k: [n for _, n in sorted(v)] for k, v in fr.items()}


def frame_bytes(data, secs):
    return b"".join(data[n * SEC + 40:n * SEC + 40 + CHUNK] for n in secs)


def to_2352(data, s0, s1):
    """Movie sectors as raw 2352-byte sectors (ffmpeg's psxstr demuxer wants sync + header)."""
    sync = b"\x00" + b"\xff" * 10 + b"\x00" + b"\x00\x00\x00\x02"
    return b"".join(sync + data[n * SEC:(n + 1) * SEC] for n in range(s0, s1 + 4))


def decode_yuv(raw2352, w=320, h=224):
    """ffmpeg-decoded frames as [(Y, Cb, Cr)] float arrays (yuvj420p, no colour conversion)."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "m.str"
        p.write_bytes(raw2352)
        out = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "psxstr", "-i", str(p),
                              "-map", "0:v", "-f", "rawvideo", "-pix_fmt", "yuvj420p", "-"],
                             capture_output=True, check=True).stdout
    fs = w * h * 3 // 2
    res = []
    for i in range(len(out) // fs):
        b = np.frombuffer(out, np.uint8, fs, i * fs).astype(float)
        y = b[:w * h].reshape(h, w)
        cb = b[w * h:w * h * 5 // 4].reshape(h // 2, w // 2)
        cr = b[w * h * 5 // 4:].reshape(h // 2, w // 2)
        res.append((y, cb, cr))
    return res


# ---- colour -----------------------------------------------------------------------------------------------------
def yuv_to_rgb(y, cb, cr):
    cb = cb.repeat(2, 0).repeat(2, 1) - 128
    cr = cr.repeat(2, 0).repeat(2, 1) - 128
    return np.stack([y + 1.402 * cr, y - 0.344136 * cb - 0.714136 * cr, y + 1.772 * cb], axis=2)


def rgb_to_yuv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb = -0.168736 * r - 0.331264 * g + 0.5 * b + 128
    cr = 0.5 * r - 0.418688 * g - 0.081312 * b + 128
    sub = lambda c: c.reshape(c.shape[0] // 2, 2, c.shape[1] // 2, 2).mean(axis=(1, 3))
    return y, sub(cb), sub(cr)  # 2x2 mean undoes yuv_to_rgb's nearest upsampling exactly


# ---- MDEC v2 bitstream -----------------------------------------------------------------------------------------
class Bits:
    def __init__(self):
        self.acc, self.n, self.out = 0, 0, bytearray()

    def put(self, code, bits):
        self.acc = (self.acc << bits) | (code & ((1 << bits) - 1))
        self.n += bits
        while self.n >= 16:
            self.n -= 16
            self.out += struct.pack("<H", (self.acc >> self.n) & 0xFFFF)
        self.acc &= (1 << self.n) - 1

    def flush(self):
        if self.n:
            self.put(0, 16 - self.n)
        return bytes(self.out)


def levels(block, qscale):
    """8x8 pixel block (0..255) -> 64 quantised levels in zigzag order (index 0 = DC)."""
    f = (DCT @ (block - 128) @ DCT.T).ravel()  # orthonormal 2-D DCT = MPEG's F(u,v); F00 = 8 * (mean - 128)
    lv = np.empty(64, int)
    lv[0] = int(np.clip(np.round(f[0] / 2), -512, 511))
    q = f[1:] * 8 / (qscale * QTAB[1:])
    lv[1:] = np.clip(np.round(q), -511, 511).astype(int)
    return lv[ZIGZAG]


def put_block(bs, lv, qscale):
    bs.put(lv[0] & 0x3FF, 10)
    codes, run = 2, 0  # DC + EOB halfwords
    for v in lv[1:]:
        if v == 0:
            run += 1
            continue
        a = abs(int(v))
        if (run, a) in VLC:
            c, n = VLC[(run, a)]
            bs.put(c, n)
            bs.put(1 if v < 0 else 0, 1)
        else:
            bs.put(*ESC)
            bs.put(run, 6)
            bs.put(int(v) & 0x3FF, 10)
        codes += 1
        run = 0
    bs.put(*EOB)
    return codes


def encode(y, cb, cr, qscale):
    """One frame -> MDEC v2 bitstream (8-byte header + data) and the header's MDEC size word."""
    h, w = y.shape
    bs = Bits()
    halfwords = 0
    for mx in range(w // 16):
        for my in range(h // 16):
            blocks = [cr[my * 8:my * 8 + 8, mx * 8:mx * 8 + 8], cb[my * 8:my * 8 + 8, mx * 8:mx * 8 + 8]]
            for by, bx in ((0, 0), (0, 8), (8, 0), (8, 8)):
                blocks.append(y[my * 16 + by:my * 16 + by + 8, mx * 16 + bx:mx * 16 + bx + 8])
            for b in blocks:
                halfwords += put_block(bs, levels(b, qscale), qscale)
    bs.put(0x1FF, 10)  # end of frame: every original frame has it; without it the game's decoder hangs
    body = bs.flush()
    size = -(-halfwords // 64) * 32  # MDEC size / 4, rounded to 0x80 bytes (as the originals)
    return struct.pack("<HHHH", size, 0x3800, qscale, 2) + body, size


def parse(fb):
    """Parse one frame's bitstream with the table; -> (blocks, halfwords, bytes used, qscale) or raise."""
    size, magic, qscale, ver = struct.unpack_from("<HHHH", fb)
    assert magic == 0x3800 and ver == 2, (magic, ver)
    words = struct.unpack_from("<%dH" % ((len(fb) - 8) // 2), fb, 8)
    bits = "".join(format(x, "016b") for x in words)
    pos, blocks, hw = 0, 0, 0
    nblocks = 320 // 16 * 224 // 16 * 6
    while blocks < nblocks:
        pos += 10
        hw += 2
        i = 0
        while True:
            if bits.startswith("10", pos):
                pos += 2
                break
            if bits.startswith("000001", pos):
                i += int(bits[pos + 6:pos + 12], 2) + 1
                pos += 22
            else:
                for n in range(2, 17):
                    rl = DECODE.get((int(bits[pos:pos + n], 2), n))
                    if rl:
                        break
                else:
                    raise ValueError(f"no code at bit {pos} (block {blocks}): {bits[pos:pos + 17]}")
                i += rl[0] + 1
                pos += n + 1
            hw += 1
            if i > 63:
                raise ValueError(f"run past 63 in block {blocks}")
        blocks += 1
    if bits[pos:pos + 10] != "0111111111":
        raise ValueError(f"no end-of-frame code 0x1FF after the last block: {bits[pos:pos + 10]}")
    pos += 10
    return blocks, hw, 8 + (pos + 15) // 16 * 2, qscale


# ---- captions ---------------------------------------------------------------------------------------------------
def rows():
    with open(TSV, encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter="\t")]


def _font(spec, size):
    from PIL import ImageFont
    path, *wght = spec.split(":")
    f = ImageFont.truetype(str(ROOT / "fonts" / path), size)
    if wght:
        f.set_variation_by_axes([int(wght[0])])
    return f


def _hex(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def _blur(a, radius):
    """Separable Gaussian blur (sigma = radius) of a float H x W (x C) array, edges clamped."""
    k = np.exp(-0.5 * (np.arange(-3 * radius, 3 * radius + 1) / radius) ** 2)
    k /= k.sum()
    p = 3 * radius
    for axis in (0, 1):
        pad = [(0, 0)] * a.ndim
        pad[axis] = (p, p)
        b = np.pad(a, pad, mode="edge")
        a = sum(k[i] * np.take(b, range(i, i + a.shape[axis]), axis=axis) for i in range(len(k)))
    return a


def jp_mask(frames_rgb, r):
    """Pixels of the JP text inside the band, over all of the row's frames: within tol of the `jp` colour, grown
    2 px to take the outline."""
    from PIL import Image, ImageFilter
    col, tol = r["jp"].split(":")
    x, y, w, h = (int(r[k]) for k in "xywh")
    m = np.zeros(frames_rgb[0].shape[:2], bool)
    for f in frames_rgb:
        m |= (np.abs(f - np.array(_hex(col), float)).max(axis=2) <= int(tol))
    box = np.zeros_like(m)
    box[y:y + h, x:x + w] = True
    m &= box
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), float) / 255


def caption(rgb, r, alpha, mask):
    """Draw one caption row onto an RGB float frame (alpha 0..1 = fade). The JP text pixels (mask) are filled from
    their surroundings (normalized convolution), then a feathered band blurs and darkens the area."""
    from PIL import Image, ImageDraw, ImageFilter
    x, y, w, h = (int(r[k]) for k in "xywh")
    H, W = rgb.shape[:2]
    keep = 1 - mask
    fill = None
    for s in (24, 6):  # wide pass first: inside a thick masked area the 6 px pass has no unmasked pixel to use
        den = _blur(keep, s)[..., None]
        f = _blur(rgb * keep[..., None], s) / np.maximum(den, 1e-6)
        fill = f if fill is None else np.where(den > 0.05, f, fill)
    clean = rgb * keep[..., None] + fill * mask[..., None]
    dark = _blur(clean, 3) * float(r.get("dark") or 0.45)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rectangle([x + 4, y + 4, x + w - 5, y + h - 5], fill=255)
    band = np.asarray(m.filter(ImageFilter.GaussianBlur(3)), float)[..., None] / 255 * alpha
    out = clean * (1 - band) + dark * band  # the fill is never faded: the JP fades in under it
    lines = r["text"].split("|")
    size = int(r["size"])
    while True:
        f = _font(r["font"], size)
        if all(f.getlength(t) <= w - 8 for t in lines) or size <= 8:
            break
        size -= 1
    asc, desc = f.getmetrics()
    lh = asc + desc
    gap = max(1, size // 8)
    top = y + (h - (lh * len(lines) + gap * (len(lines) - 1))) // 2
    txt = Image.new("L", (W, H), 0)
    edge = Image.new("L", (W, H), 0)
    dt, de = ImageDraw.Draw(txt), ImageDraw.Draw(edge)
    for i, t in enumerate(lines):
        tw = f.getlength(t)
        al = r.get("align", "center") or "center"
        tx = x + (w - tw) / 2 if al == "center" else x + 4 if al == "left" else x + w - 4 - tw
        ty = top + i * (lh + gap)
        dt.text((tx, ty), t, font=f, fill=255)
        de.text((tx, ty), t, font=f, fill=255, stroke_width=2, stroke_fill=255)
    te = np.asarray(edge, float)[..., None] / 255 * alpha
    tt = np.asarray(txt, float)[..., None] / 255 * alpha
    out = out * (1 - te) + np.array(_hex(r["edge"]), float) * te
    out = out * (1 - tt) + np.array(_hex(r["ink"]), float) * tt
    return out


def targets(data, movie):
    """{frame_no: (y, cb, cr)} drawn frames for one movie, and the movie's decoded JP frames."""
    mvs = movies(data)
    s0, s1 = mvs[movie - 1]
    jp = decode_yuv(to_2352(data, s0, s1))
    want = {}
    for r in rows():
        if int(r["movie"]) != movie:
            continue
        a, b, fade = int(r["first"]), int(r["last"]), int(r["fade"])
        mask = jp_mask([yuv_to_rgb(*jp[no - 1]) for no in range(a, b + 1)], r)
        for no in range(a, b + 1):
            base = want.get(no, jp[no - 1])
            rgb = yuv_to_rgb(*base)
            al = min(1.0, (no - a + 1) / (fade + 1)) if fade else 1.0
            want[no] = rgb_to_yuv(caption(rgb, r, al, mask))
    return want, jp


def patch_movie(data, movie):
    """Write the captioned frames of one movie into data (bytearray). -> {frame: (qscale, bytes, capacity)}."""
    want, _ = targets(data, movie)
    fr = frames(data, movies(data)[movie - 1])
    info = {}
    for no, (y, cb, cr) in sorted(want.items()):
        secs = fr[no]
        cap = len(secs) * CHUNK
        q0 = struct.unpack_from("<H", data, secs[0] * SEC + 8 + 0x18)[0]
        yq, cbq, crq = (np.clip(np.round(c), 0, 255) for c in (y, cb, cr))
        for q in range(q0, 64):
            bs, size = encode(yq, cbq, crq, q)
            if len(bs) <= cap:
                break
        else:
            raise SystemExit(f"fmv: movie {movie} frame {no} does not fit {cap} bytes")
        dsz = (len(bs) + 3) & ~3
        bs = bs.ljust(cap, b"\0")
        for k, n in enumerate(secs):
            o = n * SEC + 8
            hdr = bytearray(data[o:o + 32])
            struct.pack_into("<I", hdr, 0x0C, dsz)
            struct.pack_into("<HHHH", hdr, 0x14, size, 0x3800, q, 2)
            data[o:o + 32] = hdr
            data[o + 32:o + 32 + CHUNK] = bs[k * CHUNK:(k + 1) * CHUNK]
        info[no] = (q, len(bs.rstrip(b"\0")), cap)
    return info


def psnr(a, b):
    e = np.mean((a - b) ** 2)
    return 99.0 if e == 0 else 10 * np.log10(255 ** 2 / e)


def verify(orig, data, movie, want):
    """Decode the patched movie: drawn frames close to their target, every other frame bit-identical."""
    s0, s1 = movies(data)[movie - 1]
    new = decode_yuv(to_2352(data, s0, s1))
    old = decode_yuv(to_2352(orig, s0, s1))
    bad = []
    fr = frames(data, (s0, s1))
    for i in want:  # what ffmpeg forgives but the game's decoder may not: the end code, the size words
        fb = frame_bytes(data, fr[i])
        try:
            _, hw, used, _ = parse(fb)
        except (ValueError, AssertionError) as e:
            bad.append(f"frame {i}: {e}")
            continue
        dsz = struct.unpack_from("<I", data, fr[i][0] * SEC + 8 + 0x0C)[0]
        if struct.unpack_from("<H", fb)[0] != -(-hw // 64) * 32 or used > dsz:
            bad.append(f"frame {i}: size word / demux size")
    for i, (n, o) in enumerate(zip(new, old), 1):
        if i in want:
            p = psnr(n[0], np.clip(np.round(want[i][0]), 0, 255))
            if p < 30:
                bad.append(f"frame {i} PSNR {p:.1f}")
        elif any((a != b).any() for a, b in zip(n, o)):
            bad.append(f"frame {i} changed")
    if len(new) != len(old):
        bad.append(f"{len(new)} frames decoded, {len(old)} before")
    return bad


def apply(tree, log=None):
    if not TSV.exists():
        return
    import hashlib
    p = tree / "MOV.STR"
    orig = p.read_bytes()
    data = bytearray(orig)
    for movie in sorted({int(r["movie"]) for r in rows()}):
        s0, s1 = movies(orig)[movie - 1]
        a, b = s0 * SEC, (s1 + 1) * SEC
        # ~30 s of encoding: cache the patched movie by its inputs (this file, the TSV, the fonts, the movie bytes)
        key = hashlib.sha1(Path(__file__).read_bytes() + TSV.read_bytes() + orig[a:b] + b"".join(
            f.read_bytes() for f in sorted((ROOT / "fonts").rglob("*.ttf")))).hexdigest()[:16]
        cache = ROOT / f"build/fmv_cache/mov{movie:02d}_{key}.bin"
        if cache.exists():
            data[a:b] = cache.read_bytes()
            continue
        want, _ = targets(orig, movie)
        patch_movie(data, movie)
        bad = verify(orig, data, movie, want)
        if bad:
            raise SystemExit(f"fmv: movie {movie}: " + "; ".join(bad[:5]))
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(bytes(data[a:b]))
    p.write_bytes(bytes(data))
    if log is not None:
        import insert
        insert.log_diff(log, "MOV.STR", orig, bytes(data), "fmv")


def ranges(orig_tree):
    """Byte ranges apply() may write: the sectors of every captioned frame (header + data)."""
    data = (orig_tree / "MOV.STR").read_bytes()
    out = []
    for movie in sorted({int(r["movie"]) for r in rows()}):
        fr = frames(data, movies(data)[movie - 1])
        for r in rows():
            if int(r["movie"]) == movie:
                for no in range(int(r["first"]), int(r["last"]) + 1):
                    out += [(n * SEC + 8, n * SEC + 8 + 32 + CHUNK) for n in fr[no]]
    return {"MOV.STR": sorted(set(out))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["parse", "preview"])
    ap.add_argument("movie", nargs="*", type=int)
    ap.add_argument("--str", default=str(ROOT / "work/disc/tree/MOV.STR"))
    a = ap.parse_args()
    data = Path(a.str).read_bytes()
    mvs = movies(data)
    if a.cmd == "parse":
        bad = 0
        for m in a.movie or range(1, len(mvs) + 1):
            fr = frames(data, mvs[m - 1])
            for no, secs in sorted(fr.items()):
                fb = frame_bytes(data, secs)
                try:
                    blocks, hw, used, q = parse(fb)
                except (ValueError, AssertionError) as e:
                    bad += 1
                    print(f"mov{m:02d} f{no}: {e}")
                    continue
                size = struct.unpack_from("<H", fb)[0]
                dsz = struct.unpack_from("<I", data, secs[0] * SEC + 8 + 0x0C)[0]
                if size != -(-hw // 64) * 32 or used > dsz:
                    bad += 1
                    print(f"mov{m:02d} f{no}: size {size} vs halfwords {hw}; used {used} demux {dsz}")
            print(f"mov{m:02d}: {len(fr)} frames parsed")
        sys.exit(1 if bad else 0)
    from PIL import Image
    out = ROOT / "work/fmv/preview"
    out.mkdir(parents=True, exist_ok=True)
    for m in a.movie or sorted({int(r["movie"]) for r in rows()}):
        want, jp = targets(data, m)
        buf = bytearray(data)
        info = patch_movie(buf, m)
        bad = verify(data, buf, m, want)
        s0, s1 = movies(buf)[m - 1]
        new = decode_yuv(to_2352(buf, s0, s1))
        for no in sorted(want):
            pair = np.concatenate([yuv_to_rgb(*jp[no - 1]), yuv_to_rgb(*new[no - 1])], axis=1)
            Image.fromarray(np.clip(np.round(pair), 0, 255).astype(np.uint8)).save(out / f"mov{m:02d}_f{no:04d}.png")
        qs = [q for q, _, _ in info.values()]
        print(f"mov{m:02d}: {len(info)} frames, qscale {min(qs)}-{max(qs)}, fullest "
              f"{max(u / c for _, u, c in info.values()):.0%}; verify: {'; '.join(bad[:5]) or 'ok'}")


if __name__ == "__main__":
    main()
