# naomi-dc-port-kit

The game-agnostic core of the Naomi -> Dreamcast static-binary-conversion ports:
shims, loader, mastering, capture and test tooling, extracted from the
senkosp2dreamcast port so further ports can share it.

A port consumes the kit as a git submodule at `kit/`. The port's Makefiles
include the kit's `shims/rules.mk` and `loader/rules.mk`; kit scripts run from
the port root and read per-game values from the port's `scripts/port_def.py`,
`scripts/menu_def.py` and `scripts/maple_allowlist.py`. The kit never names a
game.

Citations: unqualified citations in kit sources (`docs/kb/...`,
`task-N-brief.md`, phase documents, `loader/main.c`, `shims/src/main.c`) refer
to the reference port's tree, `../senkosp2dreamcast` at commit `afab584`, the
base the kit was extracted from.

Tool pins and install steps: `docs/kb/tooling.md`. Status: `docs/kb/00-status.md`.

## Contract: what a port supplies

Everything below is the port's, not the kit's. The worked example for every
item is `../senkosp2dreamcast` (github.com/CaptainKoffski/senkosp2dreamcast),
the first consumer; paths are relative to the port root.

### 1. `shims/include/shim_iface.h` — the address map

The kit's whole interface to a game: shim home and region offsets,
kernel-slice and BIOS-blob placements, game load address, entry, image
offsets and lengths, `CART_FAD`, `CART_SIZE`, `BLOB_FAD`, prefetch-ring
addresses, loader FAD and sector count, warm-boot addresses, diagnostic
knobs. Example: senkosp `shims/include/shim_iface.h`.

The kit's C and assembler files (`shims/src/*.c`, `shims/src/*.S`,
`loader/*.c`, `loader/*.S`, `loader/*.h`) use exactly these names from it
(`grep -hoE '\b[A-Z][A-Z0-9_]{2,}\b'` over those files, `comm -12` with the
`#define` names in senkosp's header):

`CART_FAD`, `CART_SIZE`, `GAME_LOAD_ADDR`, `GD_STACK_BOTTOM`, `GD_STACK_CANARY`, `GD_STACK_TOP`, `KERNEL_DST`, `KERNEL_TOTAL_LEN`, `MAPLE_RX`, `MAPLE_TX`, `P2ADDR`, `PF_HEAP_BASE_NEW`, `PF_HEAP_BASE_WORD`, `PF_RING_BASE`, `PF_RING_SZ`, `SHIM_BASE`, `SHIM_BOUNCE`, `SHIM_ERR`, `SHIM_GD_DIAG`, `SHIM_PF_VERIFY`, `SHIM_PREFETCH`, `SHIM_STATE`, `SHIM_STATE_GD_BACKEND`, `SHIM_STATE_LAYOUT_VALID`, `SHIM_STATE_LAYOUT_WORD`, `STAGING_ADDR`.

The kit host tests that run with the port's header (`shims/test/test_shim_iface.c`,
`shims/test/test_gd_math.c`, run by `shims/rules.mk` `shim-tests`) also need
`BIOS60000_DST`, `BIOS60000_LEN`, `BIOS_DATA_60000_OFF`,
`BIOS_DATA_KERNEL_A_OFF`, `BIOS_DATA_KERNEL_B_OFF`, `BIOS_DATA_KERNEL_C_OFF`,
`BIOS_DATA_TOTAL`, `G1_MIRROR`, `KERNEL_A_LEN`, `KERNEL_B_LEN`,
`KERNEL_C_LEN`, `MAPLE_MIRROR`, `MAPLE_MIRROR_LEN`, `SHIM_CODE_MAX`,
`SHIM_END`. `kit/scripts/make_gdi.py` and `make_cdi.py` read `CART_FAD`,
`CART_SIZE`, `LOADER_FAD` and `LOADER_SECS` from the header text and
cross-check them.

### 2. Shim game files and `shims/Makefile`

