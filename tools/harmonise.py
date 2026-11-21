"""Consistency pass: one English form per repeated JP line (same speaker for events), as a merge batch.

    python -X utf8 tools/harmonise.py BATCH [--min 3] [--minlen 8]   write work/tl/BATCH.tsv + .out.tsv, print the plan
    then: python -X utf8 tools/batches.py merge BATCH --overwrite

The majority English wins (ties: the form used first in script order). Wrap-only differences are ignored.
"""
import sys
from collections import defaultdict
from pathlib import Path

from terms import lines

ROOT = Path(__file__).resolve().parent.parent


def plan(min_total=3, min_len=8):
    groups = defaultdict(list)
    for _, ln in lines():
        jp = ln['jp'].strip()
        if len(jp.replace('\n', '').replace('　', '')) < min_len:
            continue
        groups[(jp, ln.get('speaker', ''))].append(ln)
    out = []
    for (jp, spk), lns in groups.items():
        norm = lambda e: ' '.join(e.split())
        forms = defaultdict(list)
        for ln in lns:
            forms[norm(ln['en'])].append(ln)
        if len(lns) < min_total or len(forms) < 2:
            continue
        win = max(forms.values(), key=len)  # max keeps the first of equal lengths: script order
        out.append((jp, spk, win[0]['en'], [ln for ln in lns if norm(ln['en']) != norm(win[0]['en'])]))
    return out


def main(argv):
    batch = argv[0]
    mn = int(argv[argv.index('--min') + 1]) if '--min' in argv else 3
    ml = int(argv[argv.index('--minlen') + 1]) if '--minlen' in argv else 8
    rows = []
    for jp, spk, en, losers in plan(mn, ml):
        print(f'{len(losers):3} -> {en!r}  ({spk}) {jp[:30]!r}')
        rows += [(ln['id'], spk, ln['jp'], en) for ln in losers]
    tl = ROOT / 'work' / 'tl'
    with open(tl / f'{batch}.tsv', 'w', encoding='utf8', newline='\n') as f:
        for i, spk, jp, _ in rows:
            f.write('\t'.join([i, spk, 'harmonise', '', jp.strip().replace('\n', ' / ')]) + '\n')
    with open(tl / f'{batch}.out.tsv', 'w', encoding='utf8', newline='\n') as f:
        for i, _, _, en in rows:
            f.write(f'{i}\t' + en.replace('\n', '\\n') + '\n')
    print(f'{len(rows)} lines -> work/tl/{batch}.tsv/.out.tsv')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
