"""Game text codec: Shift-JIS (cp932) plus the renderer's single-byte control letters (docs/re/font.md).

decode(bytes) -> str: SJIS characters as themselves, 0x0A as "\\n", 0x20 as " ", the control letters b h m r w z as {b} {h} ...,
any other byte as [XX] (also an SJIS pair that cp932 would re-encode differently), so encode(decode(b)) == b.
The string terminator (NUL) is not part of the text.

    from sjis import decode, encode; assert encode(decode(raw)) == raw
"""
import re

CTRL = "bhmrwz"  # 0x62 0x68 0x6D 0x72 0x77 0x7A: h…z wraps a highlighted span, b prefixes some menu strings
TOKEN = re.compile(r"\{([%s])\}|\[([0-9A-F]{2})\]|(.)" % CTRL, re.S)


def is_lead(c):
    return 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC


def decode(b):
    out, i = [], 0
    while i < len(b):
        c = b[i]
        if is_lead(c) and i + 1 < len(b):
            try:
                ch = b[i:i + 2].decode("cp932")
                if ch.encode("cp932") == b[i:i + 2]:
                    out.append(ch)
                    i += 2
                    continue
            except UnicodeDecodeError:
                pass
        if c in (0x0A, 0x20):
            out.append(chr(c))
        elif chr(c) in CTRL:
            out.append("{%s}" % chr(c))
        else:
            out.append("[%02X]" % c)
        i += 1
    return "".join(out)


def encode(s):
    out = bytearray()
    for m in TOKEN.finditer(s):
        if m[1]:
            out.append(ord(m[1]))
        elif m[2]:
            out.append(int(m[2], 16))
        elif m[3] == "\n":
            out.append(0x0A)
        else:
            out += m[3].encode("cp932")  # raises on characters the font can't hold
    return bytes(out)


if __name__ == "__main__":
    for raw in (b"h\x82\x50z\x95\xaa", b"b\x81\x40\x82\x78\n", b"\x01\x87\x90\xed\x40"):
        assert encode(decode(raw)) == raw, (raw, decode(raw))
    print(decode(b"h\x82\x50z\x95\xaa"), "ok")
