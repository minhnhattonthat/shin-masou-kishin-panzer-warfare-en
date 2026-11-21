"""Bisect a bug down to script ids: build with the listed ids kept Japanese (their original bytes), everything
else English. Pair with a cold-boot emu.py run per build and halve the list each round.

    python -X utf8 tools/bisect_ids.py --out build/bisect_0 --keep work/tmp/keep0.txt   (one id per line)
    python -X utf8 tools/bisect_ids.py --split exe 4 --dir work/tmp                    (writes keep0..3.txt:
                                                                                        each = all exe ids but one quarter)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))


def ids(prefix):
    out = []
    for p in sorted((ROOT / "script").rglob("*.json")):
        if p.relative_to(ROOT / "script").as_posix().startswith(prefix):
            out += [ln["id"] for ln in json.loads(p.read_text(encoding="utf-8"))["lines"]]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out")
    ap.add_argument("--keep", help="file of ids to keep Japanese")
    ap.add_argument("--split", nargs=2, metavar=("PREFIX", "N"), help="script path prefix and part count")
    ap.add_argument("--from", dest="src", help="--split this id file instead of every id under PREFIX")
    ap.add_argument("--dir", default="work/tmp")
    a = ap.parse_args()
    if a.split:
        allids = Path(a.src).read_text().split() if a.src else ids(a.split[0])
        n = int(a.split[1])
        parts = [allids[i * len(allids) // n:(i + 1) * len(allids) // n] for i in range(n)]
        for i, part in enumerate(parts):
            # build i is English only for part i (and for everything outside the split set)
            keep = [x for x in allids if x not in set(part)]
            Path(a.dir, "keep%d.txt" % i).write_text("\n".join(keep) + "\n")
            Path(a.dir, "part%d.txt" % i).write_text("\n".join(part) + "\n")
            print("part%d: %d ids, %s..%s" % (i, len(part), part[0], part[-1]))
        return
    import build
    import insert
    keep = set(Path(a.keep).read_text().split())
    orig = insert.insert

    def ins(tree, script="script", mode="en", qa=None, only=None, log=None):
        qa = dict(qa or {})
        qa.update({i: None for i in keep})
        return orig(tree, script, mode, qa, only, log)
    insert.insert = ins
    sys.argv = ["build.py", "--out", a.out]
    build.main()


if __name__ == "__main__":
    main()
