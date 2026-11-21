"""Write script/ text into an unpacked disc tree (the reverse of extract.py; formats in docs/re/scripts.md, battle.md).

Modes:
  en      each line's `en` (encoded with font.encode); lines with no English keep their original bytes
  marker  every line replaced by `[id]` + filler of the original line's byte length (exe/overlay: the field's
          `max`), so nothing can overflow; shows which string each box comes from and how wide each box is
Overrides (`qa`: {id: text}) replace single lines in either mode (width-gate rulers, torture lines).

Event pools and battle string areas are repacked from their start and every pointer rewritten; exe and overlay
strings are written in place up to `max`. Raises Overflow listing every line that doesn't fit.
Library: insert(tree, script_dir, mode="en", qa=None) -> {file: changed byte count}."""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batquote  # noqa: E402
import font  # noqa: E402
import over  # noqa: E402

MAX_BLOCK = 0x1F * 0x800  # the event loader 0x800F1F48 hangs ("over 0x10000") on a block of 0x20+ sectors
TABLE = 0xAFFE4  # exe file offset (RAM 0x801557E4) of the u16 OVER.BIN sector list; event block i = [t[i], t[i+1])
OVER_SECTORS, OVER_READ_END = 0x219, 0x21C  # OVER.BIN size; its last sector-list entry
DIALOGUE_PX = 240  # event box line budget (docs/re/windows.md, measured)
SCROLL_PX = 256  # chapter-intro page line budget from x=32 (docs/re/windows.md)
# Battle quote slots (docs/re/battle.md §Relocation): set -> (exe offset of its word in the load-address table
# 0x800AB7B8, new RAM base, exe offset of its 65 x 12-byte entries whose +4 is the block's record pointer).
# New slots sit in the event-slot tail 0x801CB118-0x801D1D18: no writes there during battle (trap 2026-11-22),
# and the event block is reloaded after every battle.
BQ = {"A": (0x5FB8, 0x801CB118, 0xC59D8), "B": (0x5FC4, 0x801CE718, 0xC5CE4)}
BQ_MAX = 0x3600
EXE_BASE = 0x800A5800  # RAM = EXE_BASE + exe file offset
# Moved exe strings: the tail of the trap-tested VWF run after asm/vwf.asm (its VWF_FREE_END). Not 0x80170938+:
# a zero run there is live BSS (library code writes it at boot; the build went black), docs/re/battle.md.
EXE_FREE = (0x8016DA60, 0x8016DC40)
FILLER ="The quick brown fox jumps over the lazy dog. Sphinx of black quartz, judge my vow. "


class Overflow(Exception):
    pass


