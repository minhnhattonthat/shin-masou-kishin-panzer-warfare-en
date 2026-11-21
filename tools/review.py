"""Independent batch review with `codex exec` (read-only), per docs/reviewer-brief.md; reports land in files.

    python -X utf8 tools/review.py run b001 b002 ... [--jobs 4]   pairs + codex review -> work/qa/review/bNNN.md
    python -X utf8 tools/review.py summary [bNNN ...]              Critical/Important counts and verdict per report

Each run deletes the old report first, so a failed run can't leave stale verdicts. The prompt carries the brief,
glossary, style reference, synopsis and the pairs file (codex's sandbox can't read beyond what it is given reliably)."""
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import pairs  # noqa: E402

OUT = ROOT / "work/qa/review"
DOCS = ["docs/reviewer-brief.md", "glossary.md", "docs/style-reference.md", "docs/synopsis.md"]


def prompt(batch, text):
    parts = [f"=== {d} ===\n" + (ROOT / d).read_text(encoding="utf-8") for d in DOCS]
    return ("You are the read-only reviewer described in the first document. Review the pairs file at the end "
            "(batch %s). Follow the report format exactly; in each finding start with the id. Give only real "
            "issues; Minors at most 15.\n\n" % batch) + "\n\n".join(parts) + f"\n\n=== pairs {batch} ===\n{text}"


def run_one(batch, entries):
    OUT.mkdir(parents=True, exist_ok=True)
    text = pairs.pairs(batch, entries)
    (OUT / f"{batch}.txt").write_text(text, encoding="utf-8", newline="\n")
    rep = OUT / f"{batch}.md"
    rep.unlink(missing_ok=True)
    r = subprocess.run([shutil.which("codex"), "exec", "-s", "read-only", "--skip-git-repo-check", "-o", str(rep)],
                       input=prompt(batch, text), text=True, encoding="utf-8", capture_output=True, cwd=ROOT)
    return batch, rep.exists(), r.returncode


def sections(md):
    """{'Critical': [lines], 'Important': [...], 'Minor': [...]}, plus the Assessment line."""
    out, cur = {"Critical": [], "Important": [], "Minor": []}, None
    verdict = ""
    for line in md.splitlines():
        h = re.match(r"#+\s*(Critical|Important|Minor|Assessment)", line)
        if h:
            cur = h[1]
            continue
        if cur == "Assessment" and line.strip():
            verdict = verdict or line.strip()
        elif cur in out and re.match(r"\s*[-*\d]", line) and re.search(r"[A-Za-z]{2,}\w*_\w+", line):
            out[cur].append(line.strip())
    return out, verdict


def main(argv):
    cmd, args = argv[0], argv[1:]
    jobs = int(args[args.index("--jobs") + 1]) if "--jobs" in args else 4
    names = [a for i, a in enumerate(args) if re.fullmatch(r"b\d{3}", a)]
    if cmd == "run":
        entries = batches.index()
        with ThreadPoolExecutor(jobs) as ex:
            for b, ok, rc in ex.map(lambda b: run_one(b, entries), names):
                print(b, "ok" if ok else f"FAILED rc={rc}", flush=True)
    elif cmd == "summary":
        for rep in sorted(OUT.glob("b[0-9][0-9][0-9].md")):
            if names and rep.stem not in names:
                continue
            s, v = sections(rep.read_text(encoding="utf-8"))
            print(f"{rep.stem} C{len(s['Critical'])} I{len(s['Important'])} M{len(s['Minor'])} | {v[:90]}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
