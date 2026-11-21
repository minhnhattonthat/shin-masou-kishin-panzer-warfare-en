"""Identity build: unpack + repack with no edits must give the original disc byte for byte (keep green forever)."""
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


@pytest.mark.skipif(not build.CUE.is_file(), reason="fresh clone without the dump")
def test_unpack_repack_is_byte_identical():
    lines = (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines()
    want = next(l.split()[0] for l in lines if l.strip() and not l.startswith("#"))
    work = ROOT / "build/identity"
    build.unpack(work / "disc")
    build.repack(work / "disc", work / "identity")
    with open(work / "identity.bin", "rb") as f:
        assert hashlib.file_digest(f, "sha1").hexdigest() == want
