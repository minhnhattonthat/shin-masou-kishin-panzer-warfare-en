"""Turn reviewer reports into a merge batch and the polish list.

docs/review/reports.tsv rows: batch<TAB>SEV<TAB>id<TAB>English<TAB>reason (SEV C/I/M; `batch VERDICT text` rows too).

    python -X utf8 tools/review_fixes.py BATCH [--done FILE]   C/I rows -> work/tl/BATCH.tsv/.out.tsv (then
                                                              batches.py merge BATCH --overwrite)
    python -X utf8 tools/review_fixes.py --polish              M rows -> docs/polish.md (unticked, deduped by id)
    python -X utf8 tools/review_fixes.py --from-polish BATCH   unticked polish suggestions -> merge batch
    python -X utf8 tools/review_fixes.py --tick BATCH          tick polish lines the merged BATCH fixed
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402

ROOT = batches.ROOT
REPORTS = ROOT / 'docs' / 'review' / 'reports.tsv'
HAND = '## Hand-kept'


def rows(sevs):
    seen = {}
    for line in REPORTS.read_text(encoding='utf8').splitlines():
        c = line.split('\t')
        if len(c) >= 4 and c[1] in sevs:
            seen[c[2]] = (c[0], c[1], c[3], c[4] if len(c) > 4 else '')  # a later row for an id wins
    return seen


def main(argv):
    entries = batches.index()
    if argv == ['--polish']:
        out = ['# Polish list', '', 'Minor reviewer notes (phase 6 review), applied in one polish pass before release.',
               'Tick a line when applied or rejected. Format: id (batch) - suggested English - reason.', '']
        fixed = rows({'C', 'I'})  # an id with a merged C/I fix needs no polish line
        old = (ROOT / 'docs' / 'polish.md').read_text(encoding='utf8')
        ticked = {ln.split()[3]: ln for ln in old.split(HAND)[0].splitlines() if ln.startswith('- [x] ')}
        for i, (b, _, en, why) in rows({'M'}).items():
            if i not in fixed:
                out.append(ticked.get(i, f'- [ ] {i} ({b}) - {en} - {why}'))  # a ticked line keeps its tick
        hand = old[old.find(HAND):] if HAND in old else ''  # cuts / open questions added by hand survive a regen
        (ROOT / 'docs' / 'polish.md').write_text('\n'.join(out) + '\n' + ('\n' + hand if hand else ''),
                                                 encoding='utf8', newline='\n')
        return print(f'{len(out) - 5} polish lines')
    if argv[0] == '--from-polish':  # unticked full-line suggestions -> merge batch (notes in "(...)" stay manual)
        batch, pol = argv[1], (ROOT / 'docs' / 'polish.md').read_text(encoding='utf8').split(HAND)[0]
        fix = {m[1]: m[2] for m in re.finditer(r'^- \[ \] (\S+) \(b\d+\) - (.*?) - ', pol, re.M)
               if m[1] in entries and not m[2].startswith('(')}
        write_batch(batch, fix, entries)
        return print(f'{len(fix)} polish rows -> work/tl/{batch}.tsv/.out.tsv (append twins by hand, then merge)')
    if argv[0] == '--tick':  # run after `batches.py merge BATCH` succeeded (a merge is all or nothing)
        batch, path = argv[1], ROOT / 'docs' / 'polish.md'
        done = {r[0] for r in batches.read_tsv(batches.TL / f'{batch}.out.tsv')}
        text, n = path.read_text(encoding='utf8'), 0
        out = []
        for ln in text.splitlines():
            parts = ln.split()
            if ln.startswith('- [ ] ') and len(parts) > 3 and parts[3] in done:
                ln, n = f'- [x] {ln[6:]} => fixed ({batch})', n + 1
            out.append(ln)
        path.write_text('\n'.join(out) + '\n', encoding='utf8', newline='\n')
        return print(f'{n} lines ticked')
    batch = argv[0]
    fix = rows({'C', 'I'})
    write_batch(batch, {i: v[2] for i, v in fix.items()}, entries)
    print(f'{len(fix)} fixes -> work/tl/{batch}.tsv/.out.tsv')


def write_batch(batch, fix, entries):
    missing = [i for i in fix if i not in entries]
    assert not missing, f'unknown ids {missing}'
    assert not (batches.TL / f'{batch}.tsv').exists(), f'{batch} exists'
    with open(batches.TL / f'{batch}.tsv', 'w', encoding='utf8', newline='\n') as f:
        for i in fix:
            e = entries[i]
            f.write('\t'.join([i, e.get('speaker', ''), 'review-fix', '', e['jp'].strip().replace('\n', ' / ')]) + '\n')
    with open(batches.TL / f'{batch}.out.tsv', 'w', encoding='utf8', newline='\n') as f:
        for i, en in fix.items():
            f.write(f'{i}\t{en}\n')


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
