import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import cover  # noqa: E402


def test_match():
    cover._selftest()
