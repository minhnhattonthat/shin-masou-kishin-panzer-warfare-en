"""Term usage across all shipped English: which EN forms a JP term got, for settling glossary conflicts.

    python -X utf8 tools/terms.py JP [EN_FORM ...]   lines whose JP has JP; count each EN form; list lines with none
    python -X utf8 tools/terms.py --dupes [--min 2]  same JP line, different EN (consistency pass), grouped
"""
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def lines():
    for f in sorted(glob.glob(str(ROOT / 'script' / '**' / '*.json'), recursive=True)):
        for ln in json.load(open(f, encoding='utf8'))['lines']:
            if ln.get('en') and ln.get('status') != 'same':
                yield Path(f).stem, ln


def main(argv):
    if argv and argv[0] == '--dupes':
        mn = int(argv[2]) if len(argv) > 2 else 2
        by = defaultdict(lambda: defaultdict(list))
        for f, ln in lines():
            by[ln['jp'].strip()][ln['en'].strip()].append(ln['id'])
        for jp, ens in by.items():
            if len(ens) >= 2 and sum(map(len, ens.values())) >= mn:
                print('JP', jp.replace('\n', '/'))
                for en, ids in sorted(ens.items(), key=lambda x: -len(x[1])):
                    print(f'  {len(ids):3} {en!r}  {",".join(ids[:6])}')
        return 0
    jp, forms = argv[0], argv[1:]
    cnt = defaultdict(int)
    none = []
    for f, ln in lines():
        if jp in ln['jp']:
            hit = [e for e in forms if e.lower() in ln['en'].lower()]
            for e in hit:
                cnt[e] += 1
            if not hit:
                none.append(ln)
    for e in forms:
        print(f'{cnt[e]:4} {e}')
    print(f'{len(none):4} (none of these)')
    for ln in none[:15]:
        print('  ', ln['id'], ln['en'][:110].replace('\n', '/'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
