# Kit status

**Updated:** 2026-11-03 (v0.1.0 content complete; the tag goes on after the
final review, `extraction` → `main`)

## What shipped

The game-agnostic core of `../senkosp2dreamcast` at `afab584`, moved whole
(spec `docs/superpowers/specs/2026-11-03-port-kit-extraction-design.md` §7):

- `shims/`: `rules.mk` (build rules the port's `shims/Makefile` includes),
  `shim.ld`; `src/` `gd.c`, `gd_sys.c`, `gd_testsrv.c`, `gdstack.S`,
  `maple.c`, `jvs.c`, `scif.c`; `test/` `test_gd_math.c`,
  `test_shim_iface.c`, `test_naomi_crc.c`.
- `loader/`: `rules.mk` (included by the port's `loader/Makefile`; KOS pin
  check), `handoff.S`, `menu.c`/`.h`, `ctl_lib.c`/`.h`, `naomi_crc.c`/`.h`.
- `scripts/`: `kitpath.py` (finds the port, loads its `port_def`/`menu_def`/
  `maple_allowlist`); mastering and deploy (`make_gdi.py`, `make_cdi.py`,
  `make_dcload_gdi.py`, `make_preset.py`, `gdemu_deploy.py`); generators
  (`gen_menu_assets.py`, `gen_mie_blobs.py`, `extract_mie_blobs.py`,
  `eeprom_game_diff.py`, `patchgen.py`, `apply_reloc.py`, `bmp2rgb565.py`);
  capture and analysis (`capture_leg.sh`, `capture_dc_leg.sh`,
  `capture_rawfb_leg.sh`, `capture_naomi_splash.sh`, `capture_serial.sh`,
  `carve_ram_snapshot.py`, `parse_cartlog.py`, `parse_shimtime.py`,
  `check_stream_crc.py`, `scan_dat_constants.py`); tripwires
  (`test_maple_literals.py`, `test_vmu_untouched.sh`); `cdi-bisect/hello.c`;
  `ghidra/` (`run.sh` + ten generic scripts); the self-tests (`test_*.py`).
- `Makefile` (`make test`: the stand-alone tests, no ROM/BIOS/disc needed),
  `README.md` (the contract), `CLAUDE.md`, `LICENSE` (MIT), `.gitignore`,
  `docs/kb/tooling.md` (pins and install steps), the spec and the plan.

## Gate result

Green, 2026-11-03 (senkosp `docs/kb/tooling.md` §Kit extraction gate —
result): senkosp rebuilt against this kit is byte-identical to its `afab584`
baseline. `scripts/gate_hashes.sh check gd` (`shim.bin`, `shim.map`,
`mie_blobs.c`, `patch_table.h`, `1ST_READ.BIN`, four tracks, `disc.gdi`) and
`check cd` (the `CDI=1` `shim.bin` + `1ST_READ.BIN`) are silent; senkosp's
`make test` and this kit's `make test` pass; `make cdi` masters (its hash
varies with the mkisofs volume dates, informational). Fresh clone: senkosp
`kit-extraction` cloned from GitHub, `git submodule update --init` fetched
this kit from github.com/CaptainKoffski/naomi-dc-port-kit at the pin
(`624250e`), gitignored inputs symlinked: `check gd` and `check cd` silent
(senkosp tooling.md §Fresh clone from GitHub).

Final-review fix wave (C1: the `bios_data.bin` rule, its constants, the
blob-structure asserts and `BIOS_DATA_BASELINE` moved to the port; I2–I7,
M8–M14: `B = build`, the `ENTRY_PC` guard, ROM paths absolutized,
`ISOLDR_*` port values, the menu look in the port's `menu_def.py`, docs):
the gate was re-run at the resulting pin; result and pin in senkosp
`docs/kb/tooling.md` §Kit extraction gate — result.

## Consumers

- `../senkosp2dreamcast` — first consumer and worked example: submodule
  `kit/` on branch `kit-extraction` (→ `main` after the final review).
- `../ausfache2dreamcast` — next: its Phase 2 may start on the kit.

## Next

- Tag `v0.1.0` on this content after the final review (`extraction` →
  `main`), pin senkosp to it, merge senkosp `kit-extraction`.
- ausfache Phase 2 (instrumented analysis), then its game layer on the
  contract (`README.md`).
- Deferred clean-ups, each a gated change (senkosp `check gd`/`check cd`
  silent): senkosp's `JVS_M`-style names and comments in `shims/src/jvs.c`
  and the other byte-pinned files (README §8, spec §11); re-pointing the
  kit sources' unqualified senkosp citations (README "Citations").
