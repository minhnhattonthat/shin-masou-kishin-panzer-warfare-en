"""Stress cases (phase 8, skill emulator-qa.md §Stress saves): max numbers on every map/status/battle screen, by RAM
pokes on Keigo's records from work/states/ev01_map_p1.sstate (make it on the build under test: warp ev01 KEEP=1
--frames 9950 --state-out). Record layout: docs/re/debug.md "Pilot records" / "Unit records".

    python -X utf8 tools/debug/stress.py [CASE..] [--rom build/smk_en.cue]
      -> work/qa/stress/<case>/f*.png and the proof shots work/qa/stress_proof/<case>_<what>.png (gate them with
         qa_gate.py init work/qa/stress_manifest.tsv work/qa/stress_proof --glob "*.png")
cases:
  status   Lv 99, EXP 9999999, stats 0xFF (the game shows 55), SP 255, HP / max HP 65535: unit box, Ability > Pilot,
           Unit, Attacks
  battle   same pokes + every stage-1 enemy HP 65535: weapon list, battle confirm, battle HUD (route of work/play/confirm)
  levelup  Lv 1, EXP 199 (NEXT 200), stats 0xFF: the kill levels up for real (point allocation screen); forcing the
           level-up by sub-mode 24 leaves the unit-box orb over the help line, a real level-up does not"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

PILOT, UNIT = 0x801786C0, 0x801785D0  # Keigo (pilot idx 0) and his unit, stage 1
ENEMIES = [0x80178F30 + k * 0xF0 for k in range(8)]
OPEN = "10 -;4 circle;60 -"
ABILITY = OPEN + ";4 down;12 -" * 4 + ";4 circle;90 -;4 right;60 -;4 right;60 -;4 right;60 -"
ATTACK = ("10 -;6 circle;40 -;6 down;20 -;6 circle;40 -;6 circle;60 -;6 left;20 -;6 left;20 -;6 left;30 -;6 down;30 -;"
          "6 right;30 -;6 circle;60 -;6 down;30 -;6 left;30 -;6 circle;90 -;6 circle;600 -;400 -;1500 -;300 -")


def pokes(level, exp, enemies=False):
    p = {PILOT: level, PILOT + 4: exp & 0xFF, PILOT + 5: exp >> 8 & 0xFF, PILOT + 6: exp >> 16 & 0xFF, PILOT + 0x0E: 0xFF}
    p.update({PILOT + a: 0xFF for a in range(0x15, 0x1B)})  # Melee Aim Ranged Evade ? Luk
    for r in [UNIT] + (ENEMIES if enemies else []):
        p.update({r + o: 0xFF for o in (0x2A, 0x2B, 0xBA, 0xBB)})  # HP, max HP (u16)
    return "POKE={" + ",".join("[0x%08X]=0x%02X" % kv for kv in p.items()) + "}"


CASES = {  # route, frames, poke spec, {proof name: frame}
    "status": (ABILITY, 460, pokes(99, 9999999), {"unitbox": 70, "pilot": 220, "unit": 290, "attacks": 350}),
    "battle": (ATTACK, 2600, pokes(99, 9999999, True), {"weapons": 120, "confirm": 540, "hud": 2550}),
    "levelup": (ATTACK + ";300 -" + ";6 circle;200 -" * 5, 4400, pokes(1, 199), {"points": 3930}),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases", nargs="*", default=list(CASES))
    ap.add_argument("--rom", default=str(ROOT / "build/smk_en.cue"))
    a = ap.parse_args()
    proof = ROOT / "work/qa/stress_proof"
    proof.mkdir(parents=True, exist_ok=True)
    bad = 0
    for c in a.cases:
        route, frames, poke, shots = CASES[c]
        out = ROOT / "work/qa/stress" / c
        shutil.rmtree(out, ignore_errors=True)
        rc = subprocess.call([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/emu.py"), a.rom, "--out", str(out),
                              "--state-in", str(ROOT / "work/states/ev01_map_p1.sstate"), "--route-str", route,
                              "--frames", str(frames), "--shots", ",".join(map(str, shots.values())),
                              "--script", str(ROOT / "tools/lua/poke.lua"), "--var", "AT=8", "--var", poke])
        for name, f in shots.items():
            src = out / f"f{f:06d}.png"
            if rc or not src.exists():
                print(f"{c}: rc {rc}, no {src.name}")
                bad = 1
                continue
            shutil.copy(src, proof / f"{c}_{name}.png")
    sys.exit(bad)


if __name__ == "__main__":
    main()
