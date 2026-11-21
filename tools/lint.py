"""Text lint over script/ (budgets: docs/re/windows.md). Errors fail; unmeasured variants are counted, not failed.

    python -X utf8 tools/lint.py [--final]     (--final: untranslated lines fail unless listed in script/keep_jp.txt)

Per line with English: no Japanese left, control codes ({x}, [XX]) same multiset as the JP, encodable; event
dialogue (msg): at most 3 body lines, each <= DIALOGUE_PX of VWF advance, speaker + text <= WINDOW_GLYPHS glyph
slots, no stub last line (< 6 characters) in a multi-line message; exe/overlay: <= `max` bytes.
Library: lint(script_dir) -> (errors, counts)."""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import font  # noqa: E402
from insert import DIALOGUE_PX, SCROLL_PX, speaker_names  # noqa: E402
from slots import WINDOW_GLYPHS  # noqa: E402

JP = re.compile(r"[぀-ヿ一-鿿！-～]")
CODES = re.compile(r"\{\w\}|\[[0-9A-F]{2}\]")
# kind -> (px per line, max lines; 0 = the JP's line count), docs/re/windows.md (measured)
BOXES = {"choice": (228, 0), "bqA": (188, 2), "bqB": (188, 2)}
MEASURED = {"msg", "scroll", "choice", "bqA", "bqB"}  # the rest are counted as unmeasured


def relocatable(ln):
    """An exe string reached only through pointers/lui (not a fixed record field): phase 7 moves the longer ones to
    free space (status.md engine task b), so its `max` is not a translation limit. insert.py still raises on it."""
    return ln["id"].startswith("exe_") and "region" not in ln and bool(ln.get("ptrs") or ln.get("lui"))


def check_line(ln, names):
    """Errors for one script line with English."""
    en, jp, errs = ln["en"], ln["jp"], []
    if JP.search(en):
        errs.append("Japanese left: %r" % JP.findall(en)[:5])
    if sorted(CODES.findall(en)) != sorted(CODES.findall(jp)):
        errs.append("control codes %s != JP %s" % (CODES.findall(en), CODES.findall(jp)))
    try:
        b = font.encode(en)
    except Exception as e:  # noqa: BLE001  (unencodable character)
        return errs + ["not encodable: %s" % e]
    if "max" in ln and len(b) > ln["max"] and not relocatable(ln):
        errs.append("%d bytes > max %d" % (len(b), ln["max"]))
    kind = ln.get("kind", ln["id"].split("_")[0])
    if kind in BOXES:
        px, n = BOXES[kind]
        body = en.rstrip("\n").split("\n")
        n = n or ln["jp"].rstrip("\n").count("\n") + 1
        if len(body) > n:
            errs.append("%d lines > %d" % (len(body), n))
        errs += ["line %d px > %d: %r" % (font.width_px(t), px, t) for t in body if font.width_px(t) > px]
    if ln.get("kind") == "scroll":
        body = en.rstrip("\n").split("\n")
        if len(body) > ln["jp"].count("\n"):
            errs.append("%d lines > %d" % (len(body), ln["jp"].count("\n")))
        errs += ["line %d px > %d: %r" % (font.width_px(t.strip()), SCROLL_PX, t) for t in body
                 if font.width_px(t.strip()) > SCROLL_PX]
    if ln.get("kind") == "msg":
        body = en.rstrip("\n").split("\n")
        if len(body) > 3:
            errs.append("%d lines > 3" % len(body))
        for t in body:
            if font.width_px(t) > DIALOGUE_PX:
                errs.append("line %d px > %d: %r" % (font.width_px(t), DIALOGUE_PX, t))
        g = font.glyphs(names.get(ln["speaker"], ln["speaker"]) + en)
        if g > WINDOW_GLYPHS:
            errs.append("%d glyphs > %d" % (g, WINDOW_GLYPHS))
        if len(body) > 1 and len(body[-1].strip()) < 6:
            errs.append("stub last line %r" % body[-1])
    return errs


def lint(script=ROOT / "script", final=False):
    names, errs, counts = speaker_names(), [], collections.Counter()
    keep = set()
    kp = Path(script) / "keep_jp.txt"
    if kp.exists():
        keep = {r.split()[0] for r in kp.read_text(encoding="utf-8").splitlines() if r.strip() and r[0] != "#"}
    for p in sorted(Path(script).rglob("*.json")):
        for ln in json.loads(p.read_text(encoding="utf-8"))["lines"]:
            kind = ln.get("kind", ln["id"].split("_")[0])
            if not ln.get("en"):
                if ln.get("jp") and ln.get("kind") != "dummy" and not ln.get("same") and ln["id"] not in keep:
                    counts["untranslated"] += 1
                    if final:
                        errs.append("%s: untranslated" % ln["id"])
                continue
            counts["english"] += 1
            if kind not in MEASURED:
                counts["unmeasured " + kind] += 1
            if relocatable(ln) and len(font.encode(ln["en"])) > ln["max"]:
                counts["exe over max (relocate in phase 7)"] += 1
            errs += ["%s: %s" % (ln["id"], e) for e in check_line(ln, names)]
    return errs, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    errs, counts = lint(final=a.final)
    for e in errs:
        print(e)
    print("%d errors; %s" % (len(errs), ", ".join("%s %d" % kv for kv in sorted(counts.items()))))
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
