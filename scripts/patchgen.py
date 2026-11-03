"""Patch-table generator mechanism. A port's scripts/build_patch_table.py
builds Gen(dat, iface_text, shim_map_text, reloc, tramp_text), calls the
entry kinds below once per row, and writes emit(prefix) to
build/patch_table.h.

Adapted from ../cleopatra/scripts/build_patch_table.py. Two differences from
Cleopatra's generator, both spec pins (task-9-brief.md):

  1. Addressing is a raw `.dat` OFFSET, not a boot.bin RAM address. Patch
     sites span BOTH images (main load entry at .dat 0x0, test load
     entry at .dat TEST_DAT_OFF -- docs/kb/game.md §Parsed .dat header), and
     the old-byte verification source is the .dat itself, not boot.bin
     (Phase 4 flag 7: boot.bin only covers the main image). Every dat_offset
     therefore has the SAME mod-4 parity as the real RAM address
     it patches, because both GAME_LOAD_ADDR and TEST_DAT_OFF are 4-aligned
     (shim_iface.h) -- the hook()/detour() SH-4 PC-relative math (which only
     cares about parity, never the absolute value) carries over unchanged.
  2. Each entry carries an `img` tag (0 = main, 1 = test), inferred from
     dat_offset alone (img_of() below) -- never hand-classified, so a
     mis-tagged image is structurally impossible.

Patch kinds (little-endian; `new`/`target` values are symbolic where they
depend on the shim -- computed from shim.map/shim_iface.h so the KB doc and
the rows never drift, same convention as Cleopatra's MIRROR_P2):
  pool(dat_off, expect, value)   u32 config-time literal: assert cur==expect, write value
  ptr (dat_off, expect, target)  u32 fn-pointer slot: assert cur==expect, write target
  hook(dat_off, expect, target)  overwrite a 2-byte-verified fn entry with a
                                  6-byte SH-4 thunk + pooled target (Cleopatra's kind)
  detour(dat_off, expect, target) a self-contained 10-12 B
                                  jmp-detour window (docs/kb/phase4-conversion.md
                                  §maple-patch-sites MAPLE-BOOT-STRATEGY): unlike
                                  hook(), the replaced code is mid-body, not a
                                  function entry, so nothing may call into it --
                                  it must carry its own literal inline.
  carve(dat_off, pristine_hex, new_hex) overlap-aware raw entry, emitted as its
                                  own arrays (see carve()).
"""
import re
import struct
import sys


