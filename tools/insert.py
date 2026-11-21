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
FILLER = "The quick brown fox jumps over the lazy dog. Sphinx of black quartz, judge my vow. "


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


def battle(bat, exe, files, mode, qa):
    errs = []
    for name, base, a, b in batquote.blocks(exe):
        f = files["battle_%s.json" % name]
        lines = {ln["id"]: ln for ln in f["lines"]}
        a_lines = {ln["id"]: ln for ln in files["battle_A.json"]["lines"]}
        blk = bytearray(bat[a * 0x800:b * 0x800])
        _, strings, recs = batquote.parse(bytes(blk), base)
        end = min(recs) if recs else len(blk)
        items = []
        for o, orig in strings:
            ln = lines["bq%s_%02X_%03X" % (name, a, o)]
            src = a_lines[ln["same"]] if ln.get("same") and mode == "en" and ln["id"] not in qa else ln
            new = _text(src, mode, qa)
            ptrs = [r + 4 for r in recs if struct.unpack_from("<I", blk, r + 4)[0] == base + o]
            items.append((o, orig if new is None else new, ptrs, base))
        try:
            _repack(blk, 4, end, items, "battle %s block 0x%X" % (name, a))
        except Overflow as e:
            errs.append(str(e))
            continue
        bat[a * 0x800:b * 0x800] = blk
    return errs


def in_place(buf, f, off_of, mode, qa):
    errs = []
    for ln in f["lines"]:
        new = _text(ln, mode, qa, budget=ln["max"])
        if new is None:
            continue
        o = off_of(ln)
        if len(new) > ln["max"]:
            errs.append("%s: %d bytes > max %d" % (ln["id"], len(new), ln["max"]))
            continue
        old_end = buf.index(0, o)
        buf[o:max(old_end, o + len(new))] = new + bytes(max(old_end - o - len(new), 0))
    return errs


def insert(tree, script="script", mode="en", qa=None, only=None):
    """only: marker mode for script files whose path starts with one of these prefixes (bisecting); en for the rest."""
    tree, qa = Path(tree), dict(qa or {})
    files = _load(script)
    for rel, f in files.items():
        if only and mode == "marker" and not rel.startswith(tuple(only)):
            for ln in f["lines"]:
                qa.setdefault(ln["id"], None)  # None: keep the original bytes
    data = {n: bytearray((tree / n).read_bytes()) for n in ("OVER.BIN", "BAT_OVER.BIN", "SLPS_023.19")}
    orig = {n: bytes(v) for n, v in data.items()}
    errs, blocks = events(data["OVER.BIN"], files, mode, qa)
    errs += battle(data["BAT_OVER.BIN"], orig["SLPS_023.19"], files, mode, qa)
    errs += in_place(data["SLPS_023.19"], files["exe.json"], lambda ln: int(ln["id"][4:], 16), mode, qa)
    errs += in_place(data["OVER.BIN"], files["overlay.json"], lambda ln: int(ln["id"][3:], 16), mode, qa)
    if errs:
        raise Overflow("\n".join(errs))
    relayout(data["OVER.BIN"], data["SLPS_023.19"], blocks, (tree / "T_TIM.BIN").read_bytes())
    unknown = set(qa) - {ln["id"] for f in files.values() for ln in f["lines"]}
    if unknown:
        raise SystemExit("--qa ids not in script/: %s" % sorted(unknown))
    changed = {}
    for n, v in data.items():
        changed[n] = sum(x != y for x, y in zip(v, orig[n]))
        (tree / n).write_bytes(v)
    return changed
