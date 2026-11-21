"""tools/lint.py: the script passes, and each rule catches its case."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
pytestmark = pytest.mark.skipif(not (ROOT / "work/disc/tree/BAT_TIM.BIN").exists(), reason="disc not unpacked")

import lint  # noqa: E402


def test_script_is_clean():
    errs, _ = lint.lint()
    assert errs == []


def msg(en, jp="　あ\n\n\n", speaker=""):
    return {"id": "ev000_0", "kind": "msg", "speaker": speaker, "jp": jp, "en": en}


@pytest.mark.parametrize("en,rule", [
    ("Hello.", None),
    ("A\nB\nC\nD", "lines > 3"),
    ("W" * 60, "px >"),
    ("あ", "Japanese left"),
    ("{h}Hi", "control codes"),
    ("A long first line here\nok", "stub last line"),
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
