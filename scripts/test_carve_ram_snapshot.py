#!/usr/bin/env python3
"""Self-check for carve_ram_snapshot.py -- synthetic savestate, exact bytes.

Builds a fake RAM image with the four control-test landmarks planted at
their real offsets, wraps it in a real RZip container (1 MB chunks, one
zero-length chunk in the middle, junk before the magic), and asserts the
round trip: inflate finds and reproduces the stream, carve rejects a
decoy banner and returns exactly the planted RAM. A second container
exercises the legacy 32-bit size field path.
"""
import struct
import zlib

import carve_ram_snapshot as c

# the four RAM landmarks (port_def values in real use; one port's, as test data)
BANNER_OFF, GDFS_OFF, HEAP_LO, HEAP_HI = 0x15C980, 0x15B2C4, 0x85B00, 0x85BB4
LANDMARKS = (BANNER_OFF, GDFS_OFF, HEAP_LO, HEAP_HI)

# fake .dat prefix: non-trivial deterministic bytes covering both compared spans
dat = bytes((i * 7 + (i >> 8)) & 0xFF for i in range(HEAP_HI - c.BOOT_BASE))

ram = bytearray(c.RAM_SIZE)
ram[BANNER_OFF:BANNER_OFF + len(c.BANNER)] = c.BANNER
ram[GDFS_OFF:GDFS_OFF + len(c.GDFS)] = c.GDFS
ram[c.BOOT_BASE:c.BOOT_BASE + 0x1000] = dat[:0x1000]
ram[HEAP_LO:HEAP_HI] = dat[HEAP_LO - c.BOOT_BASE:HEAP_HI - c.BOOT_BASE]

# decoy banner in the prefix: base >= 0 but its window fails the control tests
prefix = bytearray(0x160000)
prefix[0x15D000:0x15D000 + len(c.BANNER)] = c.BANNER
stream = bytes(prefix) + bytes(ram) + b"trailing-serializer-state"


def rzip(stream, size_field):
    """Pack stream as an RZip container; size_field: '<Q' or legacy '<I'."""
    blob = bytearray(b"junk-before-magic")
    blob += c.MAGIC
    blob += struct.pack("<I", 1 << 20)              # maxChunkSize = 1 MB
    blob += struct.pack(size_field, len(stream))
    half = len(stream) // 2
    for lo, hi in ((0, half), (half, len(stream))):
        for at in range(lo, hi, 1 << 20):
            z = zlib.compress(stream[at:min(at + (1 << 20), hi)])
            blob += struct.pack("<I", len(z)) + z
        if lo == 0:
            blob += struct.pack("<I", 0)            # empty chunk, must skip
    return bytes(blob)


for size_field in ("<Q", "<I"):
    inflated = c.inflate_rzip(rzip(stream, size_field))
    assert inflated == stream, f"inflate round trip failed ({size_field})"
    assert c.carve(inflated, dat, *LANDMARKS) == bytes(ram), f"carve failed ({size_field})"

print("ok")
