"""Run warp.lua for every scene in tools/debug/scenes.tsv (or the names given) from a cold boot and check each.

    python -X utf8 tools/debug/warp_all.py [NAME..] [--rom CUE] [--out work/qa/warp] [--jobs 3] [--states]

Each scene runs in OUT/<name> with a fresh blank memory card; it passes when log.txt has "SCENE <name> reached".
A map run's MILESTONE lines (event, card, map, with shots m_*.png) also prove that stage's evNN and cardNN, so
those are skipped when their mapNN passes in the same call (named explicitly, they run on their own).
--states saves work/states/<name>.sstate at the end of each run (regenerate after engine/font/graphics edits).
--resume keeps runs that already passed in OUT (same build only); a failed run is retried --retry times.
Writes OUT/summary.tsv (name, result, frame, shot, card index) and exits 1 if any scene failed."""
import argparse
import concurrent.futures as cf
import csv
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

ORIG = os.path.join(ROOT, "rom", "Shin Masou Kishin - Panzer Warfare (Japan).cue")
GRA5 = os.path.join(ROOT, "work", "disc", "tree", "GRA5.BIN")
CARD0, CARD_STEP, CARDS = 0x1860000, 0x8800, 37  # docs/re/graphics.md G8


def blank_card():
    """A formatted, empty 128 KB PS1 memory card (header, 15 free directory frames, 20 unused link frames)."""
    def frame(head):
        f = bytearray(128)
        f[:len(head)] = head
        x = 0
        for b in f[:127]:
            x ^= b
        f[127] = x
        return bytes(f)
    d = frame(b"MC") + frame(b"\xa0" + bytes(7) + b"\xff\xff") * 15 + frame(b"\xff" * 4 + bytes(4) + b"\xff\xff") * 20
    d += bytes(128 * 27) + frame(b"MC")
    d += bytes(0x20000 - len(d))
    assert len(d) == 0x20000 and d[127] == 0x0E and d[128 + 127] == 0xA0
    return d


def scenes():
    with open(os.path.join(ROOT, "tools", "debug", "scenes.tsv"), encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    assert all(len(r) == 7 and None not in r.values() for r in rows), "scenes.tsv: every row needs 7 columns"
    return rows


def busiest(paths):
    """The shot with the most detail (an event's text scene rather than its dark logo transition)."""
    from PIL import Image, ImageStat
    have = [p for p in paths if os.path.exists(p)]
    return max(have, key=lambda p: ImageStat.Stat(Image.open(p).convert("L")).stddev[0]) if have else paths[0]


def card_index(sig):
    if not os.path.exists(GRA5):
        return ""
    with open(GRA5, "rb") as g:
        for k in range(CARDS):
            g.seek(CARD0 + k * CARD_STEP + 0x1D80)  # the first 64-byte run that differs in all 37 cards
            if g.read(64).hex() == sig:
                return str(k)
    return "?"


def run(row, a, card):
    out = os.path.join(a.out, row["name"])
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), a.rom, "--out", out,
           "--script", os.path.join(ROOT, "tools", "debug", "warp.lua"), "--var", f"SCENE='{row['name']}'",
           "--frames", row["frames"], "--sav", card, "--timeout", "1500"]
    if row["how"].startswith("card:"):  # warp.lua copies card K from GRA5: take it from the disc under test
        built = os.path.join(ROOT, "build", "disc", "tree", "GRA5.BIN")
        under_build = os.path.abspath(a.rom).startswith(os.path.join(ROOT, "build") + os.sep)
        cmd += ["--var", "GRA5='%s'" % (built if under_build else GRA5).replace("\\", "/")]
    if a.states:
        cmd += ["--state-out", os.path.join(ROOT, "work", "states", row["name"] + ".sstate")]
    if a.cover:
        cmd += ["--script", os.path.join(ROOT, "tools", "lua", "textcover.lua"), "--debugger"]
    def read_log():
        p = os.path.join(out, "log.txt")
        return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""
    log, rc = read_log(), 0
    if not (a.resume and re.search(r"SCENE \S+ reached", log)):
        with open(os.path.join(a.out, row["name"] + ".emu.txt"), "w", encoding="utf-8") as lf:
            rc = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, cwd=ROOT).returncode
        log = read_log()
    m = re.search(r"SCENE \S+ reached frame (\d+)", log)
    ms = {k: int(f) for k, f in re.findall(r"MILESTONE (\w+) stage \d+ frame (\d+)", log)}
    sig = re.search(r"CARDSIG ([0-9a-f]{128})", log)
    return {"name": row["name"], "ok": bool(m) and rc == 0, "frame": m.group(1) if m else "", "rc": rc,
            "ms": ms, "card": card_index(sig.group(1)) if sig else "", "out": out}


def show(r, tag=""):
    print(f"{tag}{'ok  ' if r['ok'] else 'FAIL'} {r['name']:18s} frame {r['frame']:6s} rc {r['rc']} "
          f"{' '.join(sorted(r['ms']))} {('card ' + r['card']) if r['card'] else ''}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--rom", default=ORIG)
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "warp"))
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--cover", action="store_true", help="also log drawn strings (tools/lua/textcover.lua)")
    ap.add_argument("--retry", type=int, default=2, help="re-runs of a failed scene (default 2)")
    ap.add_argument("--resume", action="store_true", help="keep OUT/<name> runs that already reached their scene")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    card = os.path.join(a.out, "blank.mcd")
    with open(card, "wb") as f:
        f.write(blank_card())
    rows = scenes()
    if a.names:
        unknown = set(a.names) - {r["name"] for r in rows}
        if unknown:
            sys.exit("unknown scenes: " + " ".join(sorted(unknown)))
        rows = [r for r in rows if r["name"] in a.names]
    maps = {r["stage"] for r in rows if r["how"] == "map"}
    first = [r for r in rows if not (r["how"] in ("event", "card") and r["stage"] in maps and not a.names)]
    res = {}
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for r in ex.map(lambda row: run(row, a, card), first):
            res[r["name"]] = r
            show(r)
    for row in first:  # PCSX-Redux sometimes exits 1 mid-run with 3 instances up: retry those alone
        for _ in range(a.retry):
            if res[row["name"]]["ok"]:
                break
            res[row["name"]] = r = run(row, a, card)
            show(r, "retry ")
    for row in rows:  # event / card scenes proven by their stage's map run
        if row["name"] in res:
            continue
        mp = res.get("map%02d" % int(row["stage"]))
        kind = row["how"]
        ok = bool(mp and kind in mp["ms"] and os.path.exists(os.path.join(mp["out"], f"m_{kind}.png")))
        res[row["name"]] = {"name": row["name"], "ok": ok, "frame": str(mp["ms"].get(kind, "")) if mp else "",
                            "rc": "", "ms": {}, "card": mp["card"] if mp and kind == "card" else "",
                            "out": mp["out"] if mp else ""}
    with open(os.path.join(a.out, "summary.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["name", "result", "frame", "shot", "card"])
        for row in rows:
            r = res[row["name"]]
            shot = os.path.join(r["out"], "scene.png" if r["rc"] != "" else f"m_{row['how']}.png")
            if row["how"] == "event" and r["rc"] == "":
                shot = busiest([os.path.join(r["out"], f"m_event{s}.png") for s in ("_900", "", "_2100")])
            w.writerow([r["name"], "ok" if r["ok"] else "FAIL", r["frame"], os.path.relpath(shot, ROOT), r["card"]])
    bad = [n for n, r in res.items() if not r["ok"]]
    print(f"{len(res) - len(bad)}/{len(res)} scenes reached" + (": FAILED " + " ".join(bad) if bad else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
