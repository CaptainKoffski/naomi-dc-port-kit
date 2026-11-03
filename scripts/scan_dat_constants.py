#!/usr/bin/env python3
"""Scan a flat Naomi image for LE u32 words whose 29-bit physical value lands
in a watched range (the game's above-cap corridors / VRAM). Candidate
generator for Phase 3 target 3 — catches descriptor tables OUTSIDE the boot
slice (streamed data).

Usage: scan_dat_constants.py <image.dat> --words LO-HI[,LO-HI...]
       scan_dat_constants.py <image.dat> --range LO:HI --words LO-HI[,LO-HI...]
Output: DATHIT off=0x<file offset> word=0x<value> range=<label>

`--words` (required) is the explicit inclusive 29-bit-physical list of watched
ranges (label = "lo-hi"; the game's corridors come from its own placement
analysis, e.g. the port's Ghidra ScanPlacementConstants). `--range` limits the
file window (e.g. one load entry of the .dat).
"""
import argparse
import array
import sys

def scan(path, ranges, start=0, end=None):
    """Hits in [start, end) of `path` for `ranges` = [(label, lo, hi), ...]
    (29-bit physical, inclusive); offsets returned are absolute file
    offsets. `start` is rounded down to a 4-byte boundary."""
    start &= ~3
    with open(path, "rb") as f:
        f.seek(start)
        data = f.read(-1 if end is None else max(0, end - start))
    words = array.array("I")
    words.frombytes(data[: len(data) // 4 * 4])
    if sys.byteorder != "little":
        words.byteswap()
    hits = []
    # ponytail: ~62M-word pure-python loop, ~1 min on the 250 MB .dat — fine
    # for a one-shot analysis; vectorize only if it gets re-run in a loop.
    for i, w in enumerate(words):
        p = w & 0x1FFFFFFF
        for label, lo, hi in ranges:
            if lo <= p <= hi:
                hits.append((start + i * 4, w, label))
                break
    return hits


def parse_words(spec):
    """'a05f7000-a05f77ff,a05f6c00-a05f6cff' -> [(label, lo, hi), ...],
    each bound masked to 29-bit physical (so P1/P2/P4 forms all work)."""
    out = []
    for part in spec.split(","):
        lo, _, hi = part.strip().partition("-")
        lo = int(lo, 16) & 0x1FFFFFFF
        hi = (int(hi, 16) & 0x1FFFFFFF) if hi else lo
        out.append((f"{lo:08x}-{hi:08x}", lo, hi))
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--range", dest="window", metavar="LO:HI",
                    help="hex file-offset window, end-exclusive (default: whole file)")
    ap.add_argument("--words", metavar="LO-HI[,LO-HI...]", required=True,
                    help="hex 29-bit-physical ranges to watch (the game's corridors)")
    args = ap.parse_args(argv)
    start, end = 0, None
    if args.window:
        lo, _, hi = args.window.partition(":")
        start, end = int(lo, 16), int(hi, 16) if hi else None
    for off, w, label in scan(args.image, parse_words(args.words), start, end):
        print(f"DATHIT off=0x{off:08x} word=0x{w:08x} range={label}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
