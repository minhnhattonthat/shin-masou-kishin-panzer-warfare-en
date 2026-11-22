"""tools/fmv.py: the MDEC v2 encoder writes what the disc's own frames look like (parse: every block, the size word,
the 0x1FF end code) and what ffmpeg decodes back close to the source."""
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fmv  # noqa: E402


def _frame():
    yy, xx = np.mgrid[0:224, 0:320]
    y = (xx * 0.6 + yy * 0.3 + 40 * np.sin(xx / 7.0)) % 256
    y[100:130, 50:270] = 250  # a hard-edged bright bar, like caption text
    cb = (128 + 60 * np.cos(np.mgrid[0:112, 0:160][1] / 9.0))
    cr = (128 + 50 * np.sin(np.mgrid[0:112, 0:160][0] / 5.0))
    return np.round(y), np.round(cb), np.round(cr)


def test_encode_parses_like_the_disc():
    y, cb, cr = _frame()
    bs, size = fmv.encode(y, cb, cr, 4)
    blocks, hw, used, q = fmv.parse(bs)  # raises without the end code or on a bad code
    assert (blocks, q) == (20 * 14 * 6, 4)
    assert struct.unpack_from("<H", bs)[0] == size == -(-hw // 64) * 32
    assert used <= len(bs)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="no ffmpeg")
def test_ffmpeg_decodes_close():
    y, cb, cr = _frame()
    bs, size = fmv.encode(y, cb, cr, 2)
    secs = -(-len(bs) // fmv.CHUNK)
    data = bytearray()
    for k in range(secs):
        hdr = struct.pack("<4sHHIIHHHHHHI", fmv.MAGIC, k, secs, 1, (len(bs) + 3) & ~3, 320, 224, size, 0x3800, 2, 2, 0)
        payload = (hdr + bs[k * fmv.CHUNK:(k + 1) * fmv.CHUNK]).ljust(2048, b"\0")
        data += bytes.fromhex("0101480001014800") + payload + bytes(280)
    data += bytes(fmv.SEC * 4)  # to_2352 reads 4 sectors past the end
    out = fmv.decode_yuv(fmv.to_2352(bytes(data), 0, secs - 1))
    assert out and fmv.psnr(out[0][0], y) > 35
