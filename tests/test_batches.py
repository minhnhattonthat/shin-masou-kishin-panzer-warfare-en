"""Translation batch tool: wrap/limit selftest, and every shipped English line passes the batch rules (glossary too)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402


def test_selftest():
    batches._selftest()


def test_shipped_english_passes():
    assert batches.main(["check"]) == 0
