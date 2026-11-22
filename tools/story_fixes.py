"""Story pass bookkeeping (translation.md §Review). Reports: work/qa/story/reports/NN_evXXX.tsv, the reviewer's lines
`SEV<TAB>id<TAB>suggested English<TAB>why` + `VERDICT<TAB>ok|issue<TAB>why`.

    python -X utf8 tools/story_fixes.py verdicts         first-review verdicts -> work/qa/story/verdicts/review.tsv
    python -X utf8 tools/story_fixes.py batch bNNN       every C/I/M suggestion -> work/tl/bNNN.tsv/.out.tsv
                                                         (drop rows that fail `batches.py check`, then merge)
    python -X utf8 tools/story_fixes.py log bNNN         after the merge: story lines -> docs/polish.md "## Story pass"
                                                         (merged ids ticked "fixed", the rest unticked to settle by hand)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402
import review_fixes  # noqa: E402

STORY = batches.ROOT / "work/qa/story"


def reports():
    for p in sorted((STORY / "reports").glob("*.tsv")):
        for line in p.read_text(encoding="utf-8").splitlines():
            c = line.split("\t")
            if len(c) >= 3:
                yield p.stem, c


def english(entry, s):
    """Reviewer EN uses ' / ' for the chapter file's line breaks: keep them in multi-paragraph pages (scrolls), else
    join and let the wrap re-break."""
    s = s.strip()
    if "\n\n" in entry["jp"].strip():
        return "\\n".join(part.strip() for part in s.split(" / "))
    return " ".join(part.strip() for part in s.split(" / ") if part.strip())


def main(argv):
    if argv == ["verdicts"]:
        rows = [f"{ch}\t{c[1]}\t{c[2]}" for ch, c in reports() if c[0] == "VERDICT"]
        (STORY / "verdicts").mkdir(exist_ok=True)
        (STORY / "verdicts/review.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        return print(f"{len(rows)} verdicts ({sum(r.split(chr(9))[1] == 'ok' for r in rows)} ok)")
    cmd, batch = argv
    entries = batches.index()
    found = {c[1]: (ch, c) for ch, c in reports() if c[0] in ("C", "I", "M")}
    if cmd == "batch":
        review_fixes.write_batch(batch, {i: english(entries[i], c[2]) for i, (_, c) in found.items()}, entries)
        return print(f"{len(found)} story fixes -> work/tl/{batch}.tsv/.out.tsv")
    merged = {r[0] for r in batches.read_tsv(batches.TL / f"{batch}.out.tsv")}
    path = batches.ROOT / "docs/polish.md"
    text = path.read_text(encoding="utf-8")
    head = "## Story pass (story-reviewer Minors and C/I fixes; settle unticked ones by hand)"
    lines = [ln for ln in (text.split(head)[1].splitlines() if head in text else []) if ln.startswith("- [")]
    done = {ln.split()[3] for ln in lines}
    for i, (ch, c) in found.items():
        if i not in done:
            tick = f"- [x] {i} ({c[0]}, {ch}) - {c[2]} - {c[3] if len(c) > 3 else ''} => fixed ({batch})"
            lines.append(tick if i in merged else f"- [ ] {i} ({c[0]}, {ch}) - {c[2]} - {c[3] if len(c) > 3 else ''}")
    body = text.split(head)[0].rstrip("\n") + f"\n\n{head}\n\n" + "\n".join(lines) + "\n"
    path.write_text(body, encoding="utf-8", newline="\n")
    print(f"{len(lines)} story lines in polish.md, {sum(ln.startswith('- [ ]') for ln in lines)} unticked")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
