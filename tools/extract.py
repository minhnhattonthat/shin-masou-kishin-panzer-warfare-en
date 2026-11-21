"""Extract every game string to script/*.json (formats in docs/re/scripts.md, battle.md).

Sources (original disc tree, default work/disc/tree):
  OVER.BIN event blocks  -> script/events/evXXX.json (XXX = block start sector): messages, choices, the two
                            chapter-intro scroll pages, ダミー placeholders
  BAT_OVER.BIN quotes    -> script/battle_A.json, script/battle_B.json
  SLPS_023.19 strings    -> script/exe.json (u32-pointer, lui-pair and fixed-record strings)
  OVER.BIN overlay text  -> script/overlay.json (chapter "…まで終了" save labels)

Entry fields: id (address-based, stable), jp (sjis.decode of the bytes before the NUL), en ("" until translated),
plus per source: kind and speaker (events msg/choice: the first line; jp is the rest), ptrs (offsets of the u32
words pointing at the string: block-relative for events, file offsets elsewhere), lui (file offsets of lui
instructions), max (bytes the string may use in place, without its NUL), recs (battle records pointing at it),
same (battle set B: the set-A id with the same text).

Usage: extract.py [--tree DIR] [--out script] [--merge]
  Writes missing files only. --merge refreshes jp/meta in existing files and keeps en/notes/status per id; it
  refuses if an id that has English would disappear. Library: extract(tree) -> {relpath: {"lines": [...], ...}}."""
import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batquote  # noqa: E402
import over  # noqa: E402
from sjis import decode, is_lead  # noqa: E402

T_BASE = 0x800A5800  # exe RAM = T_BASE + file offset
KEEP = ("en", "notes", "status")  # translator-owned fields that --merge preserves
# exe strings with no pointer of their own: (lo, hi, grid). grid = (record stride, ((field offset, field len), ..))
# anchored at lo; strings in a grid region must start on a field and may fill it minus the NUL.
EXE_REGIONS = {
    "yes": (0x4064, 0x40B0, None),  # memory-card YES prompts
    "spirit": (0xACFD0, 0xAD60E, (0x5E, ((4, 11), (0xF, 0x4F)))),  # spirit command name + description records
    "objective": (0xAD684, 0xAD8D8, None),  # stage win/lose conditions, space-padded, packed
    "mcard": (0xB4940, 0xB4AF7, None),  # memory-card file titles (shown by the BIOS card manager too)
    "status": (0xB7702, 0xB7AC8, (0x2E, ((0, 0x20),))),  # status-page labels + layout data
    "quote": (0xC3DC8, 0xC4CB0, None),  # 109 battle quotes 「…」, reader unknown (docs/re/battle.md)
}
# pointer-reached byte runs that decode as SJIS but are data (moving them breaks the game: status.md bug 3)
NOT_TEXT = {
    0xA72E8: "90 78 20 00 inside a 12-byte sprite-record table (map weapon-list window); 0xAC4B0 points at the record",
}
LABEL_TABLE = 0xED024  # OVER.BIN: u32 RAM pointers to the save-slot chapter labels, first at file 0xECB74
LABEL_FIRST = 0xECB74


def cstr(d, o):
    return d[o:d.index(0, o)]


def slot(d, o, limit):
    """Bytes the string at o may use in place: up to the next non-zero byte (or limit), minus the NUL."""
    e = d.index(0, o)
    while e < limit and d[e] == 0:
        e += 1
    return e - o - 1


def h(x):
    return "0x%X" % x


# --- OVER.BIN events ---------------------------------------------------------------------------------------------

