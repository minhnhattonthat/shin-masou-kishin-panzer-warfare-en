"""Which script ids a cover log dir shows, and which of them textcover still reports NEVER SHOWN.

    python -X utf8 tools/cover_ids.py work/qa/cover/<run> [..] [--strings build/smk_en.strings.tsv]
                                      [--report work/qa/textcover.txt]
Prints "<id> new|seen" per shown id (new = in the report's NEVER SHOWN list), then the count of new ones."""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cover  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dirs", nargs="+")
    p.add_argument("--strings", default="build/smk_en.strings.tsv")
    p.add_argument("--report", default="work/qa/textcover.txt")
    a = p.parse_args()
    bykey = {key: i for i, key, _, _, _ in cover.read_strings(a.strings)}
    with open(a.report, encoding="utf-8") as f:
        never = {m.group(1) for m in (re.match(r"NEVER SHOWN\s+(\S+)", line) for line in f) if m}
    shown = set()
    for d in a.dirs:
        for log in glob.glob(os.path.join(d, "**", "log.txt"), recursive=True):
            with open(log, encoding="ascii", errors="replace") as f:
                shown |= {bykey[int(line.split()[1], 16)] for line in f if line.startswith("TEXT ")}
    new = sorted(shown & never)
    for i in sorted(shown):
        print(i, "new" if i in never else "seen")
    print("%d shown, %d new" % (len(shown), len(new)))


if __name__ == "__main__":
    main()
