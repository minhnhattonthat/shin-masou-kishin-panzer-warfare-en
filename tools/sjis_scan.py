"""Recon: list Shift-JIS runs (with at least one kana) in a file. Usage: sjis_scan.py FILE [--min N] [--limit N]
Prints offset, byte length and the decoded run; a summary line per file goes to stderr."""
import argparse
import sys


def is_lead(b):
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF


def runs(data, minchars=3):
    i, n = 0, len(data)
    while i < n - 1:
        j, chars = i, []
        while j < n - 1 and is_lead(data[j]) and 0x40 <= data[j + 1] <= 0xFC and data[j + 1] != 0x7F:
            try:
                chars.append(data[j:j + 2].decode("cp932"))
            except UnicodeDecodeError:
                break
            j += 2
        if len(chars) >= minchars and any("぀" <= c <= "ヿ" for c in chars):
            yield i, j - i, "".join(chars)
            i = j
        else:
            i += 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    data = open(a.file, "rb").read()
    count = total = 0
    for off, ln, s in runs(data, a.min):
        count += 1
        total += ln
        if not a.limit or count <= a.limit:
            print(f"{off:08X} {ln:5d} {s}")
    print(f"{a.file}: {count} runs, {total} bytes", file=sys.stderr)
