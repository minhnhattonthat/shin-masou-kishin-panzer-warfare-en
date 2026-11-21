"""Translation batches (docs/translator-brief.md): split untranslated text, check translator output, merge it back.

    python -X utf8 tools/batches.py split [--size 3500]   work/tl/bNNN.tsv and build/terms_bNNN.txt for untranslated JP
    python -X utf8 tools/batches.py check [bNNN ...]      a batch's .out.tsv; with no batch, all shipped English (for check.py)
    python -X utf8 tools/batches.py merge bNNN ... [--overwrite]   check, then write the English into script/
    python -X utf8 tools/batches.py terms                 refresh build/terms_bNNN.txt after a glossary edit

Copied from the skill's assets/batches.py. Fit the ADAPTER section to this game's text format; the rest is shared.
Batch TSV: id, speaker, form, limit, JP. Output: work/tl/bNNN.out.tsv, id<TAB>English, every id once, same order.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "work/tl"
SCRIPT = ROOT / "script"
GLOSSARY = ROOT / "glossary.md"
MAX_ENTRIES = 150

# ---- ADAPTER: this game's text format ----
sys.path.insert(0, str(ROOT / "tools"))
import font  # noqa: E402
import lint  # noqa: E402
from insert import DIALOGUE_PX, speaker_names  # noqa: E402

TOKEN = lint.CODES  # {b} colour/font codes and [XX] bytes; must survive translation
FREE = set()  # layout codes the English may place freely
VARIABLE = r"\[var[^\]]*\]"  # no drawn-number placeholders in this game; kept for the shared rule
HONORIFICS = {}  # kept per glossary, but JP rarely writes them; the reviewer checks them
WRAP = {"msg": DIALOGUE_PX, "bq": lint.BOXES["bqA"][0]}  # auto-wrapped kinds; the rest keep the translator's \n
NAMES = speaker_names(GLOSSARY)


def docs():
    """(path, doc, entries) per script file; entries hold id, jp, en, and optionally speaker, kind, max."""
    for path in sorted(SCRIPT.rglob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        yield path, doc, doc["lines"]


def needs_english(entry):
    """Dummies, and battle set B (its text is set A's, `same`), need none."""
    return bool(entry.get("jp")) and not entry.get("en") and entry.get("kind") != "dummy" and not entry.get("same")


def group_of(entry):
    return entry["id"]


def entry_key(entry):
    return entry["id"]


def form(entry):
    return entry.get("kind") or {"bqA": "bq", "exe": "menu", "ov": "label"}[entry["id"].split("_")[0]]


def limit_label(entry):
    f, n = form(entry), entry["jp"].rstrip("\n").count("\n") + 1
    return {"msg": "240px x3 lines (auto-wrapped)", "bq": "188px x2 lines (auto-wrapped)",
            "choice": f"228px/line, {n} lines", "scroll": f"256px/line, {entry['jp'].count(chr(10))} lines max"
            }.get(f, f"{entry.get('max')} bytes")


def jp_cell(entry):
    return entry["jp"].rstrip("\n").replace("\n", " / ")


def _wrap1(seg, px):
    if font.width_px(seg) <= px:
        return [seg]
    lines, cur = [], ""
    for w in seg.split():
        if cur and font.width_px(cur + " " + w) > px:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    lines.append(cur)
    if len(lines) > 1 and len(lines[-1]) < 6:  # pull a word down rather than leave a stub
        head, _, last = lines[-2].rpartition(" ")
        if head and font.width_px(last + " " + lines[-1]) <= px:
            lines[-2:] = [head, last + " " + lines[-1]]
    return lines


def wrap(entry, en):
    """Translator output -> stored English: literal \\n become breaks; msg/bq are word-wrapped to the box."""
    en = en.replace("\\n", "\n").strip("\n")
    px = WRAP.get(form(entry))
    return "\n".join(t for seg in en.split("\n") for t in _wrap1(seg, px)) if px else en


def width_problems(entry, en):
    """The text lint's own rules (px per measured box, lines, glyph slots, stubs, bytes)."""
    return lint.check_line({**entry, "en": en}, NAMES)


def encodable(char):
    try:
        font.encode(char)
        return True
    except Exception:  # noqa: BLE001
        return False
# ---- end of ADAPTER ----


def kind(char):
    if "぀" <= char <= "ゟ":
        return "hiragana"
    if "゠" <= char <= "ヿ":
        return "katakana"
    if "一" <= char <= "鿿" or char == "々":
        return "kanji"
    return "other"


def has_term(jp, term):
    """term occurs as a whole kana or kanji run: ミン isn't in タイミング, くも isn't in ぼくも."""
    jp = jp.replace(" / ", "")
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        if (a == 0 or kind(jp[a - 1]) != kind(term[0])) and (b == len(jp) or kind(jp[b]) != kind(term[-1])):
            return True
    return False


def glossary():
    """[(JP forms, EN forms, avoid forms)] from glossary.md's | JP | EN | max | notes | Avoid | tables."""
    rows = []
    if not GLOSSARY.exists():
        return rows
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-: "):
            avoid = [x.strip() for x in cells[4].split("/") if x.strip()] if len(cells) > 4 else []
            rows.append(([x.strip() for x in cells[0].split("/")], [x.strip() for x in cells[1].split("/")], avoid))
    return rows


def problems(entry, en, terms):
    """Every rule, on one line of English."""
    jp = entry["jp"]
    if not en.strip():
        return ["empty English"]
    out = []
    plain = TOKEN.sub("", en)
    if bad := sorted({c for c in plain if not encodable(c) and c != "\n"}):
        out.append(f"unencodable characters {bad}")
    if re.search(r"\\u[0-9a-fA-F]{4}", en) or "\t" in en:
        out.append("escape sequence or tab in the English")
    want = Counter(t for t in TOKEN.findall(jp) if t not in FREE)
    have = Counter(t for t in TOKEN.findall(en) if t not in FREE)
    if want != have:
        out.append(f"control codes differ: JP {dict(want)} EN {dict(have)}")
    if re.search(VARIABLE + r"(st|nd|rd|th)\b", en):
        out.append('ordinal suffix after a variable (write "No. [var]")')
    jp_plain = TOKEN.sub("", jp)
    en_terms = " ".join(TOKEN.sub(lambda m: " " if m[0] in FREE else m[0], en).replace("\\n", " ").split()).lower()
    for jps, ens, avoid in terms:
        if any(has_term(jp_plain, j) for j in jps) and not any(" ".join(e.split()).lower() in en_terms for e in ens):
            out.append(f"glossary: {jps[0]} -> {ens[0]}")
        out += [f"glossary Avoid: {a}" for a in avoid if re.search(rf"\b{re.escape(a)}\b", en)]
    for jp_form, en_form in HONORIFICS.items():
        if jp_form in jp_plain and en_form.lower() not in en.lower():
            out.append(f"honorific {jp_form} needs {en_form}")
    return out + width_problems(entry, en)


def index():
    result = {}
    for _, _, entries in docs():
        for e in entries:
            key = entry_key(e)
            if key in result:
                raise ValueError(f"duplicate batch key {key!r}: supply a unique addr or adapt entry_key")
            result[key] = e
    return result


def read_tsv(path):
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing():
    return sorted(TL.glob("b[0-9][0-9][0-9].tsv"))


def split(size):
    """Numbers on from the last batch and leaves out ids already batched, so a repeat run can't duplicate work."""
    index()  # reject ambiguous ids before writing any batches
    TL.mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(exist_ok=True)
    taken = {r[0] for p in existing() for r in read_tsv(p)}
    n = max((int(p.stem[1:]) for p in existing()), default=0)
    groups = {}
    for _, _, entries in docs():
        for e in entries:
            if needs_english(e) and entry_key(e) not in taken:
                groups.setdefault(group_of(e), []).append(e)
    batches, cur, chars = [], [], 0
    for group in groups.values():
        c = sum(len(TOKEN.sub("", e["jp"])) for e in group)
        if cur and (chars + c > size or len(cur) + len(group) > MAX_ENTRIES):
            batches.append(cur)
            cur, chars = [], 0
        cur += group
        chars += c
    if cur:
        batches.append(cur)
    terms = glossary()
    for batch in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        if path.exists():
            sys.exit(f"{path} already exists")
        rows = [f"{entry_key(e)}\t{NAMES.get(e.get('speaker') or '', e.get('speaker') or '')}\t{form(e)}\t"
                f"{limit_label(e)}\t{jp_cell(e)}" for e in batch]
        path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        jps = " ".join(TOKEN.sub("", e["jp"]) for e in batch)
        used = [(j, ens[0]) for jpl, ens, _ in terms for j in jpl if has_term(jps, j)]
        (ROOT / f"build/terms_{name}.txt").write_text("".join(f"{j}\t{e}\n" for j, e in used)
                                                      or "(no glossary terms in this batch)\n", encoding="utf-8", newline="\n")
    print(f"{len(batches)} new batches in {TL}, {len(taken)} ids already batched")


def check_batch(batch, entries, terms):
    want = [r[0] for r in read_tsv(TL / f"{batch}.tsv")]
    rows = [(r[0], wrap(entries[r[0]], "\t".join(r[1:])) if r[0] in entries else "\t".join(r[1:]))
            for r in read_tsv(TL / f"{batch}.out.tsv")]
    bad = []
    if [r[0] for r in rows] != want:
        got = [r[0] for r in rows]
        dup = sorted(i for i, c in Counter(got).items() if c > 1)
        bad.append(f"ids differ: missing {sorted(set(want) - set(got))[:8]} extra {sorted(set(got) - set(want))[:8]} "
                   f"duplicate {dup[:8]} (order must match too)")
    for eid, en in rows:
        if eid in entries:
            bad += [f"{eid}: {p}: {en!r}" for p in problems(entries[eid], en, terms)]
    return bad, dict(rows)


def merge(new, overwrite):
    """Refuses to replace different English unless told to, before anything is written."""
    if not overwrite:
        for _, _, entries in docs():
            for e in entries:
                if entry_key(e) in new and e.get("en") and e["en"] != new[entry_key(e)]:
                    sys.exit(f"{e['id']} would lose {e['en']!r}: pass --overwrite if that is meant")
    changed = 0
    for path, doc, entries in docs():
        touched = False
        for e in entries:
            if entry_key(e) in new and e.get("en") != new[entry_key(e)]:
                e["en"], e["status"] = new[entry_key(e)], "done"
                touched = True
                changed += 1
        if touched:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged: {changed} entries changed")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "split":
        return split(int(args[args.index("--size") + 1]) if "--size" in args else 3500)
    if cmd == "terms":  # refresh build/terms_bNNN.txt after a glossary change
        terms = glossary()
        for path in existing():
            jps = " ".join(TOKEN.sub("", r[4]) for r in read_tsv(path))
            used = [(j, ens[0]) for jpl, ens, _ in terms for j in jpl if has_term(jps, j)]
            (ROOT / f"build/terms_{path.stem}.txt").write_text("".join(f"{j}\t{e}\n" for j, e in used)
                                                               or "(no glossary terms in this batch)\n",
                                                               encoding="utf-8", newline="\n")
        return print(f"terms refreshed for {len(existing())} batches")
    overwrite = "--overwrite" in args
    names = [a for a in args if a != "--overwrite"]
    entries, terms = index(), glossary()
    if cmd == "check" and not names:
        bad = [f"{i}: {p}: {e['en']!r}" for i, e in entries.items() if e.get("en") for p in problems(e, e["en"], terms)]
        print(f"{len(entries)} entries, {len(bad)} problems")
        print("\n".join(bad[:200]))
        return 1 if bad else 0
    if cmd not in ("check", "merge") or not names:
        sys.exit(__doc__)
    failed = 0
    for batch in names:
        bad, rows = check_batch(batch, entries, terms)
        failed += bool(bad)
        print(f"{batch}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
        if cmd == "merge" and not bad:
            merge(rows, overwrite)
    return 1 if failed else 0


def _selftest():
    assert has_term("ミンが来た", "ミン") and not has_term("タイミング", "ミン")
    msg = {"id": "x", "kind": "msg", "jp": "「あ」\n\n\n", "speaker": ""}
    long = " ".join(["word"] * 40)
    out = wrap(msg, long).split("\n")
    assert len(out) > 1 and all(font.width_px(t) <= DIALOGUE_PX for t in out) and len(out[-1]) >= 6
    assert wrap(msg, "A\\nB") == "A\nB"  # literal \n from the TSV forces a break
    assert wrap({"id": "exe_1", "jp": "あ", "max": 4}, "Hi there") == "Hi there"  # menus are never wrapped
    assert width_problems({"id": "exe_1", "jp": "あ", "max": 4}, "Hi there")  # 8 bytes > 4
    print("selftest ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--selftest"]:
        _selftest()
    else:
        sys.exit(main(sys.argv[1:]))
