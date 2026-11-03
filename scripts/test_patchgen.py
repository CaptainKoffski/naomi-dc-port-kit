# run: python3 scripts/test_patchgen.py  (from any cwd)
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patchgen import Gen

IFACE = """#define SHIM_BASE 0x8c010000
#define TEST_DAT_OFF 0x8000
#define GAME_LOAD_ADDR 0x8c020000
#define G1_MIRROR (SHIM_BASE + 0x4800)
#define MAPLE_MIRROR (SHIM_BASE + 0x5000)
"""
MAP = "8c010100 T _shim_x\n8c010200 D _mie_sub03\n"
g = Gen(dat=bytes(range(256)) * 256, iface_text=IFACE, shim_map_text=MAP, reloc=[], tramp_text="")

g.pool(0x10, 0x13121110, 0xCAFEF00D)
assert g.patches == [(0x10, 0, bytes(range(0x10, 0x14)), struct.pack("<I", 0xCAFEF00D), "")], g.patches
try:
    g.pool(0x20, 0xDEADBEEF, 0)
except AssertionError:
    pass
else:
    raise SystemExit("FAIL: wrong expect accepted")
assert len(g.patches) == 1, "refused pool() polluted the list"

h = g.emit("x")
for s in ("x_patches_main", "x_patches_test", "x_carve_main", "x_carve_test", "N_PATCHES_MAIN"):
    assert s in h, s
print("ok")
