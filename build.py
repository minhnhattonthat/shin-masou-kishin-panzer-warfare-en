"""build.py: original disc -> build/smk_en.bin + .cue.

Checks the dump against rom.sha1, unpacks it with dumpsxiso into build/disc/ (fresh every run, so no stale edits),
then repacks with mkpsxiso. With no edits the output is byte-identical to the original (tests/test_identity.py)."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from check_rom import check  # noqa: E402

MKPSXISO = ROOT / "tools/mkpsxiso/mkpsxiso-2.30-win64"
CUE = ROOT / "rom/Shin Masou Kishin - Panzer Warfare (Japan).cue"


def unpack(disc):
    """Extract the original disc into disc/tree + disc/layout.xml."""
    shutil.rmtree(disc, ignore_errors=True)
    disc.mkdir(parents=True)
    subprocess.run([MKPSXISO / "dumpsxiso.exe", "-q", "-x", "tree", "-s", "layout.xml", CUE], cwd=disc, check=True)


def repack(disc, out):
    """Build out.bin + out.cue from disc/layout.xml."""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([MKPSXISO / "mkpsxiso.exe", "-q", "-y", "-o", out.with_suffix(".bin"), "-c", out.with_suffix(".cue"),
                    "layout.xml"], cwd=disc, check=True)


def main():
    check()
    disc = ROOT / "build/disc"
    unpack(disc)
    repack(disc, ROOT / "build/smk_en")
    print("built build/smk_en.bin + .cue")


if __name__ == "__main__":
    main()
