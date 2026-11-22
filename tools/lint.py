"""Text lint over script/ (budgets: docs/re/windows.md). Errors fail; unmeasured variants are counted, not failed.

    python -X utf8 tools/lint.py [--final]     (--final: untranslated lines fail unless listed in script/keep_jp.txt)

Per line with English: no Japanese left, control codes ({x}, [XX]) same multiset as the JP, encodable; event
dialogue (msg): at most 3 body lines, each <= DIALOGUE_PX of VWF advance, speaker + text <= WINDOW_GLYPHS glyph
slots, no wrap-made one-word last line in a multi-line message; exe/overlay: <= `max` bytes.
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
from slots import HUD_GLYPHS, QUOTE_GLYPHS, SCROLL_GLYPHS, WINDOW_GLYPHS  # noqa: E402

JP = re.compile(r"[぀-ヿ一-鿿！-～]")
CODES = re.compile(r"\{\w\}|\[[0-9A-F]{2}\]")
# kind -> (px per line, max lines; 0 = the JP's line count), docs/re/windows.md (measured)
BOXES = {"choice": (228, 0), "bqA": (188, 2), "bqB": (188, 2), "ov": (200, 0)}  # ov: chapter label from x=115
MEASURED = {"msg", "scroll", "choice", "bqA", "bqB", "ov"}  # the rest are counted as unmeasured
# Exe strings reached from these pointer tables (file offsets [lo, hi)) are drawn at fixed glyph-slot bases:
# (lo, hi, max glyphs, max px, what), docs/re/windows.md
TABLES = [(0xC52F8, 0xC5440, HUD_GLYPHS, 100, "battle HUD mech label"),
          (0xC5440, 0xC5668, HUD_GLYPHS, 60, "battle HUD pilot label")]  # bottom-right box 60 px from x=250
# Battle confirm screen pilot names (table exe 0xA8810, docs/re/windows.md §Confirm screen): left name x=18, "Lv."
# graphic at x=82, less a 3 px gap; longer names need a short form in script/confirm_short.tsv (D18)
PILOTS, CONFIRM_PX, SHORT_TSV = (0xA8810, 0xA8900), 61, ROOT / "script/confirm_short.tsv"


def relocatable(ln):
    """An exe string reached only through pointers/lui (not a fixed record field): insert.py moves the longer ones
    to free space (raising only when that runs out), so its `max` is not a translation limit."""
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
        if kind.startswith("bq") and font.glyphs(en) > QUOTE_GLYPHS:
            errs.append("%d glyphs > %d quote slots" % (font.glyphs(en), QUOTE_GLYPHS))
    for lo, hi, g, px, what in TABLES:
        if any(lo <= int(p, 16) < hi for p in ln.get("ptrs", [])):
            if font.glyphs(en) > g:
                errs.append("%s: %d glyphs > %d slots" % (what, font.glyphs(en), g))
            if font.width_px(en) > px:
                errs.append("%s: %d px > %d" % (what, font.width_px(en), px))
    if ln.get("kind") == "scroll":
        body = en.rstrip("\n").split("\n")
        if len(body) > ln["jp"].count("\n"):
            errs.append("%d lines > %d" % (len(body), ln["jp"].count("\n")))
        errs += ["line %d px > %d: %r" % (font.width_px(t.strip()), SCROLL_PX, t) for t in body
                 if font.width_px(t.strip()) > SCROLL_PX]
        if font.glyphs(en) > SCROLL_GLYPHS:
            errs.append("%d glyphs > %d scroll slots" % (font.glyphs(en), SCROLL_GLYPHS))
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
        # one word alone on the last line, pushed there by the wrap (it didn't fit after the line before; a hard
        # break, where it would have fitted, is the translator's choice): batches.py rewrap balances these (bug 5)
        if len(body) > 1 and len(body[-1].split()) == 1 and \
                font.width_px(body[-2] + " " + body[-1].strip()) > DIALOGUE_PX:
            errs.append("one-word last line %r" % body[-1])
    return errs


def lint(script=ROOT / "script", final=False):
    names, errs, counts = speaker_names(), [], collections.Counter()
    keep = set()
    st = Path(script) / SHORT_TSV.name
    short = dict(r.split("\t") for r in st.read_text(encoding="utf-8").splitlines() if r and r[0] != "#") \
        if st.exists() else {}
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
            if kind not in MEASURED and not any(lo <= int(p, 16) < hi for lo, hi, *_ in TABLES
                                                for p in ln.get("ptrs", [])):
                counts["unmeasured " + kind] += 1
            if relocatable(ln) and len(font.encode(ln["en"])) > ln["max"]:
                counts["exe over max (insert.py moves them)"] += 1
            errs += ["%s: %s" % (ln["id"], e) for e in check_line(ln, names)]
            if any(PILOTS[0] <= int(p, 16) < PILOTS[1] for p in ln.get("ptrs", [])):
                t = short.get(ln["id"], ln["en"])
                if font.width_px(t) > CONFIRM_PX:
                    errs.append("%s: confirm-screen pilot %r %d px > %d (add a short form to %s)"
                                % (ln["id"], t, font.width_px(t), CONFIRM_PX, SHORT_TSV.name))
    for sid, t in short.items():
        if font.width_px(t) > CONFIRM_PX:
            errs.append("%s: short form %r %d px > %d" % (sid, t, font.width_px(t), CONFIRM_PX))
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
