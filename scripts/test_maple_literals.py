#!/usr/bin/env python3
"""VMU-safety static tripwire (design: ../cleopatra/docs/superpowers/specs/2026-07-26-vmu-safety-design.md).

A VMU is only reachable via Maple-bus frames; game code reaches the Maple
DMA registers through u32 literals in the block 0x5f6c00-0x5f6cff (any
P0/P1/P2 mirror). This scan checks that set of literals in every executable
byte source on the disc (run from the port root, or set PORT_ROOT):

  - the port's flat cart image (port_def.DAT) + build/bios_data.bin (Naomi
    ROM/BIOS-library bytes): every literal must be classified -- the cart's
    in the port's scripts/maple_allowlist.py (CART_MAPLE_PATCHED,
    CART_TRAP_TABLE, CART_STREAMED_NOISE: one justification per bucket),
    bios_data.bin's in its BIOS_DATA_BASELINE. A NEW or GONE literal
    fails `make test`; classify it (patch or prove dead -- kit/scripts/ghidra
    FindMmioXrefs.java gives xrefs) before touching the allow-list.
  - loader/main.o + handoff.o (the port's loader objects): zero vmu/maple
    references outside LOADER_MAPLE_ALLOW (the KOS libs linked into
    loader.elf legitimately contain both, and are covered by the dynamic
    canary test, kit/scripts/test_vmu_untouched.sh, instead -- so only these
    two objects are scanned).

The shim (shims/src/maple.c) is excluded by design: it is the one authorized
Maple user, TX limited to DEVICE REQUEST + GETCOND to main devices.
"""
import struct, subprocess, sys

import kitpath

port = kitpath.port_root()
_pd = kitpath.port_module("port_def")
CART = port / kitpath.port_value(_pd, "DAT")
BIOS_DATA = port / "build" / "bios_data.bin"
LOADER_OBJS = [port / "loader" / "main.o", port / "loader" / "handoff.o"]

STREAM_FLOOR = kitpath.port_value(_pd, "STREAM_FLOOR")   # end of the cart boot region;
                                                         # past it = streamed asset data
BASE_VA = 0x8C020000       # cart offset 0 loads here (docs/kb/game.md)

_al = kitpath.port_module("maple_allowlist")
CART_BASELINE = (kitpath.port_value(_al, "CART_MAPLE_PATCHED")
                 | kitpath.port_value(_al, "CART_TRAP_TABLE")
                 | kitpath.port_value(_al, "CART_STREAMED_NOISE"))

BIOS_DATA_BASELINE = kitpath.port_value(_al, "BIOS_DATA_BASELINE")   # bios_data.bin's classified hits

# Task 10: spec Decision 1's boot combo (hold A+Start on pad 1 during boot ->
# test image) makes the loader READ pad 1 before the handoff, which is the
# first time loader/main.o legitimately names a maple symbol. Classified, per
# this script's own rule, rather than deleted from the gate:
#
#   maple_wait_scan   blocks until KOS's first periodic scan has landed
#   maple_enum_type   walks the already-scanned device list, no bus traffic
#   maple_dev_status  returns the driver's cached status buffer for a device
#
# All three are pure reads of state KOS's periodic scan already produced --
# none builds or sends a frame, so none can reach a VMU write. (The scan
# itself runs in every loader build regardless: KOS starts it at init, and
# the docstring's "KOS libs legitimately contain both" clause covers it, with
# the dynamic canary test as the real guard.) Every OTHER maple symbol, and
# every vmu_* symbol without exception, still fails the build -- including a
# maple_dev_status reference from anything but an undefined-symbol import.
#
# T14 (phase 7): the A+Start combo is gone, but all three symbols stay
# legitimately referenced -- the T9 menu polls pads via enum_type/dev_status
# (loader/menu.c edge()), and main.c keeps maple_wait_scan so the menu's
# opening polls see an enumerated pad. Allow-list unchanged.
LOADER_MAPLE_ALLOW = {"_maple_wait_scan", "_maple_enum_type", "_maple_dev_status"}


