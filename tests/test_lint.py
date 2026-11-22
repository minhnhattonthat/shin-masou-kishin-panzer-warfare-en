"""tools/lint.py: the script passes, and each rule catches its case."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
pytestmark = pytest.mark.skipif(not (ROOT / "work/disc/tree/BAT_TIM.BIN").exists(), reason="disc not unpacked")

import lint  # noqa: E402


def test_script_is_clean():
    errs, _ = lint.lint(final=True)  # final: an untranslated line fails the commit too
    assert errs == []


def test_hud_tables():
    ln = {"id": "exe_0554C", "jp": "バ軍　兵士", "en": "Vartzpheem Soldier", "ptrs": ["0xC5594"]}
    errs = lint.check_line(ln, {})
    assert any("glyphs > 12" in e for e in errs) and any("px > 60" in e for e in errs)
    q = {"id": "bqA_31_098", "jp": "あ", "en": "W" * 40 + "\n" + "W" * 40}
    assert any("quote slots" in e for e in lint.check_line(q, {}))


def msg(en, jp="　あ\n\n\n", speaker=""):
    return {"id": "ev000_0", "kind": "msg", "speaker": speaker, "jp": jp, "en": en}


@pytest.mark.parametrize("en,rule", [
    ("Hello.", None),
    ("A\nB\nC\nD", "lines > 3"),
    ("W" * 60, "px >"),
    ("あ", "Japanese left"),
    ("{h}Hi", "control codes"),
    ("If only I had committed more of our\nforces...", "one-word last line"),
    ("Ardennes Island\nHeadquarters", None),  # a hard break: the word fitted, the translator broke there
])
def test_rules(en, rule):
    errs = lint.check_line(msg(en), {})
    assert any(rule in e for e in errs) if rule else errs == []


def test_boxes():
    q = {"id": "bqA_31_098", "jp": "あ", "en": "A\nB\nC"}
    assert lint.check_line(q, {}) == ["3 lines > 2"]
    c = {"id": "ev000_21F4", "kind": "choice", "speaker": "", "jp": "あ\nい\n", "en": "Yes.\n" + "W" * 30 + "\n"}
    assert any("px > 228" in e for e in lint.check_line(c, {}))


def test_max_bytes():
    assert lint.check_line({"id": "exe_0", "jp": "あ", "en": "abcd", "max": 3}, {}) == ["4 bytes > max 3"]
