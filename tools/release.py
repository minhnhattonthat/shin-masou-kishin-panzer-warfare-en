"""Release: build, gate, patch, verify, zip. Stops at the first failure.

    python -X utf8 tools/release.py [--version 1.0] [--force]

Steps: build.py (plain: no --marker/--qa/--only, so no debug or QA strings) -> check.py -> emu.py --smoke ->
jp_left.py on the exe, OVER.BIN and BAT_OVER.BIN -> qa_gate.py check on every work/qa/**/*manifest.tsv ->
textcover.py -> no unticked line in docs/polish.md -> no template placeholder in README.md -> xdelta3 patch ->
re-apply to the clean original and compare -> release/SMK_EN_vX.Y.zip (patch + README.txt, ZIP_STORED).
The debug tool (tools/debug/warp.lua etc.) runs in the emulator only; nothing of it is on the disc.
Never publishes: `gh release create` is the user's call.
"""
import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

PY = [sys.executable, "-X", "utf8"]
ORIG = ROOT / "rom/Shin Masou Kishin - Panzer Warfare (Japan).bin"
BUILT = ROOT / "build/smk_en.bin"
SCRIPTS = Path(SKILL) / "scripts"
# Old battle-quote blocks (set A sectors 0-0x4A, set B 0xB6-0x100) stay in BAT_OVER.BIN unreferenced after phase-7
# relocation (docs/re/battle.md §Relocation): scan only the rest of the file.
JP_SCANS = [("SLPS_023.19", ["--known", "script/jp_known.txt"]), ("OVER.BIN", []),
            ("BAT_OVER.BIN", ["--range", "25000-5AFFF", "--range", "80000-1000000"])]


def run(name, cmd):
    print(f"== {name}", flush=True)
    if subprocess.run(cmd, cwd=ROOT).returncode:
        sys.exit(f"release stopped: {name} failed")


def hashes(path):
    d = path.read_bytes()
    return len(d), f"{zlib.crc32(d):08X}", hashlib.md5(d).hexdigest(), hashlib.sha1(d).hexdigest()


def gates():
    for m in sorted((ROOT / "work/qa").rglob("*manifest.tsv")):
        verdicts = m.parent / ("verdicts" if m.name == "manifest.tsv" else m.name.replace("manifest.tsv", "verdicts"))
        run(f"qa_gate {m.relative_to(ROOT)}", PY + [SCRIPTS / "qa_gate.py", "check", m, verdicts])


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite this version's existing release files")
    a = ap.parse_args(argv)
    out = ROOT / "release"
    patch, zpath = out / f"SMK_EN_v{a.version}.xdelta", out / f"SMK_EN_v{a.version}.zip"
    if (patch.exists() or zpath.exists()) and not a.force:
        sys.exit(f"{zpath} exists: pass --force to overwrite v{a.version}")

    run("build", PY + ["build.py"])
    run("check", PY + ["tools/check.py"])
    run("smoke", PY + [SCRIPTS / "emu.py", "build/smk_en.cue", "--out", "work/qa/release_smoke", "--frames", "3600",
                       "--smoke"])
    for f, extra in JP_SCANS:
        run(f"jp_left {f}", PY + [SCRIPTS / "jp_left.py", f"build/disc/tree/{f}", "--orig", f"work/disc/tree/{f}",
                                  "--sjis"] + extra)
    gates()
    run("textcover", PY + [SCRIPTS / "textcover.py", "work/qa/cover", "build/smk_en.strings.tsv",
                           "--waive", "docs/text_unshown.tsv"])
    if re.search(r"^- \[ \]", (ROOT / "docs/polish.md").read_text(encoding="utf-8"), re.M):
        sys.exit("release stopped: docs/polish.md has unticked lines")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if re.search(r"<(Game title|platform|publisher|year|repo|file|size|sha1|[A-Z][a-z]+ /)[^>]*>", readme):
        sys.exit("release stopped: README.md still has template placeholders")

    out.mkdir(exist_ok=True)
    patch.unlink(missing_ok=True)
    size = ORIG.stat().st_size
    run("xdelta", ["xdelta3", "-e", "-9", "-B", str(size), "-s", ORIG, BUILT, patch])
    with tempfile.TemporaryDirectory() as tmp:
        back = Path(tmp) / "applied.bin"
        run("re-apply", ["xdelta3", "-d", "-s", ORIG, patch, back])
        if hashes(back) != hashes(BUILT):
            sys.exit("release stopped: the re-applied patch differs from build/smk_en.bin")
    o, b = hashes(ORIG), hashes(BUILT)
    text = (ROOT / "docs/release-readme.txt").read_text(encoding="utf-8").format(
        version=a.version, patch=patch.name, size=o[0], crc=o[1], md5=o[2], sha1=o[3],
        p_size=b[0], p_crc=b[1], p_md5=b[2], p_sha1=b[3])
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        z.write(patch, patch.name)
        z.writestr("README.txt", text.replace("\n", "\r\n"))
    print(f"release ok: {zpath} ({zpath.stat().st_size} bytes), patched .bin CRC32 {b[1]} SHA-1 {b[3]}")


if __name__ == "__main__":
    main(sys.argv[1:])
