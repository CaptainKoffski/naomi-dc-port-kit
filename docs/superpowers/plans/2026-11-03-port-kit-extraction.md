# Port Kit Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move senkosp2dreamcast's game-agnostic loader, shim, mastering, capture and test files into this repo and rebuild senkosp against it byte-for-byte.

**Architecture:** Whole files move from senkosp (`main` @ `afab584`) into the same directory names here; senkosp consumes them through a git submodule at `kit/`, Makefile rule files the port includes, and Python/shell scripts that take every per-game value from the port. A hash script in senkosp compares the build outputs with a baseline recorded before the first move, after every task, and on a fresh clone at the end.

**Tech Stack:** C/SH-4 assembler (sh-elf-gcc 15.2.0, KallistiOS 705c8629), GNU make, Python 3 (stdlib; Pillow offline only), POSIX sh, git submodules.

**Spec:** `docs/superpowers/specs/2026-11-03-port-kit-extraction-design.md` (this repo). Read it first; §5 (gate), §6 (contract), §7 (inventory) are the authority.

## Global Constraints

- Two repos: this kit (`/Users/captainkoffski/AntigravityProjects/naomi-dc-port-kit`, work on branch `extraction` from `main`) and senkosp (`/Users/captainkoffski/AntigravityProjects/senkosp2dreamcast`, work on branch `kit-extraction` created from `afab5844206abe3c2cf845465892ebc5ecb16aa0`). Never touch senkosp's `feat/vmu-persistence` or `main`.
- Extraction source is `git show afab584:<path>` in senkosp, never the working tree of another branch.
- A C or assembler file that feeds a gate artifact moves with identical content (`git show afab584:<path> | cmp - <kit path>` must be silent). Scripts and tests may change only to take paths and per-game values from the port.
- Shim link order, exactly: `main.c(port) scif.c(kit) util.c(port) gd.c(kit) gd_sys.c(kit) gd_testsrv.c(kit) cart.c(port) maple.c(kit) jvs.c(kit) mtramp.S(port) gdstack.S(kit) build/mie_blobs.c(generated) handoff.S(kit)`. Loader object order, exactly: `main.o handoff.o gd.o gd_sys.o shim_blob.o bios_data.o splash_blob.o naomi_crc.o menu.o ctl_lib.o menu_sheet_blob.o ctl_pad_blob.o ctl_stick_blob.o logo_blob.o`.
- Same compiler flags as senkosp's Makefiles at `afab584`; `-I` additions are allowed, nothing else changes.
- The kit never names a game: no `senkosp`, `Senko`, `T-SRS001M`, `251342848`, `0x0efb3000`, `320150` in any kit file except this spec/plan and docs that cite senkosp as the worked example. Every such value comes from the port (`scripts/port_def.py`, `scripts/menu_def.py`, Makefile variables) with no fallback: a missing value is a clear error naming the value and the file searched.
- No ROM, BIOS, disc, donor, or game-derived bytes in the kit, including test fixtures (`test_maple_literals.py`'s expected pairs become a port file).
- Every kit capture script sets `export FLYCAST_HEADLESS="${FLYCAST_HEADLESS:-1}"` before launching Flycast.
- KOS stays at the port's `tools/kos`; the kit's loader rules refuse to link if `git -C $(KOS_BASE) rev-parse HEAD` does not start with `705c8629`.
- Keep every moved file's header comment and citations intact. Commit after each task in both repos with messages that name the task.
- Gate artifact sets (senkosp paths): `gd` = `shims/build/shim.bin shims/build/shim.map shims/build/mie_blobs.c build/patch_table.h build/1ST_READ.BIN build/track01.iso build/track02.raw build/track03.iso build/track04.iso build/disc.gdi`; `cd` = `shims/build/shim.bin build/1ST_READ.BIN` built with `CDI=1`; `cdi` = `build/cdi/disc.cdi`. All tasks that touch the build verify with `scripts/gate_hashes.sh` from Task 1.
- The spec's Python module for per-game values is realised as two port files: `scripts/menu_def.py` (unchanged, menu and controls) and new `scripts/port_def.py` (identity and mastering values). Plan decision; the spec leaves the mechanism to the builder.
- Rulings: `shims/test/test_host.c`, `shims/test/test_ctl_lib.c` and `scripts/test_gen_menu_nav.py` stay in senkosp whole (every assert in them is a senkosp layout value); the kit gets no standalone JVS/controls test in v1.

## Review Focus

1. A port missing a required value (no `scripts/port_def.py`, or `CART_SIZE` absent) must fail with a message naming the value and the file, never build with senkosp's number. Pinned by Task 2 (`kitpath`) and Task 7 (mastering).
2. A kit script run from a directory that is not a port root must refuse, not write into the kit tree or the wrong repo. Pinned by Task 2 and Task 6.
3. `tools/kos` at a commit other than the pin must stop the loader link with a message naming both hashes. Pinned by Task 4.
4. A capture script launched with `FLYCAST_HEADLESS` unset must still run Flycast headless. Pinned by Task 8.
5. The VMU tripwire with an allow-list that omits a known literal must fail, not pass vacuously. Pinned by Task 8.

---

### Task 1: Baseline, determinism control, and the hash script (senkosp)

**Files:**
- Create: `senkosp2dreamcast/scripts/gate_hashes.sh`
- Create: `senkosp2dreamcast/docs/kb/kit-gate-baseline.txt`
- Modify: `senkosp2dreamcast/docs/kb/tooling.md` (append one section "Kit extraction gate — baseline (2026-11-03)")

**Interfaces:**
- Produces: `scripts/gate_hashes.sh <gd|cd|cdi>` prints `sha256  <path>` lines (sorted by path) for that artifact set and exits 1 if any file is missing. Every later task diffs its output against `docs/kb/kit-gate-baseline.txt` (sections `== gd`, `== cd`, `== cdi`).

- [ ] **Step 1: Branch senkosp**

```bash
cd /Users/captainkoffski/AntigravityProjects/senkosp2dreamcast
git status --porcelain            # must be empty
git checkout -b kit-extraction afab5844206abe3c2cf845465892ebc5ecb16aa0
```

- [ ] **Step 2: Confirm the gitignored inputs are present**

Run: `ls senkosp.dat "[GDI] Dolphin Blue.7z" bios/naomi/epr-21576h.ic27 tools/ram-snapshot.bin loader/splash.png loader/logo_strip.pal8 build/texpatch tools/kos/environ.sh tools/mkdcdisc/build/mkdcdisc tools/img4dc/build/cdi4dc/cdi4dc`
Expected: every path listed, no error. `git -C tools/kos rev-parse --short HEAD` prints `705c8629`.

- [ ] **Step 3: Write `scripts/gate_hashes.sh`**

POSIX sh. Argument `gd`, `cd` or `cdi` selects the list from Global Constraints; `shasum -a 256` each file; print `sha256  path` sorted; missing file → message on stderr, exit 1.

- [ ] **Step 4: First clean build and `make test`**

```bash
make clean && make gdi && make test
scripts/gate_hashes.sh gd > /tmp/gate1-gd.txt
make objclean && make loader CDI=1 && scripts/gate_hashes.sh cd > /tmp/gate1-cd.txt && make objclean
make cdi && scripts/gate_hashes.sh cdi > /tmp/gate1-cdi.txt
```
Expected: `make test` ends green (shim host tests print ok, the seven Python tests exit 0); three hash files written.

- [ ] **Step 5: Second clean build, compare**

Repeat Step 4 into `/tmp/gate2-*.txt`, then `diff /tmp/gate1-gd.txt /tmp/gate2-gd.txt; diff /tmp/gate1-cd.txt /tmp/gate2-cd.txt; diff /tmp/gate1-cdi.txt /tmp/gate2-cdi.txt`.
Expected: `gd` and `cd` identical. `cdi` is expected to differ (mkisofs writes volume dates); confirm with `cmp -l build/cdi/disc.cdi <copy from build 1> | wc -l` being small and inside the first 64 KB. If `gd` or `cd` differ, stop: find the differing artifact's cause (`cmp -l`, then which input changed) and record it in tooling.md before continuing; the gate then compares that artifact at the stable level and the spec gets an addendum.

- [ ] **Step 6: Record the baseline**

Write `docs/kb/kit-gate-baseline.txt` as `== gd` + gate1-gd, `== cd` + gate1-cd, `== cdi` + gate1-cdi (marked `# informational: differs between clean builds, ISO9660 dates` if Step 5 showed that). Append the tooling.md section: date, base commit, toolchain versions as printed by `sh-elf-gcc --version`, `git -C tools/kos rev-parse HEAD`, python3 version, the determinism result, and the rule "the CDI gate is the `cd` pair".

- [ ] **Step 7: Commit**

```bash
git add scripts/gate_hashes.sh docs/kb/kit-gate-baseline.txt docs/kb/tooling.md
git commit -m "kit-extraction: gate hash script, determinism control, baseline hashes"
```

---

### Task 2: Kit skeleton, path helper, submodule wiring

**Files:**
- Create (kit): `LICENSE` (MIT, copy senkosp's text), `.gitignore`, `CLAUDE.md`, `README.md` (stub: what the kit is, how a port consumes it; §6 contract filled in Task 9), `Makefile`, `scripts/kitpath.py`, `scripts/test_kitpath.py`
- Modify (senkosp): `.gitmodules` (new), `kit` submodule, `Makefile` (add `KIT := $(abspath kit)` and `export KIT`)

**Interfaces:**
- Produces `scripts/kitpath.py`:
  - `kit_root() -> pathlib.Path` — parent of `scripts/` resolved from `__file__`.
  - `port_root() -> pathlib.Path` — `$PORT_ROOT` if set, else `Path.cwd()`; raises `SystemExit("kitpath: <dir> is not a port root: scripts/port_def.py not found (run from the port root or set PORT_ROOT)")` when `<root>/scripts/port_def.py` is absent.
  - `port_module(name: str)` — imports `<port_root>/scripts/<name>.py` by path (importlib) and returns it; `SystemExit` naming the missing file.
  - `port_value(module, name: str)` — `getattr` or `SystemExit(f"{module.__file__}: {name} is required")`.
- Produces kit `Makefile` target `test` (list grows per task).
- Produces senkosp `.gitmodules` entry `submodule.kit` with `url = ../naomi-dc-port-kit.git`, path `kit`.

- [ ] **Step 1: Kit branch and skeleton**

```bash
cd /Users/captainkoffski/AntigravityProjects/naomi-dc-port-kit && git checkout -b extraction
```
`.gitignore`: `build/`, `tools/`, `captures/`, `roms/`, `bios/`, `*.dat`, `*.7z`, `*.gdi`, `*.iso`, `*.chd`, `__pycache__/`, `.DS_Store`, `._*`, `.superpowers/`. `CLAUDE.md`: what the repo is, the spec path, the rules (citations, tool installs in `docs/kb/tooling.md`, no copyrighted bytes, `FLYCAST_HEADLESS=1`, the gate), consumers (`../senkosp2dreamcast` worked example, `../ausfache2dreamcast` next).

- [ ] **Step 2: Write the failing test `scripts/test_kitpath.py`**

```python
# run: python3 scripts/test_kitpath.py  (from any cwd)
def test_port_root_refuses_non_port(tmp):      # cwd=tmp, no scripts/port_def.py -> SystemExit mentioning "port_def.py"
def test_port_root_env_override(tmp):          # PORT_ROOT=tmp with scripts/port_def.py -> returns tmp
def test_port_module_and_value(tmp):           # port_def.py with CART_SIZE=7 -> port_value(m,"CART_SIZE")==7; port_value(m,"NOPE") -> SystemExit mentioning "NOPE"
def test_kit_root():                           # kit_root()/"scripts"/"kitpath.py" exists
```
Plain asserts, `tempfile`, prints `ok`.

- [ ] **Step 3: Run it, expect failure** — `python3 scripts/test_kitpath.py` → `ModuleNotFoundError: kitpath`.

- [ ] **Step 4: Implement `scripts/kitpath.py`** per Interfaces.

- [ ] **Step 5: Run it, expect `ok`**; add `python3 scripts/test_kitpath.py` to the kit `Makefile` `test` target; `make test` → ok.

- [ ] **Step 6: Commit kit**

```bash
git add -A && git commit -m "kit skeleton: licence, ignore, CLAUDE.md, README stub, kitpath helper"
```

- [ ] **Step 7: Add the submodule to senkosp**

```bash
cd /Users/captainkoffski/AntigravityProjects/senkosp2dreamcast
git submodule add -b extraction /Users/captainkoffski/AntigravityProjects/naomi-dc-port-kit kit
git config -f .gitmodules submodule.kit.url ../naomi-dc-port-kit.git
git config -f .gitmodules --unset submodule.kit.branch
```
If git refuses the local path, prefix the add with `git -c protocol.file.allow=always`. The committed `.gitmodules` carries the relative URL (resolves to github.com/CaptainKoffski/naomi-dc-port-kit against senkosp's GitHub origin); the local clone's `.git/config` keeps the absolute path so later tasks bump the pointer with `git -C kit fetch origin extraction && git -C kit checkout <sha>` without pushing. Add `KIT := $(abspath kit)`, `DAT := senkosp.dat`, `export KIT DAT` near the top of senkosp's `Makefile`.

- [ ] **Step 8: Verify and commit senkosp**

`cat .gitmodules` shows path `kit`, url `../naomi-dc-port-kit.git`; `ls kit/scripts/kitpath.py` exists; `make gdi && scripts/gate_hashes.sh gd | diff - <(sed -n '/^== gd/,/^== cd/p' docs/kb/kit-gate-baseline.txt | grep sha256)` is empty.
```bash
git add .gitmodules kit Makefile && git commit -m "kit-extraction: add naomi-dc-port-kit submodule at kit/"
```

---

### Task 3: Shim runtime files and shim rules

**Files:**
- Create (kit): `shims/src/{gd.c,gd_sys.c,gd_testsrv.c,gdstack.S,maple.c,jvs.c,scif.c}`, `shims/shim.ld`, `shims/rules.mk`, `shims/test/{test_shim_iface.c,test_gd_math.c}`
- Delete (senkosp): the same seven sources, `shims/shim.ld`, `shims/test/test_shim_iface.c`, `shims/test/test_gd_math.c`
- Create (senkosp): `shims/test/test_game_values.c`
- Modify (senkosp): `shims/Makefile` (becomes variables + include), `shims/test/test_host.c` (include line only)

**Interfaces:**
- Consumes: `KIT` from Task 2.
- Produces `shims/rules.mk` (included from the port's `shims/Makefile`, cwd = `<port>/shims`): variables the port sets before including: `SRCS` (ordered list, kit entries as `$(KIT)/shims/src/<f>`), `INC` (`-I` flags), `DEFS`, `DAT` (path of the cart image relative to the port root), `B` (default `build`). Provides: `CC/NM/OBJCOPY/CFLAGS` exactly as senkosp's `shims/Makefile` at `afab584` plus `$(INC)`; targets `all` (`$(B)/shim.bin $(B)/shim.map`), `$(B)/mie_blobs.c` (runs `cd .. && python3 $(KIT)/scripts/gen_mie_blobs.py --dat $(DAT) --out shims/$(B)` — the script moves in Task 6; until then the rule calls `../scripts/gen_mie_blobs.py`), `shim-tests` (compiles and runs `test_shim_iface.c` and `test_gd_math.c` with `$(INC)`, `-DHOST_TEST`, linking `$(KIT)/shims/src/gd.c` for the math test), `clean`.
- Produces kit `shims/test/test_shim_iface.c` = senkosp's file minus the value asserts for `CART_SIZE`, `CART_FAD`, `KERNEL_DST + KERNEL_TOTAL_LEN == 0x8c003800`, `KERNEL_TOTAL_LEN == 0x3200`, `BIOS_DATA_TOTAL == 0xa200`, `GAME_LOAD_ADDR`, `GAME_ENTRY`, `MAIN_LEN`, `TEST_DAT_OFF == MAIN_LEN`, `TEST_LEN`; those ten asserts become senkosp's `shims/test/test_game_values.c` (same includes, `main` printing `ok`).

- [ ] **Step 1: Move the seven sources, the linker script, the two tests** with `git show afab584:shims/src/gd.c > ../naomi-dc-port-kit/shims/src/gd.c` etc., then `git rm` in senkosp. Verify each: `git show afab584:<path> | cmp - ../naomi-dc-port-kit/<path>` silent (for the two tests, after the split below the cmp is expected to differ only in the removed lines; check with `diff`).

- [ ] **Step 2: Write `shims/rules.mk`** from senkosp's `shims/Makefile` at `afab584`: keep `CC`, `NM`, `OBJCOPY`, `CFLAGS` (append `$(INC)`), the `.DEFAULT_GOAL := all`, `all`, `$(B)/shim.elf`, `shim.bin`, `shim.map`, `mie_blobs.c`, `clean` rules; drop the LZ4 block and the `../senkosp.dat` rule (the port keeps them); add `shim-tests`. `$(B)/shim.elf` depends on `$(SRCS) $(KIT)/shims/shim.ld` and links with `-Wl,-T,$(KIT)/shims/shim.ld`.

- [ ] **Step 3: Rewrite senkosp `shims/Makefile`**

```make
KIT ?= $(abspath ../kit)
DAT ?= senkosp.dat
INC = -Iinclude -Isrc
SRCS = src/main.c $(KIT)/shims/src/scif.c src/util.c $(KIT)/shims/src/gd.c $(KIT)/shims/src/gd_sys.c \
       $(KIT)/shims/src/gd_testsrv.c src/cart.c $(KIT)/shims/src/maple.c $(KIT)/shims/src/jvs.c \
       src/mtramp.S $(KIT)/shims/src/gdstack.S $(B)/mie_blobs.c $(KIT)/loader/handoff.S
include $(KIT)/shims/rules.mk
# senkosp-only: the LZ4 block from afab584, unchanged, below the include
test: shim-tests
	<test_host, test_ctl_lib, test_naomi_crc, test_lz4_lay, test_game_values lines from afab584, paths updated>
```
`handoff.S` is still in senkosp until Task 4: reference `../loader/handoff.S` now and switch to `$(KIT)/loader/handoff.S` in Task 4. `test_host.c` include becomes `#include "jvs.c"` with `-I$(KIT)/shims/src` on its compile line.

- [ ] **Step 4: Build and compare**

```bash
cd /Users/captainkoffski/AntigravityProjects/senkosp2dreamcast && make objclean && make gdi
scripts/gate_hashes.sh gd | diff - <(sed -n '/^== gd/,/^== cd/p' docs/kb/kit-gate-baseline.txt | grep sha256)
make objclean && make loader CDI=1 && scripts/gate_hashes.sh cd | diff - <(sed -n '/^== cd/,/^== cdi/p' docs/kb/kit-gate-baseline.txt | grep sha256); make objclean
make -C shims test
```
Expected: both diffs empty; every test prints ok. A non-empty diff on `shim.bin`: check `shim.map` first (symbol order reveals a link-order slip).

- [ ] **Step 5: Commit both**

Kit: `git add -A && git commit -m "shims: runtime files, linker script, rules.mk, host tests (from senkosp afab584)"`. senkosp: `git -C kit rev-parse HEAD` is what the submodule points at; `git add -A && git commit -m "kit-extraction: shim runtime from kit, link order preserved; test_game_values split out"`.

---

### Task 4: Loader files and loader rules

**Files:**
- Create (kit): `loader/{handoff.S,menu.c,menu.h,ctl_lib.c,ctl_lib.h,naomi_crc.c,naomi_crc.h}`, `loader/rules.mk`, `shims/test/test_naomi_crc.c`
- Delete (senkosp): the same seven loader files and `shims/test/test_naomi_crc.c`
- Modify (senkosp): `loader/Makefile` (variables + include), `shims/Makefile` (handoff path, test paths), `shims/test/test_ctl_lib.c` (include line only)
- Modify (kit): `Makefile` (`test` gains the CRC test)

**Interfaces:**
- Consumes: `KIT`, `rules.mk` conventions from Task 3.
- Produces `loader/rules.mk` (included from the port's `loader/Makefile`, cwd = `<port>/loader`): port sets `OBJS`, `BIOS`, `CFLAGS` additions, `KOS_PIN` (default `705c8629`); rules.mk provides `TARGET = loader.elf`, `include $(KOS_BASE)/Makefile.rules`, the link rule (depends on `kos-pin-check`), explicit object rules for `handoff.o menu.o ctl_lib.o naomi_crc.o` from `$(KIT)/loader/` and `gd.o gd_sys.o` from `$(KIT)/shims/src/` with `-DGD_LOADER_BUILD=1`, the blob rules (`shim_blob.o bios_data.o splash_blob.o menu_sheet_blob.o ctl_pad_blob.o ctl_stick_blob.o logo_blob.o`) and `../build/bios_data.bin`, `../build/splash.bin`, `../build/ctl_pad.bin`, `../build/ctl_stick.bin` exactly as at `afab584` (`bmp2rgb565.py` path becomes `$(KIT)/scripts/bmp2rgb565.py` after Task 6; until then `../scripts/`), `../build/patch_table.h` rule (`cd .. && python3 scripts/build_patch_table.py` — the port's entry point, unchanged), `../build/1ST_READ.BIN`, `clean`, and `kos-pin-check`: fails with `KOS at $(KOS_BASE) is <hash>, kit pins $(KOS_PIN)` unless `git -C $(KOS_BASE) rev-parse HEAD` starts with `$(KOS_PIN)`.

- [ ] **Step 1: Move the files** (`git show afab584:` → kit, `git rm` in senkosp, `cmp` silent for all seven C/asm files and the test).

- [ ] **Step 2: Write `loader/rules.mk`**; rewrite senkosp `loader/Makefile` to: `KIT ?= $(abspath ../kit)`, `OBJS` (order from Global Constraints), `BIOS = ../bios/naomi/epr-21576h.ic27`, `CFLAGS += -I. -I../shims/include -I../build -I$(KIT)/loader $(DEFS)`, the LZ4BENCH conditional from `afab584`, `include $(KIT)/loader/rules.mk`. In `shims/Makefile` switch `handoff.S` to `$(KIT)/loader/handoff.S`; `test_ctl_lib.c` includes `"ctl_lib.h"` with `-I$(KIT)/loader -I../loader`; `test_naomi_crc` moves into the kit `Makefile` `test` (`cc -o build/test_naomi_crc shims/test/test_naomi_crc.c loader/naomi_crc.c && build/test_naomi_crc`).

- [ ] **Step 3: Pin check test (Review Focus 3)**

Run: `make objclean && KOS_PIN=deadbeef make loader` → expected: fails, message contains both `deadbeef` and the real hash. Then `make objclean`.

- [ ] **Step 4: Build and compare** — same four commands as Task 3 Step 4, plus `make test` (senkosp) and `make test` (kit). Expected: diffs empty, all ok.

- [ ] **Step 5: Commit both** (kit: "loader: handoff, menu engine, controls library, EEPROM CRC, rules.mk"; senkosp: "kit-extraction: loader from kit, 1ST_READ.BIN byte-identical").

---

### Task 5: Patch-table generator mechanism, relocation applier

**Files:**
- Create (kit): `scripts/patchgen.py`, `scripts/apply_reloc.py`, `scripts/test_apply_reloc.py`, `scripts/test_patchgen.py`
- Delete (senkosp): `scripts/apply_reloc.py`, `scripts/test_apply_reloc.py`
- Modify (senkosp): `scripts/build_patch_table.py` (rows only, calls the kit), `scripts/test_build_patch_table.py` (import path only if needed)
- Modify (kit): `Makefile` test list

**Interfaces:**
- Produces `scripts/patchgen.py` class `Gen(dat: bytes, iface_text: str, shim_map_text: str, reloc: list[dict], tramp_text: str)` exposing the functions senkosp's rows call, same names and argument order as at `afab584`: `pool`, `ptr`, `hook`, `detour`, `carve`, `sym`, `sym_opt`, `rd`, `img_of`, `resume_check(site, image, dat_off, nbytes)`, and `emit(prefix: str) -> str` returning the header text whose arrays are `<prefix>_patches_main` / `<prefix>_patches_test` and whose every other byte matches `afab584`'s `build/patch_table.h`. The `_hexdef`/`_sb_off` parsing, `_detour_code`, `_selftest`, `_row`, `_emit_array` move in as methods or module functions. Constants read from the header (`SHIM_BASE`, `TEST_DAT_OFF`, `GAME_LOAD_ADDR`, `G1_MIRROR_P2`, `MAPLE_MIRROR_P2`) stay derived from `iface_text`.
- senkosp's `scripts/build_patch_table.py` becomes: imports via `kit/scripts/kitpath.py` (`sys.path.insert(0, "kit/scripts")` relative to port root), reads `port_def.DAT`, builds `Gen(...)`, then the row section from `afab584` lines 229–~700 verbatim with each bare call prefixed by `g.` (or `from` the instance via local names), then writes `build/patch_table.h` from `g.emit(port_def.PATCH_PREFIX)`. `port_def.py` gains `PATCH_PREFIX = "senkosp"` (file created in this task with `DAT = "senkosp.dat"` and `PATCH_PREFIX`; Task 7 adds the rest).

- [ ] **Step 1: Write the failing kit test `scripts/test_patchgen.py`** — synthetic 64 KB image, a 3-line fake `shim_iface.h` text, a 2-symbol fake map, no reloc; assert: `pool()` on a matching word appends one row and refuses (`AssertionError`) on a mismatch; `emit("x")` contains `x_patches_main` and `N_PATCHES_MAIN`. Run → `ModuleNotFoundError`.

- [ ] **Step 2: Implement `patchgen.py`** by moving the mechanism out of `afab584:scripts/build_patch_table.py`; move `apply_reloc.py` + its test unchanged. Kit `make test` gains both tests → ok.

- [ ] **Step 3: Rewrite senkosp `build_patch_table.py`** as above; create `scripts/port_def.py`.

- [ ] **Step 4: Compare the header, then the build**

```bash
make objclean && make loader && shasum -a 256 build/patch_table.h   # equals the baseline line
python3 scripts/test_build_patch_table.py                            # ok
make gdi && scripts/gate_hashes.sh gd | diff - <(...baseline gd...)  # empty
```

- [ ] **Step 5: Commit both.**

---

### Task 6: Generators — menu assets, MIE blobs, EEPROM diff, splash converter

**Files:**
- Create (kit): `scripts/{gen_menu_assets.py,gen_mie_blobs.py,extract_mie_blobs.py,eeprom_game_diff.py,bmp2rgb565.py,test_gen_mie_blobs.py,test_gen_menu_sheet.py,test_eeprom_game_diff.py}`
- Delete (senkosp): the same eight
- Modify (senkosp): `scripts/test_gen_menu_nav.py` (import path), `Makefile` `test` lines, `shims/Makefile`/kit `shims/rules.mk` (`mie_blobs.c` rule now calls the kit script), kit `loader/rules.mk` (`bmp2rgb565.py` path)
- Modify (kit): `Makefile` test list (`test_eeprom_game_diff.py`)

**Interfaces:**
- All four generators resolve `port = kitpath.port_root()` and `menu_def = kitpath.port_module("menu_def")`; `gen_menu_assets.py` writes to `port/loader/...` and `port/shims/src/layouts.h`, reads `port/loader/*_diagram.png` and `port/logo.png`, previews to `port/build/`; `gen_mie_blobs.py` defaults `--dat` to `port_def.DAT` and `--out` to `port/shims/build`, and reads `CART_SIZE` from `port/shims/include/shim_iface.h` as today; `extract_mie_blobs.py` defaults under `port/captures` and `port/build/mie-oracle`.

- [ ] **Step 1: Move the eight files; adapt paths only** (every `REPO = ...__file__...` becomes `port_root()`; `import menu_def` becomes `port_module`).

- [ ] **Step 2: Regenerate and compare**

```bash
cd senkosp2dreamcast && rm -f shims/build/mie_blobs.c && make -C shims build/mie_blobs.c && shasum -a 256 shims/build/mie_blobs.c   # baseline line
tools/pyenv/bin/python3 -c "import PIL; print(PIL.__version__)"      # if 12.3.0: next line; else skip the PNG part and say so in the report
tools/pyenv/bin/python3 kit/scripts/gen_menu_assets.py && git status --porcelain loader shims/src   # empty: pal8, headers, PNGs unchanged
git -C kit status --porcelain                                         # empty: nothing written into the kit (Review Focus 2)
```
If only PNG previews differ under a different Pillow, `git checkout loader/*.png` and record the Pillow version in the task report; `menu_layout.h`, `layouts.h`, `menu_sheet.pal8` must be unchanged regardless.

- [ ] **Step 3: Tests** — senkosp `make test` (its `test` target now runs `python3 kit/scripts/test_gen_mie_blobs.py`, `python3 kit/scripts/test_gen_menu_sheet.py`, `python3 scripts/test_gen_menu_nav.py`); kit `make test`. Expected: ok everywhere, the mie oracle line says PASS or SKIP as at baseline.

- [ ] **Step 4: Full compare** (`gd` and `cd` sets) → empty diffs. **Commit both.**

---

### Task 7: Mastering and deploy scripts, port identity module

**Files:**
- Create (kit): `scripts/{make_gdi.py,make_cdi.py,make_dcload_gdi.py,make_preset.py,gdemu_deploy.py,test_gdemu_deploy.py}`
- Delete (senkosp): `scripts/make_gdi.py`, `make_cdi.py`, `make_dcload_gdi.py`, `make_preset.py`, `gdemu_deploy.py`, `test_gdemu_deploy.py`
- Modify (senkosp): `scripts/port_def.py` (complete), `Makefile` (`gdi`, `cdi`, `release`, `deploy`, `deploy-dcload` call `$(KIT)/scripts/...`)
- Modify (kit): `Makefile` test list (`test_gdemu_deploy.py`)

**Interfaces:**
- `scripts/port_def.py` (senkosp) final content: `GAME_NAME = "Senko no Ronde Special"`, `DAT = "senkosp.dat"`, `CART_SIZE = 251342848`, `IP_PRODUCT = "T-SRS001M"`, `IP_VERSION = "V1.000"`, `IP_DATE = "20260822"`, `IP_COMPANY = "SEGA LC-T-99"`, `IP_TITLE = "SENKO NO RONDE SPECIAL"`, `CDI_FILE = "senkosp.cdi"`, `PATCH_PREFIX = "senkosp"`, `GHIDRA_PROJECT = "senkosp3"`.
- `make_gdi.py`: `IP_*` and `CART_SIZE` from `port_def` via `kitpath.port_value` (no defaults); `--rom` default `port_def.DAT`; donor constants (`DONOR_7Z`, `DONOR_SUB`, `DONOR_FILES`, `BOOT_REGION`, `BOOT_FILE_SIZE`, `BOOT_LBA`, `TRACK4_LBA`, `GD_END_LBA`, `CART_LBA`) stay in the kit with their citations; the second `assert len(rom) == 251342848` line is removed (it duplicates the `CART_SIZE` assert with a literal). `make_cdi.py` and `make_preset.py`: README/preset text built from `IP_TITLE`, `CDI_FILE`, `GAME_NAME`. `make_dcload_gdi.py` imports `make_gdi` from the kit dir as today. `port_def.py` also gets `TEXPATCH = True`: `make_gdi.py`/`make_cdi.py` require `build/texpatch/` when it is true (senkosp's rule today) and skip the splice with a printed note when false, so a port without a texture pass (ausfache) is not forced to invent one; the value is required, no default. `CD_CART_FAD = 15372` stays in senkosp's top Makefile with a comment pointing at `make_cdi.py`'s FAD cross-check; the README contract lists it as a value every port must carry unchanged.

- [ ] **Step 1: Move the six files; adapt as above; complete `port_def.py`.**

- [ ] **Step 2: Missing-value test (Review Focus 1)** — `PORT_ROOT=$(mktemp -d)`, `mkdir -p $PORT_ROOT/scripts && echo 'DAT="x.dat"' > $PORT_ROOT/scripts/port_def.py`, run `python3 kit/scripts/make_gdi.py` from there. Expected: exits non-zero, message names `CART_SIZE` and `port_def.py`. No file written.

- [ ] **Step 3: Rebuild and compare everything**

```bash
make clean && make gdi && scripts/gate_hashes.sh gd | diff - <(...gd...)     # empty
make objclean && make loader CDI=1 && scripts/gate_hashes.sh cd | diff - <(...cd...); make objclean   # empty
make cdi && ls -l build/cdi/disc.cdi build/cdi/README.txt && diff <(git show afab584:scripts/make_cdi.py | sed -n '/^README = """/,/^"""/p') <(... the README text the new script produced ...)
make release && ls build/*.zip
python3 kit/scripts/test_gdemu_deploy.py
```
Expected: diffs empty; README text identical to the `afab584` template with senkosp's values; two zips; deploy test ok. `make deploy` is not run (needs a card); say so in the report.

- [ ] **Step 4: Commit both.**

---

### Task 8: Capture, analysis, tripwires, Ghidra

**Files:**
- Create (kit): `scripts/{capture_leg.sh,capture_dc_leg.sh,capture_rawfb_leg.sh,capture_naomi_splash.sh,capture_serial.sh,test_vmu_untouched.sh,carve_ram_snapshot.py,parse_cartlog.py,parse_shimtime.py,check_stream_crc.py,scan_dat_constants.py,test_maple_literals.py}` + the five matching `test_*.py`, `scripts/cdi-bisect/hello.c`, `scripts/ghidra/{run.sh,CallTree.java,Decomp.java,DisasmEntry.java,DisasmRange.java,ExportToXML.java,FindMmioXrefs.java,FindRefsTo.java,ListPoolWords.java,ScanBiosTargets.java,WhichFuncArgs.java}`
- Delete (senkosp): the same
- Create (senkosp): `scripts/maple_allowlist.py`
- Modify (senkosp): `Makefile` (`test`, `test-vmu`, `test-vmu-play` lines), `scripts/ghidra/run.sh` is gone — the four senkosp Ghidra scripts stay and run through `kit/scripts/ghidra/run.sh`
- Modify (kit): `Makefile` test list (the five Python tests)

**Interfaces:**
- Shell scripts: `port="${PORT_ROOT:-$PWD}"` replaces `repo=$(dirname "$0")/..`; Flycast binary `"${FLYCAST_BIN:-$port/../flycast4naomi2dreamcast/build/Flycast.app/Contents/MacOS/Flycast}"`; `export FLYCAST_HEADLESS="${FLYCAST_HEADLESS:-1}"` before launch; `capture_leg.sh` and `capture_naomi_splash.sh` take the ROM/image path as a required argument (no game default); logs under `$port/captures/`. `ghidra/run.sh`: project name from `GHIDRA_PROJECT` env (required), `GHIDRA_HOME` default `$port/tools/ghidra_12.1.2_PUBLIC`, boot slice `$port/tools/boot.bin`.
- `test_maple_literals.py`: `CART`, `BIOS_DATA`, `LOADER_OBJS` under `port_root()`; `CART` = `port_def.DAT`; the three sets come from `kitpath.port_module("maple_allowlist")` names `CART_MAPLE_PATCHED`, `CART_TRAP_TABLE`, `CART_STREAMED_NOISE` (senkosp's `scripts/maple_allowlist.py` = those three sets moved verbatim with their comments).
- `carve_ram_snapshot.py`: savestate default `~/Library/Application Support/Flycast/data/<stem of port_def.DAT>.state`, out `port/tools/ram-snapshot.bin`, dat `port/port_def.DAT`. `parse_cartlog.py`: `ATTRACT_HW` becomes a `--attract-hw` argument with no default (senkosp's Makefile/KB value 33453344 is passed by the caller); its test passes the value. `scan_dat_constants.py`: the module-level `RANGES` default (senkosp's above-cap corridors) is removed; `--range lo:hi` (repeatable) is required; its test passes explicit ranges.
- Constants audit, part of Step 1: `grep -nE '0x[0-9a-fA-F]{5,}|[0-9]{7,}' <each moved Python/shell file>`; for every hit decide "method constant (same for every Naomi game: Naomi load base `0x8c020000`, MMIO register addresses, Flycast log formats, RZip container magic)" or "game value (would differ for ausfache: boot-region sizes such as `BOOT_END`/`STREAM_FLOOR = 0x100000`, RAM landmark offsets in `carve_ram_snapshot.py`'s control tests, high-water marks)"; game values become arguments or `port_def` names with no default; list every hit and its verdict in the task report for the reviewer.

- [ ] **Step 1: Move and adapt** as above; the Java files and `hello.c` unchanged (`cmp` silent).

- [ ] **Step 2: Headless test (Review Focus 4)** — `FLYCAST_BIN=/tmp/fakefc` where `/tmp/fakefc` is a script `#!/bin/sh\necho "HEADLESS=$FLYCAST_HEADLESS" > /tmp/fakefc.out; sleep 1`; run `env -u FLYCAST_HEADLESS kit/scripts/capture_dc_leg.sh fake-leg build/disc.gdi` from the senkosp root and stop it. Expected: `/tmp/fakefc.out` contains `HEADLESS=1`. Delete `captures/fake-leg*`.

- [ ] **Step 3: Tripwire test (Review Focus 5)** — copy `scripts/maple_allowlist.py` aside, remove one pair from `CART_MAPLE_PATCHED`, run `python3 kit/scripts/test_maple_literals.py`. Expected: non-zero exit naming the unclassified literal. Restore the file; rerun → exit 0.

- [ ] **Step 4: Smoke the capture path** — `make gdi` (if objects are clean) then `timeout 90 kit/scripts/capture_dc_leg.sh kit-smoke build/disc.gdi` or the script's own bounded form; expected: `captures/kit-smoke.log` exists and contains at least one `SHIM` or `GDPIO`/`GDDMA` line; no Flycast window appeared. `python3 kit/scripts/parse_cartlog.py captures/kit-smoke.log --attract-hw 33453344` runs to its summary. Delete the leg's files afterwards (gitignored anyway).

- [ ] **Step 5: Tests and compare** — kit `make test` (now also the five parser/carver/CRC/scan tests), senkosp `make test` (its tripwire line is `python3 $(KIT)/scripts/test_maple_literals.py`); `gd` diff empty. **Commit both.**

---

### Task 9: Gate run, fresh-clone check, documentation, tag, merge

**Files:**
- Modify (kit): `README.md` (§6 contract filled, with the exact `#define` names kit C files take from the port's `shim_iface.h`, found by `grep -ho '\b[A-Z][A-Z0-9_]*\b' shims/src/*.c shims/src/*.S loader/*.c | sort -u` intersected with the names defined in senkosp's header), `docs/kb/tooling.md` (new), `docs/kb/00-status.md` (new, short)
- Modify (senkosp): `README.md` (build steps gain `git submodule update --init`; the file table and script paths updated), `CLAUDE.md` (kit named as build-required), `docs/kb/tooling.md` (append "Kit extraction gate — result")
- Modify (umbrella `../naomi2dreamcast/docs/kb/port-playbook.md`): one paragraph in the Phase 4 section
- Modify (ausfache `../ausfache2dreamcast/docs/kb/00-status.md`, `CLAUDE.md`): kit shipped, tag, path

- [ ] **Step 1: Kit `docs/kb/tooling.md`** — copy these senkosp tooling.md sections verbatim with their citations, then edit only paths and game names: "Instrumented Flycast", "Ghidra — 12.1.2", "sh-elf / KOS toolchain", "GDI mastering (Task 8) — `make gdi`", "Decoupling from ../cleopatra (2026-09-21)" (the KOS recipe part), "CDI mastering — `make cdi`" → "Installs" and "Layout", "dcload-serial + dc-tool-ser", "VMU canary harness", "T9 menu asset generator", "`make deploy` — `gdemu_deploy.py`". Add the headless launch rule and the pin table from spec §8.

- [ ] **Step 2: Full gate on senkosp `kit-extraction`** — `make clean && make gdi && make test`, `gd` diff empty; `cd` pair diff empty; `make cdi` runs; kit `make test` ok. Record all three hash listings and the test outputs in senkosp tooling.md's result section.

- [ ] **Step 3: Push both work branches, then the fresh-clone check from GitHub**

The relative submodule URL only resolves against senkosp's GitHub origin, so both branches go up first (the user authorised pushes for all three repos on 2026-11-03).

```bash
git -C ../naomi-dc-port-kit push -u origin extraction
git push -u origin kit-extraction
d=$(mktemp -d) && git clone -b kit-extraction git@github.com:CaptainKoffski/senkosp2dreamcast.git $d/senkosp && cd $d/senkosp
git submodule update --init          # must clone github.com/CaptainKoffski/naomi-dc-port-kit at the pinned commit
for f in senkosp.dat "[GDI] Dolphin Blue.7z" tools/kos tools/mkdcdisc tools/img4dc tools/ram-snapshot.bin loader/splash.png loader/logo_strip.pal8 build/texpatch; do ln -s /Users/captainkoffski/AntigravityProjects/senkosp2dreamcast/"$f" "$f"; done
mkdir -p bios && ln -s /Users/captainkoffski/AntigravityProjects/senkosp2dreamcast/bios/naomi bios/naomi
make gdi && scripts/gate_hashes.sh gd | diff - <(...baseline gd...)
```
Expected: empty diff. (Symlinked `tools/kos` has an absolute `KOS_BASE` in `environ.sh` pointing at the original checkout; that is the same files, acceptable for this check.)

- [ ] **Step 4: Docs** — kit README §6 contract; kit `docs/kb/00-status.md` (what shipped, gate result, consumers, next: ausfache Phase 2); senkosp README/CLAUDE.md/tooling.md; umbrella playbook paragraph (ports consume `naomi-dc-port-kit` as a submodule; the contract is its README; the gate was byte-identical senkosp); ausfache `00-status.md` and `CLAUDE.md` (kit shipped as `v0.1.0`, Phase 2 may start). Commit each repo.

- [ ] **Step 5: Tag and merge** — kit: merge `extraction` into `main` (fast-forward), `git tag v0.1.0`, push `main` and the tag; senkosp: `git -C kit checkout v0.1.0`, commit "kit-extraction: pin kit v0.1.0", merge `kit-extraction` into `main` (`--no-ff`), push `main`; umbrella and ausfache: commit and push. Report the final hashes, the tag, and the three pushes.
