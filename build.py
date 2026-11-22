"""build.py: original disc -> build/smk_en.bin + .cue.

Checks the dump against rom.sha1, unpacks it with dumpsxiso into build/disc/ (fresh every run, so no stale edits),
patches the tree (script/ text, VWF font cells, asm/vwf.asm renderer hook) and repacks with mkpsxiso. Unpack +
repack alone is byte-identical to the original (tests/test_identity.py).
    build.py [--marker] [--qa ID=TEXT ..] [--out build/NAME]"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from check_rom import check  # noqa: E402
import cover  # noqa: E402
import fmv  # noqa: E402
import font  # noqa: E402
import gfx  # noqa: E402
import insert  # noqa: E402
import slots  # noqa: E402

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


def patch(tree, mode, qa, only=None, log=None):
    """Text (tools/insert.py), glyph slots (tools/slots.py), the VWF font cells (tools/font.py) and the renderer
    hook (asm/vwf.asm). log: {file: [writes]}, one entry per byte run each stage changed (insert.log_diff)."""
    changed = insert.insert(tree, ROOT / "script", mode, qa, only, log=log)
    exe0 = (tree / "SLPS_023.19").read_bytes()
    exe = slots.patch(exe0)
    insert.log_diff(log, "SLPS_023.19", exe0, exe, "slots")
    (tree / "SLPS_023.19").write_bytes(exe)
    for name, off in [*font.TIM_OFFS.items(), *font.TIM_COPIES]:
        p = tree / name
        old = p.read_bytes()
        p.write_bytes(font.patch_tim(old, off, exe))
        insert.log_diff(log, name, old, p.read_bytes(), "font")
    tables = ROOT / "build/vwf_tables.asm"
    tables.write_text(font.tables_asm(*font.tables((tree / "BAT_TIM.BIN").read_bytes(), font.TIM_OFFS["BAT_TIM.BIN"],
                                                   exe)), encoding="ascii")
    short = ROOT / "build/short.asm"
    short.write_text(insert.short_asm(exe, ROOT / "script/confirm_short.tsv"), encoding="ascii")
    subprocess.run([ROOT / "tools/armips/armips.exe", ROOT / "asm/vwf.asm", "-strequ", "EXE", tree / "SLPS_023.19",
                    "-strequ", "TABLES", tables, "-strequ", "SHORT", short], check=True)
    insert.log_diff(log, "SLPS_023.19", exe, (tree / "SLPS_023.19").read_bytes(), "armips")
    if mode == "en":
        gfx.apply(tree, log)  # graphics-text redraws, gfx/<group>.tsv
        fmv.apply(tree, log)  # FMV subtitles burned into MOV.STR frames, gfx/fmv/subtitles.tsv (needs ffmpeg)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", action="store_true", help="marker build: every string -> [id] + filler")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT", help="override one line (repeatable)")
    ap.add_argument("--only", nargs="+", help="bisect: change only these script/ paths (prefixes, e.g. exe events/ev0); the rest stay JP")
    ap.add_argument("--out", default="build/smk_en", help="output name without extension")
    a = ap.parse_args()
    qa = dict(x.split("=", 1) for x in a.qa)
    check()
    disc = ROOT / "build/disc"
    unpack(disc)
    log = {}
    changed = patch(disc / "tree", "marker" if a.marker else "en", {k: v.replace("\\n", "\n") for k, v in qa.items()},
                    a.only, log)
    wdir = ROOT / "build/writes"
    shutil.rmtree(wdir, ignore_errors=True)
    wdir.mkdir(parents=True)
    for name, w in log.items():
        insert.write_log(w, wdir / (name + ".log"))
    subprocess.run([sys.executable, "-X", "utf8", ROOT / "tools/writes_check.py", "--tree", disc / "tree",
                    "--writes", wdir], check=True)
    repack(disc, ROOT / a.out)
    print("strings:", cover.write_strings(disc / "tree", ROOT / (a.out + ".strings.tsv")))  # textcover keys
    print("text bytes changed:", changed)
    print("built %s.bin + .cue" % a.out)


if __name__ == "__main__":
    main()