class Gen:
    def __init__(self, dat, iface_text, shim_map_text, reloc, tramp_text):
        # ---- shim_iface.h: single source of truth for the shim addresses --
        self.iface = iface_text
        self.SHIM_BASE = self._hexdef("SHIM_BASE")
        self.TEST_DAT_OFF = self._hexdef("TEST_DAT_OFF")      # main/test boundary, raw .dat offset
        self.GAME_LOAD_ADDR = self._hexdef("GAME_LOAD_ADDR")  # both images load here (RAM address)
        # Register mirrors (P2/uncached, matching the game's original access mode).
        self.G1_MIRROR_P2 = self._sb_off("G1_MIRROR") | 0xA0000000        # cart/G1 repoints
        self.MAPLE_MIRROR_P2 = self._sb_off("MAPLE_MIRROR") | 0xA0000000  # maple repoints

        # ---- shim entry points from shim.map ----------------------------------
        # Symbols carry a leading _ (__USER_LABEL_PREFIX__=_); look up with or without.
        self.symtab = {}
        for line in shim_map_text.splitlines():
            p = line.split()
            if len(p) == 3:
                self.symtab[p[2]] = int(p[0], 16)

        # ---- the .dat: the old-byte verification source for EVERY entry ------
        # NOT boot.bin (Cleopatra's source): entries span both the main and test
        # load images, and dat_offset is uniformly a raw .dat offset
        # (task-9-brief.md Interfaces block, Phase 4 flag 7).
        self.dat = dat
        self.reloc = reloc            # the port's reloc_patchset.json rows (carve() overlays them)
        self.tramp_text = tramp_text  # the port's mtramp.S (resume_check() reads it)
        self.patches = []   # (dat_off, img, old-bytes, new-bytes, comment)
        self.carves = []    # separate list: emitted as its own arrays, applied by the
                            # loader ONLY when backend == syscall, AFTER the main table
        self._selftest()

    def _hexdef(self, name):
        m = re.search(rf"#define\s+{name}\s+(0x[0-9a-fA-F]+)", self.iface)
        if not m:
            sys.exit(f"{name} not in shim_iface.h as a plain #define hex literal")
        return int(m.group(1), 16)

    def _sb_off(self, name):     # "#define NAME (SHIM_BASE + 0xNNNN)" -> abs address
        m = re.search(rf"#define\s+{name}\s+\(SHIM_BASE\s*\+\s*(0x[0-9a-fA-F]+)\)", self.iface)
        if not m:
            sys.exit(f"{name} not in shim_iface.h as (SHIM_BASE + 0xNNNN)")
        return self.SHIM_BASE + int(m.group(1), 16)

    def sym(self, name):
        v = self.symtab.get(name)
        if v is None:
            v = self.symtab.get("_" + name)     # C name -> asm label _name
        if v is None:
            sys.exit(f"symbol {name!r} not in shim.map (rebuild: make -C shims)")
        return v            # code entries run cached (P1); jmp/jsr targets want P1

    def sym_opt(self, name):
        """Like sym(), but returns None instead of exiting when the symbol is
        absent -- for gd_test_server, which only exists in a TESTSRV=1 shim
        build (shims/src/gd_testsrv.c, `#if GD_TEST_SERVER`). A plain build's
        shim.map legitimately has no such symbol; that must not fail the
        generator, only leave GD_TEST_SERVER_ADDR at a value LOADER_TESTSRV=0
        builds never read."""
        v = self.symtab.get(name)
        return v if v is not None else self.symtab.get("_" + name)

    def img_of(self, dat_off):
        """0 = main image, 1 = test image (docs/kb/phase4-conversion.md
        §Cart-patch-sites Conventions: dat_offset >= TEST_DAT_OFF -> test)."""
        return 1 if dat_off >= self.TEST_DAT_OFF else 0

    def rd(self, dat_off, n):
        assert 0 <= dat_off <= len(self.dat) - n, hex(dat_off)
        return self.dat[dat_off:dat_off + n]

    def _append(self, dat_off, old, new, comment):
        assert len(old) == len(new), (dat_off, len(old), len(new))
        assert len(old) <= 12, f"@dat:{dat_off:#x}: {len(old)} B exceeds the 12 B old/neu capacity"
        self.patches.append((dat_off, self.img_of(dat_off), old, new, comment))

    def pool(self, dat_off, expect, value, comment=""):
        old = self.rd(dat_off, 4)
        got = struct.unpack("<I", old)[0]
        assert got == expect, f"pool @dat:{dat_off:#x}: found {got:#010x}, expected {expect:#010x}"
        self._append(dat_off, old, struct.pack("<I", value), comment)

    def ptr(self, dat_off, expect, target, comment=""):
        old = self.rd(dat_off, 4)
        got = struct.unpack("<I", old)[0]
        assert got == expect, f"ptr @dat:{dat_off:#x}: found {got:#010x}, expected {expect:#010x}"
        self._append(dat_off, old, struct.pack("<I", target), comment)

    def hook(self, dat_off, expect, target, comment=""):
        """SH-4 entry thunk (Cleopatra's kind, math unchanged -- see module
        docstring point 1): mov.l @(disp,PC),r0 ; jmp @r0 ; nop ; [pad] ; .long target.
        `expect` = the first opcode (u16) at dat_off (entry-point guard)."""
        old0 = struct.unpack("<H", self.rd(dat_off, 2))[0]
        assert old0 == expect, f"hook @dat:{dat_off:#x}: found {old0:#06x}, expected {expect:#06x}"
        slot = (dat_off + 6 + 3) & ~3            # 4-align the pooled .long
        pad = slot - (dat_off + 6)
        disp = (slot - ((dat_off & ~3) + 4)) // 4
        assert 0 <= disp <= 255, hex(dat_off)
        code = struct.pack("<HHH", 0xD000 | disp, 0x402B, 0x0009)
        code += struct.pack("<H", 0x0009) * (pad // 2) + struct.pack("<I", target)
        self._append(dat_off, self.rd(dat_off, len(code)), code, comment)

    @staticmethod
    def detour_code(w, target):
        """jmp-detour kind (no Cleopatra analog -- MAPLE-BOOT-STRATEGY needs a
        self-contained mid-body detour, not an entry hook). Layout
        (docs/kb/phase4-conversion.md §maple-patch-sites):

            +0x00  d201   mov.l @(0x01,PC),r2   ; r2 = the trampoline address
            +0x02  422b   jmp @r2
            +0x04  0009   nop                    ; delay slot
            +0x06  0009   [pad -- only if w%4==0, to 4-align the literal]
            +0x06/8  <32-bit trampoline address>

        `w` = window-start dat_offset. SH-4 `mov.l @(1,PC),r2` at address A reads
        EA = ((A+4)&~3)+4 (PC-relative load; PC = insn addr + 4). Substituting
        A=w gives the literal's offset from w; both w%4 cases (0 and 2 -- SH-4
        code is only ever 2-aligned) are exercised by the port's
        scripts/test_build_patch_table.py. Returns the code bytes (10 or 12 B);
        the caller is responsible for old-byte verification.
        """
        lit_off = 8 if w % 4 == 0 else 6
        total = lit_off + 4
        # The KB's own math, re-derived and asserted per entry (not just trusted
        # from the table) -- this is the literal-lands-inside-the-window guarantee.
        assert lit_off == (((w + 4) & ~3) + 4) - w, (hex(w), lit_off)
        assert lit_off + 4 <= total <= 12, (hex(w), lit_off, total)
        code = struct.pack("<HHH", 0xD201, 0x422B, 0x0009)
        if lit_off == 8:
            code += struct.pack("<H", 0x0009)
        code += struct.pack("<I", target & 0xFFFFFFFF)
        assert len(code) == total
        return code

    def detour(self, dat_off, expect, target, comment=""):
        code = self.detour_code(dat_off, target)
        old = self.rd(dat_off, len(code))
        assert old == expect, (
            f"detour @dat:{dat_off:#x}: found {old.hex()}, expected {expect.hex()}")
        self._append(dat_off, old, code, comment)

    def _selftest(self):
        # Money path: the old-byte verify is worthless unless a wrong expectation
        # raises. dat_off 0x0 is the .dat's own header (never 0xdeadbeef in any
        # real image), so this needs no reloc/KB value and can run before any
        # definitions are loaded.
        n = len(self.patches)
        try:
            self.pool(0x0, 0xDEADBEEF, 0, "selftest (deliberately wrong expect)")
        except AssertionError:
            assert len(self.patches) == n, "selftest polluted the patch list"
            return
        sys.exit("SELFTEST FAILED: bad expectation did not raise")

    def carve(self, dat_off, pristine_hex, new_hex, comment=""):
        """Overlap-aware raw entry. Verifies `pristine_hex` against the
        pristine DAT (same money path as pool()), then derives the emitted
        `old` by overlaying every reloc word from reloc_patchset.json that
        intersects the window -- because the loader applies the unconditional
        table first, the runtime memcmp sees post-reloc bytes."""
        pristine = bytes.fromhex(pristine_hex)
        new = bytes.fromhex(new_hex)
        got = self.rd(dat_off, len(pristine))
        assert got == pristine, (
            f"carve @dat:{dat_off:#x}: found {got.hex()}, expected {pristine_hex}")
        assert len(pristine) == len(new) <= 12
        old = bytearray(pristine)
        for r in self.reloc:                  # single source: the json, already
            ro = int(r["dat_offset"], 16)     # pristine-asserted by pool() in the rows
            w = struct.pack("<I", int(r["new"], 16))
            for i in range(4):
                j = ro + i - dat_off
                if 0 <= j < len(old):
                    old[j] = w[i]
        self.carves.append((dat_off, self.img_of(dat_off), bytes(old), new, comment))

    def resume_check(self, site, image, dat_off, nbytes):
        """The trampoline's baked resume address MUST be window_ram + window_len:
        control returns to the first instruction the detour did not swallow. Both
        numbers exist twice (the port's rows and mtramp.S), so assert them equal
        rather than trusting two hand-typed tables."""
        ram = self.GAME_LOAD_ADDR + dat_off - (self.TEST_DAT_OFF if image == "test" else 0)
        m = re.search(rf"MBSITE\s+{site}_{image},\s*(0x[0-9a-fA-F]+)", self.tramp_text)
        if not m:
            sys.exit(f"mtramp.S has no MBSITE {site}_{image}")
        got = int(m.group(1), 16)
        if got != ram + nbytes:
            sys.exit(f"MAPLE-BOOT-{site.upper()} {image}: mtramp.S resumes at "
                     f"{got:#010x}, window {ram:#010x}+{nbytes} ends at "
                     f"{ram + nbytes:#010x}")

    def emit(self, prefix):
        """The full build/patch_table.h text; arrays are <prefix>_patches_main,
        <prefix>_patches_test, <prefix>_carve_main, <prefix>_carve_test."""
        main_patches = [p for p in self.patches if p[1] == 0]
        test_patches = [p for p in self.patches if p[1] == 1]
        main_carves = [p for p in self.carves if p[1] == 0]
        test_carves = [p for p in self.carves if p[1] == 1]

        # FIX ROUND 2 (task-6-report.md): gd_test_server's own runtime address, the
        # same "resolve from shim.map" path every hook()/detour() target already
        # uses (shim.ld links at SHIM_BASE, so shim.map addresses ARE final runtime
        # addresses -- no extra math). Only present in a TESTSRV=1 shim build
        # (shims/src/gd_testsrv.c, `#if GD_TEST_SERVER`); sym_opt() (not sym())
        # because a plain build's shim.map legitimately lacks it, and that must not
        # fail generation -- the loader only ever reads this under its own
        # LOADER_TESTSRV=1 (loader/main.c), which the top Makefile always sets in
        # lockstep with the shim's GD_TEST_SERVER=1.
        gd_test_server_addr = self.sym_opt("gd_test_server") or 0

        # T9 task 6: the baked EEPROM image's runtime address -- the loader pokes the
        # menu's session record into the STAGED copy's game area before handoff
        # (loader/main.c MENUEE block). ADAPTED from the task brief, which names a
        # standalone `eeprom_img` symbol: no such symbol exists in this shim (that
        # name belongs to the still-#if-0'd Cleopatra-style RAM-copy skeleton in
        # shims/src/main.c, dead code carried over from the import). The LIVE EEPROM
        # path (same file, case 0x03/0x0b, docs/kb/phase4-conversion.md "EEPROM -- a
        # RAM copy, session-only") serves sub-0x03 out of a RAM copy of `mie_sub03`
        # -- the generated MIE reply blob (shims/build/mie_blobs.c, sub03()
        # in scripts/gen_mie_blobs.py): a 4-byte MIE reply header followed by the
        # 128-byte EEPROM image. EEPROM_IMG_ADDR therefore resolves to mie_sub03's
        # address; loader/main.c's poke offset folds in the extra +4 header skip so
        # the game-area offset (+0x24 in image coordinates) still lands correctly.
        # sym(), not sym_opt(): mie_sub03 is unconditionally compiled (no #if guard).
        eeprom_img_addr = self.sym("mie_sub03")

        out = [
            "/* GENERATED by scripts/build_patch_table.py - do not edit, do not commit",
            " * (embeds original .dat bytes read at generation time). */",
            "typedef struct {",
            "  unsigned int dat_off;",
            "  unsigned char img;      /* 0 = main image, 1 = test image */",
            "  unsigned char len;",
            "  unsigned char old[12];",
            "  unsigned char neu[12];",
            "  const char *what;",
            "} patch_t;",
            f"#define GD_TEST_SERVER_ADDR 0x{gd_test_server_addr:08x}u",
            f"#define EEPROM_IMG_ADDR 0x{eeprom_img_addr:08x}u",
            _emit_array(f"{prefix}_patches_main", main_patches, "N_PATCHES_MAIN"),
            _emit_array(f"{prefix}_patches_test", test_patches, "N_PATCHES_TEST"),
            _emit_array(f"{prefix}_carve_main", main_carves, "N_CARVE_MAIN"),
            _emit_array(f"{prefix}_carve_test", test_carves, "N_CARVE_TEST"),
        ]
        return "\n".join(out) + "\n"


# ---- emit -------------------------------------------------------------
def _row(dat_off, img, old, new, what):
    old_b = list(old) + [0] * (12 - len(old))
    new_b = list(new) + [0] * (12 - len(new))
    old_s = ",".join(f"0x{b:02x}" for b in old_b)
    new_s = ",".join(f"0x{b:02x}" for b in new_b)
    what_s = what.replace("\\", "\\\\").replace('"', '\\"')
    return (f'  {{0x{dat_off:08x}u, {img}u, {len(old)}u, '
            f'{{{old_s}}}, {{{new_s}}}, "{what_s}"}}')


def _emit_array(arr_name, plist, count_name):
    if plist:
        rows = ",\n".join(_row(*p) for p in plist)
        body = f"static const patch_t {arr_name}[] = {{\n{rows}\n}};"
    else:
        body = f"static const patch_t {arr_name}[1] = {{{{0}}}};"
    return body + f"\nenum {{ {count_name} = {len(plist)} }};"