def _combo_read(nm_line):
    """True for an UNDEFINED reference to one of the three allowed
    controller-read entry points (nm format: '<blanks> U <symbol>')."""
    parts = nm_line.split()
    return (len(parts) == 2 and parts[0] == "U"
            and parts[1] in LOADER_MAPLE_ALLOW
            and "vmu" not in parts[1].lower())


def scan(data):
    """Aligned u32 literals with (v & 0x1fffff00) == 0x005f6c00.
    find()-driven: every candidate contains the byte pair 6c 5f at u32
    bytes 1-2 (LE layout lo,6c,5f,hi) -- ~1 s over the 109 MB cart."""
    hits = set()
    pos = data.find(b"\x6c\x5f")
    while pos != -1:
        off = pos - 1
        if off >= 0 and off % 4 == 0 and off + 4 <= len(data):
            v = struct.unpack_from("<I", data, off)[0]
            if (v & 0x1FFFFF00) == 0x005F6C00:
                hits.add((off, v))
        pos = data.find(b"\x6c\x5f", pos + 1)
    return hits

def selftest():
    planted = b"\0" * 4 + struct.pack("<I", 0xA05F6C18) + b"\0" * 8
    assert scan(planted) == {(4, 0xA05F6C18)}, "self-test: planted literal missed"
    assert scan(b"\0" * 16) == set(), "self-test: false hit on zeros"
    assert scan(b"\0" + planted) == set(), "self-test: unaligned literal must not match"

def check(name, got, want):
    """Returns True iff got==want; otherwise prints every GONE/NEW literal."""
    if got == want:
        print(f"OK   {name}: {len(got)} literals match baseline")
        return True
    for off, v in sorted(want - got):
        print(f"FAIL {name}: baseline literal GONE  off 0x{off:07x} = 0x{v:08x}")
    for off, v in sorted(got - want):
        print(f"FAIL {name}: NEW maple literal     off 0x{off:07x} = 0x{v:08x}"
              f"  (VA 0x{BASE_VA + off:08x} if boot code)")
    print("     classify before touching the allow-list (patch or prove dead;"
          " kit/scripts/ghidra FindMmioXrefs.java) -- see the spec")
    return False

def main():
    selftest()
    for p in (CART, BIOS_DATA, *LOADER_OBJS):
        if not p.exists():
            sys.exit(f"missing {p} -- ROM at the port root + a normal 'make disc' first")

    cart_hits = scan(CART.read_bytes())
    cart_ok = check("cart", cart_hits, CART_BASELINE)
    streamed = {h for h in cart_hits if h[0] >= STREAM_FLOOR}
    if streamed:
        for off, v in sorted(streamed):
            print(f"INFO streamed region: maple literal off 0x{off:07x} = 0x{v:08x}")
    else:
        print(f"OK   streamed region (>= 0x{STREAM_FLOOR:x}): zero maple literals")
    bios_ok = check("bios_data.bin", scan(BIOS_DATA.read_bytes()), BIOS_DATA_BASELINE)

    # loader/main.o + handoff.o are the port's own build output, and
    # "zero vmu/maple symbol references" is fully knowable.
    nm = subprocess.run(["nm", *map(str, LOADER_OBJS)],
                        capture_output=True, text=True, check=True)
    bad = [l for l in nm.stdout.splitlines()
           if ("vmu" in l.lower() or "maple" in l.lower())
           and not _combo_read(l)]
    if bad:
        loader_ok = False
        for l in bad:
            print(f"FAIL loader objects reference VMU/Maple: {l}")
    else:
        loader_ok = True
        print("OK   loader main.o/handoff.o: no unclassified vmu/maple references\n     (allowed, boot-combo controller reads only: "
              + ", ".join(sorted(LOADER_MAPLE_ALLOW)) + ")")
    sys.exit(0 if cart_ok and bios_ok and loader_ok else 1)

if __name__ == "__main__":
    main()