def event_strings(d, s, e):
    """Every string an aligned u32 RAM pointer in block [s, e) reaches: ({offset: [(word offset, kind)]}, pools).
    kind: msg (word c of an op 0x384 command), choice (op 0x0001), scroll (the 2-entry chapter-intro page table),
    dummy (ダミー placeholders). pools = [lo, hi) runs of strings separated only by NUL padding (hi 4-aligned)."""
    tg = {}
    for i in range(s, e - 3, 4):
        w = struct.unpack_from("<I", d, i)[0]
        if not over.BASE <= w < over.BASE + (e - s) or not text_end(d, o := s + w - over.BASE):
            continue
        op = struct.unpack_from("<I", d, i - 8)[0] & 0xFFFF if i - 8 >= s else None
        kind = {over.MSG_OP: "msg", 1: "choice"}.get(op) or ("dummy" if cstr(d, o) == "ダミー".encode("cp932")
                                                              else "scroll")
        tg.setdefault(o, []).append((i, kind))
    pools = []
    for o in sorted(tg):
        end = (d.index(0, o) + 4) & ~3
        if pools and not any(d[pools[-1][1]:o]):
            pools[-1][1] = end
        else:
            pools.append([o, end])
    return tg, pools


def events(d):
    out = {}
    for s, e in over.blocks(d):
        tg, pools = event_strings(d, s, e)
        lines = []
        for o in sorted(tg):
            kinds = sorted({k for _, k in tg[o]})
            ln = {"id": "ev%03X_%04X" % (s // 0x800, o - s), "kind": "/".join(kinds),
                  "ptrs": [h(i - s) for i, _ in tg[o]]}
            if kinds[0] in ("choice", "msg"):  # speaker line, then the box text
                ln["speaker"], _, ln["jp"] = decode(cstr(d, o)).partition("\n")
            else:
                ln["jp"] = decode(cstr(d, o))
            ln["en"] = ""
            lines.append(ln)
        out["events/ev%03X.json" % (s // 0x800)] = {
            "source": "OVER.BIN", "block": [h(s), h(e)], "base": h(over.BASE),
            "pools": [[h(a - s), h(b - s)] for a, b in pools], "lines": lines}
    return out


# --- BAT_OVER.BIN battle quotes ------------------------------------------------------------------------------------

def battle(exe, d):
    sets = {}
    for name, base, a, b in batquote.blocks(exe):
        blk = d[a * 0x800:b * 0x800]
        bid, strings, recs = batquote.parse(blk, base)
        cnt = {}
        for r in recs:
            t = struct.unpack_from("<I", blk, r + 4)[0] - base
            cnt[t] = cnt.get(t, 0) + 1
        sets.setdefault(name, []).append((a, b, bid, [(o, decode(s), cnt.get(o, 0)) for o, s in strings]))
    out = {}
    for name, blocks in sets.items():
        lines = []
        for k, (a, b, bid, strings) in enumerate(blocks):
            twin = sets["A"][k] if name == "B" else None
            same = twin and [s for _, s, _ in twin[3]] == [s for _, s, _ in strings]
            for j, (o, s, n) in enumerate(strings):
                ln = {"id": "bq%s_%02X_%03X" % (name, a, o), "jp": s, "en": "", "recs": n}
                if same:
                    ln["same"] = "bqA_%02X_%03X" % (twin[0], twin[3][j][0])
                lines.append(ln)
        base = dict((n, b) for n, _, b in batquote.SETS)[name]
        out["battle_%s.json" % name] = {"source": "BAT_OVER.BIN", "base": h(base), "lines": lines,
                                        "blocks": [[h(a), h(b), h(bid)] for a, b, bid, _ in blocks]}
    return out


# --- exe -----------------------------------------------------------------------------------------------------------

def text_end(d, i):
    """End offset of a text string at i (SJIS pairs, newline, control letters), or None if a byte isn't text."""
    j, n = i, 0
    while d[j]:
        c = d[j]
        if is_lead(c) and c <= 0xEF:
            try:
                d[j:j + 2].decode("cp932")
            except UnicodeDecodeError:
                return None
            j, n = j + 2, n + 1
        elif c in (0x0A, 0x20) or chr(c) in "bhmrwz":  # objectives pad with half-width spaces
            j += 1
        else:
            return None
    return j if n else None


def lui_targets(e):
    import importlib.util
    spec = importlib.util.spec_from_file_location("exe_refs", Path(__file__).with_name("re.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.lui_targets(e)


def exe_strings(e):
    words = {}
    for k in range(0x800, len(e) - 3, 4):
        words.setdefault(struct.unpack_from("<I", e, k)[0], []).append(k)
    lui = lui_targets(e)
    lines, i = [], 0x800
    while i < len(e):
        # a string follows a NUL, or directly follows a u32 RAM pointer (top byte 0x80) of a pointer table
        if e[i] and (not e[i - 1] or i % 4 == 0 and e[i - 1] == 0x80) and (j := text_end(e, i)):
            a = T_BASE + i
            region = next((r for r, (lo, hi, _) in EXE_REGIONS.items() if lo <= i < hi), None)
            if (a in words or a in lui or region) and i not in NOT_TEXT:
                ln = {"id": "exe_%05X" % i, "jp": decode(e[i:j]), "en": ""}
                if a in words:
                    ln["ptrs"] = [h(k) for k in words[a]]
                if a in lui:
                    ln["lui"] = [h(pc - T_BASE) for pc in lui[a]]
                lim = len(e)
                if region:
                    ln["region"] = region
                    lo, hi, grid = EXE_REGIONS[region]
                    lim = hi
                    if grid:
                        stride, fields = grid
                        f = [(lo + (i - lo) // stride * stride + fo, n) for fo, n in fields]
                        f = [x for x in f if x[0] == i]
                        assert f, "exe %X: not on a %s field" % (i, region)
                        lim = i + f[0][1]
                ln["max"] = min(slot(e, i, lim), lim - i - 1)
                lines.append(ln)
            i = j
            continue
        i += 1
    return {"exe.json": {"source": "SLPS_023.19", "base": h(T_BASE), "lines": lines}}


# --- OVER.BIN overlay labels ---------------------------------------------------------------------------------------

def overlay(d):
    ptrs, o = [], LABEL_TABLE
    while 0x801C0000 <= (w := struct.unpack_from("<I", d, o)[0]) < 0x80200000:
        ptrs.append((o, w))
        o += 4
    delta = LABEL_FIRST - ptrs[0][1]
    lines = []
    for k, (po, w) in enumerate(ptrs):
        s = w + delta
        nxt = ptrs[k + 1][1] + delta if k + 1 < len(ptrs) else LABEL_TABLE
        lines.append({"id": "ov_%05X" % s, "ptrs": [h(po)], "jp": decode(cstr(d, s)), "en": "",
                      "max": min(slot(d, s, nxt), nxt - s - 1)})
    return {"overlay.json": {"source": "OVER.BIN", "table": h(LABEL_TABLE), "ram_minus_file": h(-delta & 0xFFFFFFFF),
                             "lines": lines}}


def extract(tree):
    tree = Path(tree)
    exe = (tree / "SLPS_023.19").read_bytes()
    ovr = (tree / "OVER.BIN").read_bytes()
    out = {}
    out.update(events(ovr))
    out.update(battle(exe, (tree / "BAT_OVER.BIN").read_bytes()))
    out.update(exe_strings(exe))
    out.update(overlay(ovr))
    return out


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def merge(new, old):
    keep = {ln["id"]: ln for ln in old["lines"]}
    ids = {ln["id"] for ln in new["lines"]}
    lost = [i for i, ln in keep.items() if i not in ids and ln.get("en")]
    if lost:
        raise SystemExit("merge would drop translated ids: %s" % lost[:10])
    for ln in new["lines"]:
        for k in KEEP:
            if k in keep.get(ln["id"], {}):
                ln[k] = keep[ln["id"]][k]
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default="work/disc/tree")
    ap.add_argument("--out", default="script")
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()
    wrote = kept = 0
    for rel, obj in extract(a.tree).items():
        p = Path(a.out) / rel
        if p.exists():
            if not a.merge:
                kept += 1
                continue
            obj = merge(obj, json.loads(p.read_text(encoding="utf-8")))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(dump(obj), encoding="utf-8", newline="\n")
        wrote += 1
    print("wrote %d files, left %d existing (use --merge to refresh them)" % (wrote, kept))


if __name__ == "__main__":
    main()