def filler(n, head=""):
    """head + filler text, exactly n encoded bytes (head cut if longer)."""
    return (head + FILLER * (n // len(FILLER) + 2))[:n]  # ASCII: one byte per character


_CW = {}


def fill_px(px, head=""):
    """head + filler text, as many characters as fit in px of VWF pen advance (no trailing space)."""
    s, w = head + FILLER * 4, 0
    for i, ch in enumerate(s):
        w += _CW.setdefault(ch, font.width_px(ch))
        if w > px:
            return s[:i].rstrip()
    raise ValueError(px)


def marker_text(ln, jp, budget=None):
    """Marker for one line: each text line -> filler, the id on the first one.
    Event dialogue (kind msg): each line filled to the measured box width (DIALOGUE_PX), so the marker build
    shows the widest English a box can hold and stresses the pool growth. Other lines: the JP byte length.
    budget (exe/overlay): one line filling `budget` bytes, id shortened to fit."""
    if budget is not None:
        tag = ln["id"].split("_", 1)[1].lstrip("0") or "0"
        head = "[%s]" % ln["id"] if budget >= len(ln["id"]) + 2 else tag
        return filler(budget, head)[:budget]
    out, first = [], True
    # battle quotes are short and their areas full: compact id bqA_00_004 -> A00.004
    head = "%s%s.%s " % tuple(ln["id"][2:].split("_")) if ln["id"].startswith("bq") else "[%s] " % ln["id"]
    for part in jp.split("\n"):
        n = len(font.encode(part))
        if not n:
            out.append("")
            continue
        out.append(fill_px(DIALOGUE_PX, head if first else "") if ln.get("kind") == "msg" else
                   filler(n, head if first else ""))
        first = False
    return "\n".join(out)


def speaker_names(glossary=Path(__file__).resolve().parents[1] / "glossary.md"):
    """JP -> EN from glossary.md's Characters table (the speaker line of event messages in en mode)."""
    names, on = {}, False
    for row in Path(glossary).read_text(encoding="utf-8").splitlines():
        if row.startswith("## "):
            on = row.strip() == "## Characters"
        elif on and row.startswith("|"):
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) > 1 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-"):
                names[cells[0]] = cells[1]
    return names


def _load(script):
    return {p.relative_to(script).as_posix(): json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(Path(script).rglob("*.json"))}


def _text(ln, mode, qa, budget=None, body="jp"):
    """Encoded bytes for a line, or None to keep the original bytes."""
    if ln["id"] in qa:
        return None if qa[ln["id"]] is None else font.encode(qa[ln["id"]])
    if mode == "marker":
        return font.encode(marker_text(ln, ln[body], budget))
    if not ln.get("en"):
        return None
    en = ln["en"]
    if ln.get("kind") == "msg":  # keep the JP's line-terminator count (body padded to the box's 3 lines)
        en = en.rstrip("\n")
        en += "\n" * max(1, ln["jp"].count("\n") - en.count("\n"))
    elif ln.get("kind") == "scroll":
        en = center_scroll(en, ln["jp"].count("\n"))
    return font.encode(en)


def center_scroll(en, n_newlines):
    """Chapter-intro page: each line centred in SCROLL_PX with spaces (the JP centres with full-width spaces),
    padded with empty lines to the JP's line count (a u16 table before the pages may be per-line)."""
    lines = [t.strip() for t in en.rstrip("\n").split("\n")]
    lines = [" " * round((SCROLL_PX - font.width_px(t)) / 2 / font.SPACE) + t if t else "" for t in lines]
    return "\n".join(lines) + "\n" * max(1, n_newlines - len(lines) + 1)


def _repack(buf, lo, hi, items, where, extra=None):
    """items: [(old_off, bytes, [ptr word offsets], value_base)]; lays strings from lo, 4-aligned, NUL-terminated,
    rewrites each pointer to value_base + new offset. extra=(lo2, hi2): once the pool is full, the rest go there
    (buf grows as needed). Raises Overflow (nothing written then)."""
    cur, place = lo, []
    for old, b, ptrs, vb in items:
        if extra and cur < extra[0] and cur + len(b) + 1 > hi:
            cur = extra[0]
        place.append((cur, b, ptrs, vb))
        cur = (cur + len(b) + 1 + 3) & ~3
    end = place[-1][0] + len(place[-1][1]) + 1 if place else lo  # up to the last string's NUL
    if end > (extra[1] if extra and end > hi else hi):
        raise Overflow("%s: pool 0x%X-0x%X (+ %s) needs up to 0x%X" % (where, lo, hi, extra and "0x%X-0x%X" % extra, end))
    buf[lo:hi] = bytes(hi - lo)
    if end > len(buf):
        buf.extend(bytes(end - len(buf)))
    for off, b, ptrs, vb in place:
        buf[off:off + len(b)] = b
        for p in ptrs:
            struct.pack_into("<I", buf, p, vb + off)


def events(ovr, files, mode, qa):
    """Repack each event block's pools; strings that don't fit the pool go after the block's end (up to MAX_BLOCK).
    Returns (errors, [block bytes in disc order])."""
    errs, out, names = [], [], speaker_names()
    for rel, f in files.items():
        if not rel.startswith("events/"):
            continue
        s, e = (int(x, 16) for x in f["block"])
        blk = bytearray(ovr[s:e])
        for i, (lo, hi) in enumerate((int(a, 16), int(b, 16)) for a, b in f["pools"]):
            items = []
            for ln in f["lines"]:
                o = int(ln["id"].split("_")[1], 16)
                if not lo <= o < hi:
                    continue
                orig = bytes(blk[o:blk.index(0, o)])
                if "speaker" in ln:
                    new = _text(ln, mode, qa)
                    spk = names.get(ln["speaker"], ln["speaker"]) if mode == "en" else ln["speaker"]
                    b = orig if new is None else font.encode(spk) + b"\n" + new
                elif ln["kind"] == "dummy":
                    b = orig
                else:
                    b = _text(ln, mode, qa)
                    b = orig if b is None else b
                items.append((o, b, [int(p, 16) for p in ln["ptrs"]], over.BASE))
            try:
                _repack(blk, lo, hi, items, "%s pool %d" % (rel, i), extra=((len(blk) + 3) & ~3, MAX_BLOCK))
            except Overflow as e:
                errs.append(str(e))
        out.append(bytes(blk))
    return errs, out


def relayout(ovr, exe, blocks, ttim):
    """Event blocks move to the end of OVER.BIN (they may have grown) and the exe's sector list follows them.
    The old event sectors are zeroed. OVER.BIN's last overlay reads 3 sectors past the file end (into T_TIM on the
    original disc, docs/re/disc.md), so those 3 T_TIM sectors are copied in first."""
    t = list(struct.unpack_from("<%dH" % (len(blocks) + 1), exe, TABLE))
    assert t[0] == 0 and t[-1] == over.EVENT_END_SECTOR and len(ovr) == OVER_SECTORS * 0x800, "sector list moved?"
    ovr[:over.EVENT_END_SECTOR * 0x800] = bytes(over.EVENT_END_SECTOR * 0x800)
    ovr += ttim[:(OVER_READ_END - OVER_SECTORS) * 0x800]
    for i, b in enumerate(blocks):
        t[i] = len(ovr) // 0x800
        ovr += b + bytes(-len(b) % 0x800)
    t[len(blocks)] = len(ovr) // 0x800
    struct.pack_into("<%dH" % len(t), exe, TABLE, *t)


def _pad(s):
    return s + bytes(4 - len(s) % 4)  # NUL-terminated, 4-aligned


def battle(bat, exe, files, mode, qa):
    """Rebuild every quote block for its new RAM slot (BQ): id, strings, then its records (record pointers rebased,
    the exe's per-block record-pointer table entry rewritten). Returns (errors, {set: [block bytes]}) for
    battle_relayout. docs/re/battle.md §Relocation."""
    errs, out = [], {"A": [], "B": []}
    a_lines = {ln["id"]: ln for ln in files["battle_A.json"]["lines"]}
    for name, base, a, b in batquote.blocks(bytes(exe)):
        _, nbase, tab = BQ[name]
        lines = {ln["id"]: ln for ln in files["battle_%s.json" % name]["lines"]}
        blk = bytes(bat[a * 0x800:b * 0x800])
        _, strings, recs = batquote.parse(blk, base)
        new, where = bytearray(blk[:4]), {}
        for o, orig in strings:
            ln = lines["bq%s_%02X_%03X" % (name, a, o)]
            src = a_lines[ln["same"]] if ln.get("same") and mode == "en" and ln["id"] not in qa else ln
            t = _text(src, mode, qa)
            where[base + o] = nbase + len(new)
            new += _pad(orig if t is None else t)
        recs_out = []
        for r in recs:
            kind, p, q = struct.unpack_from("<3I", blk, r)
            if p not in where:  # block 0x20/0xD6: a kind-0 record aimed past the strings (bytes 02 00): keep them
                where[p] = nbase + len(new)
                new += _pad(blk[p - base:blk.index(0, p - base)])
            recs_out.append(struct.pack("<3I", kind, where[p], q))
        struct.pack_into("<I", exe, tab + 12 * len(out[name]) + 4, nbase + len(new))
        new += b"".join(recs_out)
        if len(new) > BQ_MAX:
            errs.append("battle %s block 0x%X: 0x%X bytes > slot 0x%X" % (name, a, len(new), BQ_MAX))
        out[name].append(bytes(new))
    return errs, out


def battle_relayout(bat, exe, out):
    """Quote blocks go to the end of BAT_OVER.BIN, set by set (the old sectors stay, unread); the exe's u16 sector
    lists and slot bases follow."""
    for name, off, _ in batquote.SETS:
        t = []
        for blk in out[name]:
            t.append(len(bat) // 0x800)
            bat += blk + bytes(-len(blk) % 0x800)
        t.append(len(bat) // 0x800)
        assert len(t) == len(batquote.sector_list(exe, off)), "quote sector list length changed"
        struct.pack_into("<%dH" % len(t), exe, off, *t)
        struct.pack_into("<I", exe, BQ[name][0], BQ[name][1])


def _relocate(buf, longs, free):
    """Pointer/lui-reached exe strings too long for their slot: best fit into `free` (file-offset ranges: slot tails,
    the old slots of the moved strings, EXE_FREE), identical strings shared; their u32 pointers and lui+addiu pairs
    are re-aimed. Returns errors."""
    errs, at = [], {}
    free = sorted(free, key=lambda r: r[1] - r[0])
    for ln, new in sorted(longs, key=lambda x: -len(x[1])):
        if new not in at:
            k = next((k for k, (a, b) in enumerate(free) if b - a >= len(new) + 1), None)
            if k is None:
                errs.append("%s: %d bytes, no exe free space left" % (ln["id"], len(new)))
                continue
            a, b = free.pop(k)
            buf[a:a + len(new) + 1] = new + b"\0"
            at[new] = EXE_BASE + a
            if b - ((a + len(new) + 4) & ~3) >= 4:
                free = sorted(free + [((a + len(new) + 4) & ~3, b)], key=lambda r: r[1] - r[0])
        ram = at[new]
        for p in ln.get("ptrs", []):
            struct.pack_into("<I", buf, int(p, 16), ram)
        for p in ln.get("lui", []):
            p = int(p, 16)
            lui = struct.unpack_from("<I", buf, p)[0]
            assert lui >> 26 == 0x0F, "lui at 0x%X" % p
            # its low half: the first addiu/load/store on the same register within 16 instructions (tools/re.py)
            q = next(q for q in range(p + 4, p + 68, 4) if (w := struct.unpack_from("<I", buf, q)[0]) >> 21 & 31 ==
                     lui >> 16 & 31 and w >> 26 in (0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B))
            lo = struct.unpack_from("<I", buf, q)[0]
            hi = ram >> 16 if lo >> 26 == 0x0D else (ram + 0x8000) >> 16  # ori is unsigned
            struct.pack_into("<I", buf, p, lui & 0xFFFF0000 | hi)
            struct.pack_into("<I", buf, q, lo & 0xFFFF0000 | ram & 0xFFFF)
    return errs


def in_place(buf, f, off_of, mode, qa, relocate=False):
    """Strings written over their originals up to `max`. With relocate (exe): a pointer/lui string gets only the
    JP string's own 4-aligned slot (the zero bytes `max` counts past it may be zero-init variables) and longer ones
    move (_relocate)."""
    errs, longs, free = [], [], []
    for ln in f["lines"]:
        o = off_of(ln)
        old_end = buf.index(0, o)
        movable = relocate and "region" not in ln and bool(ln.get("ptrs") or ln.get("lui"))
        slot_end = (old_end + 4) & ~3 if movable else o + ln["max"] + 1
        new = _text(ln, mode, qa, budget=slot_end - o - 1)  # marker filler fits the slot
        if new is None:
            continue
        if len(new) >= slot_end - o:
            if movable:
                longs.append((ln, new))
                free.append((o, slot_end))  # unreached once its pointers move
            else:
                errs.append("%s: %d bytes > max %d%s" % (ln["id"], len(new), ln["max"], " (fixed field)" * relocate))
            continue
        buf[o:max(old_end, o + len(new))] = new + bytes(max(old_end - o - len(new), 0))
        if movable and slot_end - ((o + len(new) + 4) & ~3) >= 4:
            free.append(((o + len(new) + 4) & ~3, slot_end))
    if longs:
        errs += _relocate(buf, longs, free + [(EXE_FREE[0] - EXE_BASE, EXE_FREE[1] - EXE_BASE)])
    return errs


def insert(tree, script="script", mode="en", qa=None, only=None):
    """only (bisecting): apply `mode` to script files whose path starts with one of these prefixes; the rest keep
    their original bytes (layout moves still happen)."""
    tree, qa = Path(tree), dict(qa or {})
    files = _load(script)
    for rel, f in files.items():
        if only and not rel.startswith(tuple(only)):
            for ln in f["lines"]:
                qa.setdefault(ln["id"], None)  # None: keep the original bytes
    data = {n: bytearray((tree / n).read_bytes()) for n in ("OVER.BIN", "BAT_OVER.BIN", "SLPS_023.19")}
    orig = {n: bytes(v) for n, v in data.items()}
    errs, blocks = events(data["OVER.BIN"], files, mode, qa)
    e, quotes = battle(data["BAT_OVER.BIN"], data["SLPS_023.19"], files, mode, qa)
    errs += e
    errs += in_place(data["SLPS_023.19"], files["exe.json"], lambda ln: int(ln["id"][4:], 16), mode, qa, relocate=True)
    errs += in_place(data["OVER.BIN"], files["overlay.json"], lambda ln: int(ln["id"][3:], 16), mode, qa)
    if errs:
        raise Overflow("\n".join(errs))
    relayout(data["OVER.BIN"], data["SLPS_023.19"], blocks, (tree / "T_TIM.BIN").read_bytes())
    battle_relayout(data["BAT_OVER.BIN"], data["SLPS_023.19"], quotes)
    unknown = set(qa) - {ln["id"] for f in files.values() for ln in f["lines"]}
    if unknown:
        raise SystemExit("--qa ids not in script/: %s" % sorted(unknown))
    changed = {}
    for n, v in data.items():
        changed[n] = sum(x != y for x, y in zip(v, orig[n]))
        (tree / n).write_bytes(v)
    return changed
