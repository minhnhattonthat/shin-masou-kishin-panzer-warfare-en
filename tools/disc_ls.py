"""List root-directory files of a raw MODE2/2352 PS1 image: name, LBA, size. Usage: disc_ls.py IMAGE.bin"""
import struct
import sys


def sector(f, lba):
    f.seek(lba * 2352 + 24)
    return f.read(2048)


def listing(path):
    with open(path, "rb") as f:
        pvd = sector(f, 16)
        root_lba, root_size = struct.unpack_from("<I", pvd, 156 + 2)[0], struct.unpack_from("<I", pvd, 156 + 10)[0]
        out = []
        for s in range((root_size + 2047) // 2048):
            d, i = sector(f, root_lba + s), 0
            while i < 2048 and d[i]:
                ln = d[i]
                lba, size, flags, nl = struct.unpack_from("<I", d, i + 2)[0], struct.unpack_from("<I", d, i + 10)[0], d[i + 25], d[i + 32]
                name = d[i + 33:i + 33 + nl].decode("ascii", "replace")
                if name not in ("\x00", "\x01"):
                    out.append((name, lba, size))
                i += ln
        return out


if __name__ == "__main__":
    for name, lba, size in listing(sys.argv[1]):
        print(f"{name:16s} LBA {lba:6d} (0x{lba:05X})  size {size:10d} (0x{size:X})")
