"""Reviewer pairs files (docs/reviewer-brief.md) from translation batches, with the merged English from script/.

    python -X utf8 tools/pairs.py b001 b002 ... [--out work/qa/review]   -> <out>/<batch>.txt

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


def main(argv):
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else batches.ROOT / "work/qa/review"
    names = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--out")]
    out.mkdir(parents=True, exist_ok=True)
    entries = batches.index()
    for b in names:
        (out / f"{b}.txt").write_text(pairs(b, entries), encoding="utf-8", newline="\n")
    print(f"{len(names)} pairs files in {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