- `shims/src/main.c` (hooks keyed to the game's addresses), `cart.c` (the
  hooked cart sites), `util.c`, `mtramp.S` (detour trampolines with the
  game's resume addresses), and the generated `shims/src/layouts.h`
  (written by `kit/scripts/gen_menu_assets.py`; `kit/shims/src/jvs.c`
  includes it). The build generates `shims/build/mie_blobs.c`
  (`kit/scripts/gen_mie_blobs.py`, never committed).
- `shims/Makefile` (senkosp's, in order): `KIT ?= $(abspath ../kit)`,
  `DAT ?= <the .dat>`, `INC = -Iinclude -Isrc`, the ordered `SRCS` (the
  order is the binary: `kit/shims/shim.ld` concatenates `.text*` in input
  order), then `include $(KIT)/shims/rules.mk`, then the header
  prerequisites. senkosp's `SRCS` (kit entries marked `[kit]`):

  ```make
  SRCS = src/main.c $(KIT)/shims/src/scif.c src/util.c $(KIT)/shims/src/gd.c $(KIT)/shims/src/gd_sys.c \
         $(KIT)/shims/src/gd_testsrv.c src/cart.c $(KIT)/shims/src/maple.c $(KIT)/shims/src/jvs.c \
         src/mtramp.S $(KIT)/shims/src/gdstack.S $(B)/mie_blobs.c $(KIT)/loader/handoff.S
  #      main.c, util.c, cart.c, mtramp.S = port; scif.c, gd.c, gd_sys.c, gd_testsrv.c,
  #      maple.c, jvs.c, gdstack.S, handoff.S = [kit]; mie_blobs.c = generated
  include $(KIT)/shims/rules.mk
  $(B)/shim.elf: include/shim_iface.h src/layouts.h
  $(B)/mie_blobs.c: ../scripts/menu_def.py ../scripts/port_def.py include/shim_iface.h
  ```

  Then the port's own `test:` target (prerequisite `shim-tests`, the kit's
  rule): `test/test_host.c` (`#include "jvs.c"`, built with
  `cc -DHOST_TEST -Iinclude -I$(KIT)/shims/src -Isrc`),
  `test/test_ctl_lib.c` (with `$(KIT)/loader/ctl_lib.c`,
  `-I$(KIT)/loader -I../loader`) and `test/test_game_values.c` (the port's
  value asserts, split out of the kit's host tests). Example: senkosp
  `shims/Makefile`, `shims/test/`.

### 3. Loader game files and `loader/Makefile`

- `loader/main.c` (staging layout and flow), the generated
  `loader/menu_layout.h`, the committed generated art (`menu_sheet.pal8`,
  `menu_sheet.png`, `controls_pad.png`, `controls_stick.png`, and the
  sources of the controls pages, `pad_diagram.png/.svg`,
  `stick_diagram.png/.svg`), and the gitignored `loader/splash.png` and
  `loader/logo_strip.pal8`.
- `loader/Makefile` (senkosp's): `KIT ?= $(abspath ../kit)`, `DAT`, the
  ordered `OBJS`, `BIOS`, the `CFLAGS` additions, then
  `include $(KIT)/loader/rules.mk`, then the header prerequisites of
  `main.o` and the port's inputs of the patch-table generator:

  ```make
  OBJS = main.o handoff.o gd.o gd_sys.o shim_blob.o bios_data.o splash_blob.o naomi_crc.o \
         menu.o ctl_lib.o menu_sheet_blob.o ctl_pad_blob.o ctl_stick_blob.o logo_blob.o
  CFLAGS += -I. -I../shims/include -I../build -I$(KIT)/loader
  CFLAGS += $(DEFS)
  BIOS = ../bios/naomi/epr-21576h.ic27
  include $(KIT)/loader/rules.mk
  main.o: $(KIT)/loader/menu.h $(KIT)/loader/ctl_lib.h menu_layout.h ../build/patch_table.h ../shims/include/shim_iface.h
  ../build/patch_table.h: ../scripts/reloc_patchset.json
  ../build/patch_table.h: ../scripts/port_def.py
  ```

  `loader/rules.mk` builds every object in that list except `main.o`
  (KOS's pattern rule) and refuses to link unless
  `git -C $(KOS_BASE) rev-parse HEAD` starts with `KOS_PIN` (default
  `705c8629`, `docs/kb/tooling.md` §Pins).

### 4. Top-level `Makefile`

senkosp's, the parts every port carries:

```make
KIT := $(abspath kit)
PORT_DEF = PORT_ROOT=$(CURDIR) python3 kit/scripts/kitpath.py port_def
DAT := $(shell $(PORT_DEF) DAT)
GAMEDIR := $(shell $(PORT_DEF) GAME_NAME)
CDI_FILE := $(shell $(PORT_DEF) CDI_FILE)
export KIT DAT
export PORT_ROOT := $(CURDIR)
CD_CART_FAD = 15372
ifeq ($(CDI),1)
DEFS += -DCART_FAD=$(CD_CART_FAD)
endif
export DEFS
gdi: loader
	python3 $(KIT)/scripts/make_gdi.py $(GDI_FLAGS)
cdi:
	$(MAKE) objclean
	$(MAKE) loader CDI=1
	python3 $(KIT)/scripts/make_cdi.py $(GDI_FLAGS)
	$(MAKE) objclean
release: cdi disc
	python3 $(KIT)/scripts/make_preset.py
	# ... zips, see senkosp Makefile
test:
	$(MAKE) -C shims test
	python3 scripts/test_build_patch_table.py
	python3 $(KIT)/scripts/test_maple_literals.py
	$(MAKE) -C kit test
	python3 kit/scripts/test_gen_mie_blobs.py
	python3 scripts/test_gen_menu_nav.py
	python3 kit/scripts/test_gen_menu_sheet.py
test-vmu:
	$(KIT)/scripts/test_vmu_untouched.sh attract
test-vmu-play:
	$(KIT)/scripts/test_vmu_untouched.sh play
deploy: cdi gdi
	CARD="$(CARD)" NOEJECT="$(NOEJECT)" python3 $(KIT)/scripts/gdemu_deploy.py "$(GAMEDIR)" build/disc.gdi build/cdi/disc.cdi
```

`CD_CART_FAD = 15372` is the same in every port: it is the kit's CD layout
(150 + 11702 + 1792 + 1728), and `kit/scripts/make_cdi.py` cross-checks it
against the loader binary and the header's `#elif CART_FAD == 15372` arm.
`DEFS` carries the port's debug knobs (senkosp: `SERIAL=1`, `CRC=1`, ...,
documented at the top of its Makefile).

### 5. Per-game Python modules and data (`scripts/`)

Kit scripts load these with `kit/scripts/kitpath.py` (`port_module`,
`port_value`); a missing name is an error, never a default.

`scripts/port_def.py` (senkosp's, with comments):

| Name | Read by |
|---|---|
| `GAME_NAME` | top Makefile `GAMEDIR` (release zips, `make deploy` card folder); `make_preset.py` (release folder name) |
| `DAT` | top Makefile (exported to the shim/loader rules); `make_gdi.py`/`make_cdi.py` `--rom` default; `gen_mie_blobs.py` `--dat` default; `carve_ram_snapshot.py` (savestate name); `test_maple_literals.py`; `test_gen_mie_blobs.py`; the port's `build_patch_table.py` |
| `CART_SIZE` | `make_gdi.py` (asserts `len(DAT)`, cross-checks `shim_iface.h`) |
| `IP_PRODUCT`, `IP_VERSION`, `IP_DATE`, `IP_COMPANY` | `make_gdi.py` IP.BIN branding (0x40, 0x4a, 0x50, 0x70); `make_cdi.py` (mkdcdisc IP) |
| `IP_TITLE` | IP.BIN 0x80 (`make_gdi.py`, `make_cdi.py`); `make_preset.py` (preset title, README heading) |
| `CDI_FILE` | top Makefile (CDI release zip); `make_cdi.py` (burn README) |
| `ISO_VOLUME` | `make_cdi.py` (`mkisofs -V`) |
| `TEXPATCH` | `make_gdi.py`/`make_cdi.py`: `True` splices `build/texpatch/` into the cart image |
| `PATCH_PREFIX` | the port's `build_patch_table.py` → `Gen.emit(prefix)`: array names in `build/patch_table.h` |
| `GHIDRA_PROJECT` | `scripts/ghidra/run.sh` (unless `$GHIDRA_PROJECT` is set) |
| `ENTRY_PC` | `capture_leg.sh` → `FLYCAST_ENTRYPC` (unless exported); hex without `0x` |
| `STREAM_FLOOR` | `test_maple_literals.py` (end of the cart boot region) |
| `RAM_BANNER_OFF`, `RAM_GDFS_OFF`, `RAM_HEAP_LO`, `RAM_HEAP_HI` | `carve_ram_snapshot.py` control tests |
| `MIE_ORACLE_LOG` (optional) | `test_gen_mie_blobs.py` oracle capture (absent: SKIP) |

- `scripts/menu_def.py` — the menu definition: `gen_menu_assets.py` reads
  `TOP_ITEMS`, `TOP_FOOTER`, `SET_FOOTER`, `SETTINGS`, `DEFAULT_RECORD`,
  `SHEET_W`, `SHEET_H`, `PAD_BUTTONS`, `STICK_BUTTONS`, `PAD_LAYOUTS`,
  `STICK_LAYOUTS`, `FUNC_JVS`, `FUNC_WORDS`, `CTL_CLASSES`, `CTL_PORTS`,
  `CTL_ROW_ITEMS`, `CTL_FOOTERS`, `CTL_N_CUSTOM`, `CTL_CUSTOM_NAMES`,
  `CTL_DELETE_CELL`, `CUSTOM_DEMO` (and the page layout values it names);
  `gen_mie_blobs.py` reads `DEFAULT_RECORD` and `SYSTEM_COIN_SETTING`.
  Rerun `python3 kit/scripts/gen_menu_assets.py` after any edit and commit
  its outputs. Example: senkosp `scripts/menu_def.py`.
- `scripts/maple_allowlist.py` — the cart's classified Maple-register
  literals: `CART_MAPLE_PATCHED`, `CART_TRAP_TABLE`, `CART_STREAMED_NOISE`
  (`kit/scripts/test_maple_literals.py`).
- `scripts/reloc_patchset.json` — the relocation words (single source; read
  by the port's `build_patch_table.py` through `patchgen.Gen(reloc=...)`).
- `scripts/build_patch_table.py` — the game's patch rows on
  `kit/scripts/patchgen.py`'s `Gen` (cart rows, Maple rows, boot detours,
  hooks, carves), writing `build/patch_table.h`; plus its test
  (`scripts/test_build_patch_table.py` in senkosp).
- The game's Ghidra scripts in `scripts/ghidra/` (senkosp: `WhichFunc.java`,
  `DumpEntryChain.java`, `FindTexErrXrefs.java`,
  `ScanPlacementConstants.java`); `kit/scripts/ghidra/run.sh` searches the
  kit's and the port's `scripts/ghidra`.

### 6. Kit scripts: run from the port root (or set `PORT_ROOT`)

Required arguments (ROM paths absolute — Flycast rejects a relative one,
`docs/kb/tooling.md` §Instrumented Flycast):

- `kit/scripts/capture_leg.sh <leg> <rom>`
- `kit/scripts/capture_dc_leg.sh <leg> [gdi]` (default `build/disc.gdi`)
- `kit/scripts/capture_naomi_splash.sh <dat>`
- `python3 kit/scripts/extract_mie_blobs.py <log>`
- `python3 kit/scripts/parse_cartlog.py <log> --attract-hw N --boot-end N --carve-end N`
  (`--task-sp-floor` together with `--stack`)
- `python3 kit/scripts/scan_dat_constants.py <dat> --words LO-HI[,LO-HI...]`
- `kit/scripts/ghidra/run.sh script DisasmEntry.java 0x<ENTRY_PC>`

`GHIDRA_PROJECT` and `FLYCAST_ENTRYPC` come from the environment when set,
else from `port_def`. Every Flycast launcher defaults `FLYCAST_HEADLESS=1`
and passes `-config config:pvr.rend=0` (`docs/kb/tooling.md` §Headless
launch rule); `test_vmu_untouched.sh play` is headed on purpose (the tester
plays).

### 7. Gitignored inputs (each port supplies its own)

The `.dat` (`port_def.DAT`); `bios/` (Naomi BIOS, `loader/Makefile`
`BIOS`); the donor archive `[GDI] Dolphin Blue.7z` at the port root (a kit
constant, `scripts/make_gdi.py` `DONOR_7Z`; the B5 donor-clone layout is the
method, `docs/kb/tooling.md` §GDI mastering); `tools/kos` with its
`environ.sh`; `tools/ram-snapshot.bin` (`kit/scripts/carve_ram_snapshot.py`);
`loader/splash.png` (`kit/scripts/capture_naomi_splash.sh`);
`loader/logo_strip.pal8`; `build/texpatch/` when `TEXPATCH` is `True`;
optional `0GDTEX.pvr`/`0GDTEX.png` (disc art) and `iplogo.mr` (TM-screen
logo). For `make cdi` also `tools/img4dc` and `tools/mkdcdisc`
(`docs/kb/tooling.md` §CDI mastering).

### 8. Exceptions and caveats

- Byte-pinned kit files still carry the reference port's name in comments:
  `shims/src/jvs.c`, `loader/handoff.S`, `scripts/cdi-bisect/hello.c`,
  `scripts/ghidra/Decomp.java`, `WhichFuncArgs.java`, `DisasmRange.java:2`;
  and `jvs.c` uses senkosp's `JVS_M`-style button names. Renaming them is a
  later, gated clean-up (spec §11).
- Kit constants proven on senkosp's hardware that a new port must confirm
  on its own hardware round: `scripts/make_preset.py`'s DreamShell `heap`
  and `memory` pins, and `scripts/test_maple_literals.py`'s
  `BIOS_DATA_BASELINE` (the Maple literal in the BIOS slice). A port
  cannot extend that baseline without a kit change.
- The Maple tripwire exits non-zero on any unclassified literal: a new port
  is red until it classifies its cart's literals in `maple_allowlist.py`.

## The gate

A kit change is proven on senkosp: rebuilt against the kit, its
`scripts/gate_hashes.sh check gd` and `check cd` must be silent (sha256 of
`shim.bin`, `shim.map`, `mie_blobs.c`, `patch_table.h`, `1ST_READ.BIN`, the
four tracks and `disc.gdi`, and the `CDI=1` `shim.bin` + `1ST_READ.BIN`,
against senkosp `docs/kb/kit-gate-baseline.txt`), and senkosp's
`make test` and the kit's `make test` green. Result of this extraction
(2026-11-03, senkosp `docs/kb/tooling.md` §Kit extraction gate — result):
every gate hash identical to the `afab584` baseline.
