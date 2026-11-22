"""Text coverage for this game: the string table a build writes and the probe logs turned into textcover.py input.

    python -X utf8 tools/cover.py strings build/disc/tree build/smk_en.strings.tsv   (build.py runs this)
    python -X utf8 tools/cover.py logs work/qa/tour [more dirs] --strings build/smk_en.strings.tsv --out work/qa/cover
    python -X utf8 $SKILL/scripts/textcover.py work/qa/cover build/smk_en.strings.tsv --waive docs/text_unshown.tsv

STRINGS.tsv: id, key (hex row number: textcover.py wants one key per id), RAM address, built bytes (hex). Strings
share RAM (35 event blocks in one slot, overlays loaded into it, quote blocks in two slots), so `logs` matches each
"PTR <addr> <bytes>" line of tools/lua/textcover.lua to the string whose range holds addr AND whose built bytes at
that point equal the logged ones, and writes "TEXT <key>" lines to OUT/<run>/log.txt. A battle quote in set B has
the same text as its set-A twin (`same`, rebuilt by the same code into a same-size slot), so either one covers both.
"""
import argparse, glob, json, os, struct, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batquote, insert, over  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _cstr(buf, o):
    return bytes(buf[o:buf.index(0, o)])


def table(tree, script=ROOT / "script"):
    """[(id, ram address, built bytes, twin id or None)] for every script string, from the built tree."""
    tree, files = Path(tree), insert._load(script)
    exe = (tree / "SLPS_023.19").read_bytes()
    ovr = (tree / "OVER.BIN").read_bytes()
    bat = (tree / "BAT_OVER.BIN").read_bytes()
    out = []
    t = struct.unpack_from("<36H", exe, insert.TABLE)
    events = [f for rel, f in files.items() if rel.startswith("events/")]  # insert.events/relayout order
    for i, f in enumerate(events):
        blk = ovr[t[i] * 0x800:t[i + 1] * 0x800]
        for ln in f["lines"]:
            a = struct.unpack_from("<I", blk, int(ln["ptrs"][0], 16))[0]
            out.append((ln["id"], a, _cstr(blk, a - over.BASE), None))
    for name, off, _ in batquote.SETS:
        lines = files["battle_%s.json" % name]["lines"]
        sec, nbase = batquote.sector_list(exe, off), insert.BQ[name][1]
        per = defaultdict(list)
        for ln in lines:
            per[ln["id"].split("_")[1]].append(ln)
        for j, key in enumerate(per):  # blocks in sector order, strings laid from +4, each NUL-padded to 4
            blk, o = bat[sec[j] * 0x800:sec[j + 1] * 0x800], 4
            for ln in per[key]:
                s = _cstr(blk, o)
                out.append((ln["id"], nbase + o, s, ln.get("same")))
                o += (len(s) + 4) & ~3
    for ln in files["exe.json"]["lines"]:
        if ln.get("ptrs"):
            a = struct.unpack_from("<I", exe, int(ln["ptrs"][0], 16))[0]
        elif ln.get("lui"):
            p = int(ln["lui"][0], 16)
            a = insert.lui_target(*(struct.unpack_from("<I", exe, q)[0] for q in (p, insert.lo_users(exe, p)[0])))
        else:
            a = insert.EXE_BASE + int(ln["id"].split("_")[1], 16)
        out.append((ln["id"], a, _cstr(exe, a - insert.EXE_BASE), None))
    ov = files["overlay.json"]
    for ln in ov["lines"]:
        o = int(ln["id"].split("_")[1], 16)
        out.append((ln["id"], o + int(ov["ram_minus_file"], 16), _cstr(ovr, o), None))
    return out


def write_strings(tree, path):
    rows = table(tree)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# id\tkey\taddr\tbytes\ttwin (tools/cover.py)\n")
        for k, (i, a, b, twin) in enumerate(rows):
            f.write("%s\t%X\t%08X\t%s\t%s\n" % (i, k, a, b.hex().upper(), twin or ""))
    return len(rows)


def read_strings(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#"):
                i, k, a, b, twin = line.rstrip("\n").split("\t")
                rows.append((i, int(k, 16), int(a, 16), bytes.fromhex(b), twin))
    return rows


def match(rows):
    """f(addr, logged bytes) -> keys of every string holding those bytes at addr (+ quote twins)."""
    pages, key_of = defaultdict(list), {r[0]: r[1] for r in rows}
    twins = defaultdict(set)
    for i, k, a, b, twin in rows:
        if twin:
            twins[k].add(key_of[twin])
            twins[key_of[twin]].add(k)
        for p in range(a >> 8, (a + len(b)) // 256 + 1):
            pages[p].append((a, b, k))

    def f(addr, got):
        keys = {k for a, b, k in pages[addr >> 8] if a <= addr <= a + len(b) and b[addr - a:addr - a + len(got)] == got}
        return keys.union(*(twins[k] for k in keys)) if keys else keys
    return f


def logs(dirs, strings, out):
    f, total, miss = match(read_strings(strings)), 0, 0
    for d in dirs:
        for log in glob.glob(os.path.join(d, "**", "log.txt"), recursive=True):
            keys = set()
            for line in open(log, encoding="utf-8", errors="replace"):
                if line.startswith("PTR "):
                    _, a, *rest = line.split()
                    got = bytes.fromhex(rest[0]) if len(rest) > 1 else b""
                    k = f(int(a, 16), got)
                    total, miss = total + 1, miss + (not k)
                    keys |= k
            if keys:
                dst = Path(out) / os.path.relpath(os.path.dirname(log), os.path.dirname(os.path.normpath(d)))
                dst.mkdir(parents=True, exist_ok=True)
                (dst / "log.txt").write_text("".join("TEXT %X\n" % k for k in sorted(keys)), encoding="ascii")
    print("%d PTR lines, %d matched no string (buffers, numbers)" % (total, miss))


def _selftest():
    rows = [("a", 0, 0x100, b"Hello", "b"), ("b", 1, 0x200, b"Hello", ""), ("c", 2, 0x100, b"Bye", "")]
    f = match(rows)
    assert f(0x100, b"Hel") == {0, 1} and f(0x101, b"ello") == {0, 1} and f(0x100, b"Bye") == {2}
    assert f(0x100, b"Xyz") == set() and f(0x300, b"") == set()
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("strings")
    s.add_argument("tree")
    s.add_argument("out")
    g = sub.add_parser("logs")
    g.add_argument("dirs", nargs="+")
    g.add_argument("--strings", default="build/smk_en.strings.tsv")
    g.add_argument("--out", default="work/qa/cover")
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "strings":
        print("%d strings -> %s" % (write_strings(a.tree, a.out), a.out))
    elif a.cmd == "logs":
        logs(a.dirs, a.strings, a.out)
    else:
        _selftest()


if __name__ == "__main__":
    main()
