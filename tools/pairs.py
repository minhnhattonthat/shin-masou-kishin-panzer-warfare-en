"""Reviewer pairs files (docs/reviewer-brief.md) from translation batches, with the merged English from script/.

    python -X utf8 tools/pairs.py b001 b002 ... [--out work/qa/review]   -> <out>/<batch>.txt
    python -X utf8 tools/pairs.py --chapters   story-pass files work/qa/story/chapters/NN_evXXX.txt (re-run after edits)

Each entry: `>> id | speaker | form | JP` (JP line breaks as ` / `), then `   EN` (breaks as ` / `). Batches are in
story order, so the neighbours are the context."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402


def pairs(batch, entries):
    out = []
    for row in batches.read_tsv(batches.TL / f"{batch}.tsv"):
        e = entries[row[0]]
        out.append(f">> {row[0]} | {row[1]} | {row[2]} | {row[4]}\n   {e.get('en', '').replace(chr(10), ' / ')}")
    return "\n".join(out) + "\n"


def chapters(out):
    """Story pass: one file per event block (= chapter, docs/synopsis.md), entries in pool (story) order."""
    import json
    import re
    syn = (batches.ROOT / "docs/synopsis.md").read_text(encoding="utf-8")
    titles = {m[2]: (int(m[1]), m[3]) for m in re.finditer(r'^(\d+)\. (ev\w+) "([^"]+)"', syn, re.M)}
    out.mkdir(parents=True, exist_ok=True)
    for path in sorted((batches.SCRIPT / "events").glob("ev*.json")):
        n, title = titles[path.stem]
        lines = [f"# Chapter {n}: {title} ({path.stem}). Entries in script order; choices and their answers follow"
                 " each other, and battle win/lose branches may sit side by side.", ""]
        for e in json.loads(path.read_text(encoding="utf-8"))["lines"]:
            if e.get("kind") == "dummy":
                continue
            sp = e.get("speaker") or ""
            sp = batches.NAMES.get(sp, sp)
            jp = e["jp"].replace("　", "").strip().replace("\n", " / ")
            lines.append(f">> {e['id']} | {sp} | {e.get('kind')} | {jp}\n   {e.get('en', '').replace(chr(10), ' / ')}")
        (out / f"{n:02d}_{path.stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(titles)} chapters in {out}")


def main(argv):
    if argv[:1] == ["--chapters"]:
        return chapters(batches.ROOT / "work/qa/story/chapters")
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else batches.ROOT / "work/qa/review"
    names = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--out")]
    out.mkdir(parents=True, exist_ok=True)
    entries = batches.index()
    for b in names:
        (out / f"{b}.txt").write_text(pairs(b, entries), encoding="utf-8", newline="\n")
    print(f"{len(names)} pairs files in {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
