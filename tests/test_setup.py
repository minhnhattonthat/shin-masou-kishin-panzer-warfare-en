import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rom_sha1_listing_is_filled():
    lines = [l for l in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    assert lines and all(len(l.split()[0]) == 40 for l in lines)


def test_rom_matches_when_present():
    if not (ROOT / "rom").is_dir() or not any((ROOT / "rom").glob("*.bin")):
        return  # fresh clone without the dump
    assert subprocess.call([sys.executable, str(ROOT / "tools" / "check_rom.py")]) == 0
