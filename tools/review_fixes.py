"""Turn reviewer reports into a merge batch and the polish list.

docs/review/reports.tsv rows: batch<TAB>SEV<TAB>id<TAB>English<TAB>reason (SEV C/I/M; `batch VERDICT text` rows too).

    python -X utf8 tools/review_fixes.py BATCH [--done FILE]   C/I rows -> work/tl/BATCH.tsv/.out.tsv (then
                                                              batches.py merge BATCH --overwrite)
    python -X utf8 tools/review_fixes.py --polish              M rows -> docs/polish.md (unticked, deduped by id)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402

ROOT = batches.ROOT
REPORTS = ROOT / 'docs' / 'review' / 'reports.tsv'


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
        for i, (b, _, en, why) in rows({'M'}).items():
            if i not in fixed:
                out.append(f'- [ ] {i} ({b}) - {en} - {why}')
        (ROOT / 'docs' / 'polish.md').write_text('\n'.join(out) + '\n', encoding='utf8', newline='\n')
        return print(f'{len(out) - 5} polish lines')
    batch = argv[0]
    fix = rows({'C', 'I'})
    missing = [i for i in fix if i not in entries]
    assert not missing, f'unknown ids {missing}'
    tl = batches.TL
    with open(tl / f'{batch}.tsv', 'w', encoding='utf8', newline='\n') as f:
        for i in fix:
            e = entries[i]
            f.write('\t'.join([i, e.get('speaker', ''), 'review-fix', '', e['jp'].strip().replace('\n', ' / ')]) + '\n')
    with open(tl / f'{batch}.out.tsv', 'w', encoding='utf8', newline='\n') as f:
        for i, (_, _, en, _) in fix.items():
            f.write(f'{i}\t{en}\n')
    print(f'{len(fix)} fixes -> work/tl/{batch}.tsv/.out.tsv')


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
