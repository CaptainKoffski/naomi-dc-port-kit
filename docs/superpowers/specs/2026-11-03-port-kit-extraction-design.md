# Port kit extraction — design (sub-project 2 of the ausfache charter)

Date: 2026-11-03. Repo: `naomi-dc-port-kit` (github.com/CaptainKoffski/naomi-dc-port-kit, public, MIT).
Charter: `../ausfache2dreamcast/docs/superpowers/specs/2026-11-02-charter-phase1-foundation-design.md` §Decomposition item 2.
Origin: `../cleopatra/docs/superpowers/specs/2026-07-26-experience-reuse-design.md` §3 bucket 3 ("own reusable code … extract into a standalone `naomi-dc-port-kit` repo that port #2 depends on").

## 1. Intent

Three Naomi → Dreamcast static-binary ports now exist or are under way
(Cleopatra Fortune Plus, Senko no Ronde Special, Akatsuki Blitzkampf Ausf.
Achse). Each so far copied the previous one's loader, shims, mastering
scripts and test harnesses and adapted them by hand. A fix in one port never
reaches the others, and every port re-proves the same hardware facts.

The kit is the game-agnostic core of the most recent, complete, hardware-
verified port (senkosp2dreamcast), moved into its own repo so that every port
from now on consumes one implementation. senkosp is the first consumer and
the proof: rebuilt against the kit, it must produce the same bytes it
produces today. ausfache is the second consumer (its Phase 2 waits for this
kit to ship).

## 2. Decisions made in the brainstorm (the user's)

- **New public repo**, not a directory in the umbrella. Created 2026-11-03,
  empty, remote wired.
- **Extraction base = senkosp `main` at `afab5844206abe3c2cf845465892ebc5ecb16aa0`**
  (short `afab584`), extracted now. The in-progress VMU-persistence branch
  (`feat/vmu-persistence`, operator legs pending) is excluded; it rebases
  onto the kit layout after this ships. The charter fixed the base rule; the
  user chose "extract now" over "wait for VMU".
- **The player-facing flow is senkosp's and becomes the kit's default:** the
  disc boots to a pre-game menu with START GAME, SETTINGS, CONTROLS; SETTINGS
  holds the arcade game's own GAME ASSIGNMENTS; CONTROLS shows each port's
  button layout, tweakable, with a default as close to the arcade cabinet as
  the pad allows; START GAME shows a loading screen while the cart image
  streams, then hands over to the game.
- **Restyle is possible per port.** The kit ships the menu engine and the
  generators; each port owns its menu definition (entries, settings rows,
  controls page, layout numbers, fonts, colours, artwork). senkosp's look
  becomes senkosp's definition, not the kit's default.
- **Kit v1 moves whole files only.** Files that mix generic machinery with
  senkosp's reverse-engineered addresses stay in senkosp as that game's
  layer; ausfache writes its own versions using senkosp's as the worked
  example. Splitting those files is deferred until ausfache shows which parts
  really repeat. (Reason: §5 The gate.)

## 3. Goals, non-goals, anti-goals

**Goals**
1. The kit repo holds every file in §7 "Kit". A C or assembler file that
   feeds a gate artifact (§5) is moved with its content unchanged. Scripts
   and test files may change, but only to take paths and per-game values
   from the consuming port.
2. senkosp consumes the kit (§4) and its build outputs are byte-identical to
   the baseline (§5). senkosp's `make test` stays green.
3. The kit has its own `make test`, green, needing no ROM, BIOS, disc or
   donor bytes and no port. It runs the tests that stand alone: the EEPROM
   CRC, the cartlog and shim-timing parsers, the RAM-snapshot carver, the
   relocation applier, the EEPROM diff, the stream CRC checker, the constant
   scanner, the GDEMU deploy script. The host tests that need a port's
   header, generated tables or menu module (`test_shim_iface.c`,
   `test_gd_math.c`, `test_host.c`, `test_ctl_lib.c`, `test_gen_menu_nav.py`,
   `test_gen_menu_sheet.py`, `test_gen_mie_blobs.py`) become kit test rules
   that the port's `make test` runs with the port's files; the kit keeps only
   their invariant asserts (region-map arithmetic, splitter math, pack and
   unpack round trips). Every assert of a senkosp value in those files
   (`CART_SIZE`, `CART_FAD`, the layout words `0x343210`/`0x432130`/`0x421063`,
   the chip navigation table) moves into a senkosp-side test file. No
   synthetic fixture port is built; the first real second port is ausfache.
4. The kit's README states the contract: what a port must supply (§6), with
   senkosp named as the worked example for every item.
5. The kit's `docs/kb/tooling.md` records every tool pin needed to rebuild
   (§8), copied from senkosp's record with its citations.
6. A fresh clone of kit + senkosp (submodule initialised, gitignored inputs
   supplied) builds the same bytes.

**Non-goals (not in this sub-project)**
- Splitting any mixed file (shim `main.c`, `cart.c`, `util.c`, `mtramp.S`,
  loader `main.c`).
- Any behaviour change, feature, or clean-up beyond path/parameter plumbing
  (renaming senkosp's `JVS_M`-style button macros to generic names included;
  later).
- VMU persistence, the texture arena-fit tools, the LZ4 streaming
  experiment.
- ausfache's own game layer (that is ausfache Phase 4).
- Changes to the Flycast fork or the umbrella beyond a pointer in the port
  playbook.

**Anti-goals (a failure even if everything "works")**
- One differing byte in any gate artifact (§5).
- One byte of ROM, BIOS, disc image, donor track, or data derived from game
  bytes anywhere in the kit, including test fixtures and docs. (The MIE reply
  constants in `gen_mie_blobs.py` are emulator output with cited emitters,
  already public in senkosp; they are fine. The fifteenth blob carries the
  ROM's game id and is generated at build time, never committed, as today.)
- Game-derived test data in the kit. `test_maple_literals.py` carries about
  eighty (cart offset, word) pairs read from `senkosp.dat` as its expected
  literal set; the kit keeps the scanner, and the expected set becomes a
  port-owned allow-list file the scanner reads. Same rule for any other
  fixture taken from a game image.
- A kit file that quietly keeps a senkosp value as a default. Any constant
  that would differ for ausfache (cart size, FADs, IP.BIN fields, game name,
  settings rows, button functions, patch rows, prefetch-ring addresses) must
  come from the port, with no fallback. Constants of the method itself (the
  B5 donor-clone layout, the donor's name and boot region, G1/Maple register
  addresses, EEPROM CRC seed) stay in the kit with their citations.
- A kit that cannot be rebuilt by someone who was not there.

## 4. How a port consumes the kit (my calls; reject any)

- **Git submodule at `kit/`** in the port repo, pinned to a kit commit. The
  pin lives in the port's history, so a rebuild next year checks out the same
  kit without a hand-maintained note. The project's sibling-path convention
  (`../naomi2dreamcast`, `../flycast4naomi2dreamcast`) stays for everything
  else.
- **KOS stays at the port's `tools/kos`** (gitignored checkout, commit
  `705c8629`, v2.2.0-932, `environ.sh` as recorded in senkosp's tooling.md).
  Earlier in the brainstorm I said the kit would own the KOS checkout; I am
  reversing that: a second KOS checkout and build is a second source of
  non-determinism inside the gate for no gain. The kit records the pin and
  the toolchain version, and its loader rules refuse to build if
  `git -C $(KOS_BASE) rev-parse HEAD` is not the pin (a few lines).
- **The port keeps its game layer where it is today** (`shims/src/main.c`,
  `loader/main.c`, `scripts/menu_def.py`, …). Nothing in senkosp moves except
  the files that leave for the kit. ausfache lays its game layer out the same
  way.
- **The kit's Makefiles are rule files the port's Makefiles include**, and the
  port passes what is game-specific as variables: the ordered shim source
  list, the loader object list, the include path for `shim_iface.h` and the
  generated headers, `DEFS`, the game name, the `.dat` path. Exact include
  mechanism: builder's choice.
- **Kit scripts run from the port root** (as senkosp's do today), find the
  kit from their own location, and take every per-game value from the port:
  one Python module the port owns (senkosp's grows out of `scripts/menu_def.py`)
  plus the Makefile variables above. The kit never names a game.
- **Every kit capture script defaults `FLYCAST_HEADLESS=1`** (user rule,
  2026-11-02, recorded in ausfache and senkosp CLAUDE.md). senkosp's base
  commit does not set it; the kit versions do. This changes no gate byte.
- **Licence MIT**, as senkosp. Kit `CLAUDE.md` carries the project rules:
  citations on hardware claims (keep every moved file's header citations
  intact), record tool installs, never commit copyrighted bytes, headless
  emulator, the gate.
- **Directory names mirror senkosp's** (`shims/`, `loader/`, `scripts/`,
  `scripts/ghidra/`) so moved files keep their relative references and the
  KB cites stay readable.

## 5. The gate (fixed by the charter; procedure is mine)

Charter wording: *senkosp rebuilt against the kit produces byte-identical
`shim.bin`, `1ST_READ.BIN` and disc tracks, and senkosp's `make test` stays
green.* Same control the 2026-09-21 KOS decoupling used (senkosp
`docs/kb/tooling.md` §Decoupling).

**Why whole files only.** The shim is one link of an ordered source list
(`shims/Makefile` `SRCS`) under `-Os` with a linker script that concatenates
`.text*` in input order (`shims/shim.ld`). Moving a whole file to another
path keeps its object identical and its position in the list unchanged.
Splitting a file into two changes function order in the binary. So the
link order below is a constraint, and the port owns it:

```
shim:   main.c(game) scif.c(kit) util.c(game) gd.c(kit) gd_sys.c(kit)
        gd_testsrv.c(kit) cart.c(game) maple.c(kit) jvs.c(kit) mtramp.S(game)
        gdstack.S(kit) build/mie_blobs.c(generated) loader/handoff.S(kit)
loader: main.o(game) handoff.o(kit) gd.o(kit) gd_sys.o(kit) shim_blob.o
        bios_data.o splash_blob.o naomi_crc.o(kit) menu.o(kit) ctl_lib.o(kit)
        menu_sheet_blob.o ctl_pad_blob.o ctl_stick_blob.o logo_blob.o
```

Same `CFLAGS`, same toolchain, no LTO. The loader's `objcopy -I binary`
blobs get their auto-generated symbol names from the input path; the rules
already rename them with `--redefine-sym`, so the builder updates those
names to the new paths. No file in loader or shims uses `__FILE__`,
`__DATE__`, `__TIME__`, `__LINE__` or `assert` (checked at the base commit).

Python may be split (the patch-table generator's mechanism goes to the kit,
its row tables stay with the port) because its outputs, not its text, feed
the gate: `build/patch_table.h` becomes loader bytes, `shims/build/mie_blobs.c`
becomes shim bytes, `make_gdi.py` writes the tracks.

**Artifacts compared (sha256):** `shims/build/shim.bin`, `build/1ST_READ.BIN`,
`build/track01.iso`, `build/track02.raw`, `build/track03.iso`,
`build/track04.iso`, `build/disc.gdi`, `build/cdi/disc.cdi`. Not the release
zips (they carry timestamps).

**Procedure**
1. *Determinism control first.* On senkosp `main` at `afab584`: `make clean`,
   `make gdi`, `make cdi`, hash; then again from clean; compare. Any artifact
   that differs between two unchanged builds is investigated before any file
   moves (the cause is recorded in senkosp's tooling.md; the gate then
   compares that artifact at whatever level the control shows is stable, and
   this spec gets an addendum saying so).
2. Record the baseline hashes in senkosp `docs/kb/tooling.md`.
3. Build the kit; on a senkosp branch `kit-extraction`, add the submodule,
   delete the moved files, point the Makefiles at the kit, rebuild from
   clean, hash, compare. `make test` in senkosp green; `make test` in the kit
   green.
4. Fresh-clone check: clone kit + senkosp into a scratch directory, init the
   submodule, symlink the gitignored inputs (`senkosp.dat`, `bios/`, donor
   archive, `tools/kos`, `tools/ram-snapshot.bin`, `loader/splash.png`),
   build, compare again.
5. Only then: tag the kit `v0.1.0`, merge `kit-extraction` into senkosp
   `main`, push both, mark the kit shipped in ausfache's
   `docs/kb/00-status.md` (Phase 2 may start).

*Addendum (final review, M8):* `disc.cdi` differs between clean builds in the
mkisofs volume dates and their EDC/ECC (ISO sectors 16–23; 168 bytes in the
Task 1 control, 244 in Task 7's, 192 in the final review's `cmp`), so the CDI
gate is the `cd` pair (`shim.bin` + `1ST_READ.BIN` built with `CDI=1`) and the
`cdi` hash is informational.

## 6. The contract: what a port supplies (the game layer)

The kit's README lists these, each with the senkosp file as the example.
The builder derives the exact set of names the kit's C files need from the
port's header by grepping the kit files, and lists them in the README.

- `shims/include/shim_iface.h` — the address map: shim home and region
  offsets, kernel-slice and BIOS-blob placements, game load address, entry,
  image offsets and lengths, `CART_FAD`, `CART_SIZE`, `BLOB_FAD`, prefetch
  ring addresses, loader FAD/sector count, warm-boot addresses, diagnostic
  knobs. This header is the kit's whole interface to a game.
- Shim game files: `shims/src/main.c` (the hooks keyed to the game's RE'd
  addresses), `cart.c` (the hooked cart sites), `util.c`, `mtramp.S` (the
  detour trampolines with the game's resume addresses), generated
  `layouts.h`, and the build-time generated `mie_blobs.c`.
- Loader game files: `loader/main.c` (staging layout and flow), generated
  `menu_layout.h`, the committed generated art (`menu_sheet.pal8/.png`,
  `controls_pad.png`, `controls_stick.png`, the pad/stick diagrams), the
  gitignored `splash.png`, optional logo/cover art.
- Scripts and data: the menu definition module, `reloc_patchset.json`, the
  patch-table rows (cart rows, maple rows, boot detour sites, hooks), the
  Ghidra scripts with game-specific address lists.
- The top-level Makefile: game name, IP.BIN fields, cart size and FADs,
  `DEFS` knobs, the ordered source/object lists. The donor and its layout
  (`DONOR_7Z`, `DONOR_SUB`, `BOOT_LBA`, `BOOT_REGION`, `BOOT_FILE_SIZE`, and
  `make_cdi.py`'s sectors derived from them) are kit constants: the B5
  donor-clone layout is the hardware-proven method, shared by Cleopatra and
  senkosp. The port supplies only the donor archive file (gitignored) and
  keeps `LOADER_SECS` in its header equal to the kit's boot region, which
  `make_cdi.py` already cross-checks.
- The Maple-literal allow-list for the VMU tripwire, and the port's own
  value-assert tests (Goal 3).
- Gitignored inputs as today: the `.dat`, BIOS, donor archive, RAM snapshot,
  Flycast captures.

## 7. Inventory, judged at senkosp `main` `afab584`

**Kit** (whole files; `+test` = the host test that belongs to it moves too)

- `shims/src/`: `gd.c`, `gd_sys.c`, `gd_testsrv.c`, `gdstack.S`, `maple.c`,
  `jvs.c`, `scif.c`; `shims/shim.ld`; `shims/Makefile` (as rules).
  Note: `gd.c` includes `gd_lz4.inc.c` only under `SHIM_LZ4`; that include
  stays and resolves against the port's tree when the port uses the knob.
- `shims/test/`: `test_gd_math.c`, `test_host.c`, `test_shim_iface.c`
  (checks the port's header against the kit's region-map invariants),
  `test_naomi_crc.c`, `test_ctl_lib.c`.
- `loader/`: `handoff.S`, `menu.c`, `menu.h`, `ctl_lib.c`, `ctl_lib.h`,
  `naomi_crc.c`, `naomi_crc.h`; `loader/Makefile` (as rules).
- `scripts/` mastering and deploy: `make_gdi.py`, `make_cdi.py`,
  `make_dcload_gdi.py`, `make_preset.py`, `gdemu_deploy.py` (+ its test, from
  the repo root).
- `scripts/` generators: `gen_menu_assets.py` (+`test_gen_menu_nav.py`,
  `test_gen_menu_sheet.py`), `gen_mie_blobs.py` (+test), `extract_mie_blobs.py`
  (the generator's dev oracle), `eeprom_game_diff.py` (+test),
  `build_patch_table.py` mechanism only, `apply_reloc.py` (+test),
  `bmp2rgb565.py`.
- `scripts/` capture and analysis: `capture_leg.sh`, `capture_dc_leg.sh`,
  `capture_rawfb_leg.sh`, `capture_naomi_splash.sh`, `capture_serial.sh`,
  `carve_ram_snapshot.py` (+test), `parse_cartlog.py` (+test),
  `parse_shimtime.py` (+test), `check_stream_crc.py` (+test),
  `scan_dat_constants.py` (+test).
- `scripts/` tripwires: `test_maple_literals.py`, `test_vmu_untouched.sh`.
- `scripts/cdi-bisect/hello.c` (boot-chain control payload).
- `scripts/ghidra/`: `run.sh`, `CallTree.java`, `Decomp.java`,
  `DisasmEntry.java`, `DisasmRange.java`, `ExportToXML.java`,
  `FindMmioXrefs.java`, `FindRefsTo.java`, `ListPoolWords.java`,
  `ScanBiosTargets.java`, `WhichFuncArgs.java`.

**Per game** (senkosp keeps; ausfache writes its own)

- `shims/include/shim_iface.h`; `shims/src/main.c`, `cart.c`, `util.c`,
  `mtramp.S`, `layouts.h`.
- `loader/main.c`, `menu_layout.h`, `menu_sheet.pal8`, `menu_sheet.png`,
  `controls_pad.png`, `controls_stick.png`, `pad_diagram.png/.svg`,
  `stick_diagram.png/.svg`.
- `scripts/menu_def.py`, `scripts/reloc_patchset.json`, the row tables now
  inside `build_patch_table.py` (`_CART_ROWS`, `_MAPLE_ROWS`,
  `MAPLE_BOOT_SITES`, the hook/pointer/carve calls) as a port-owned module,
  `scripts/test_build_patch_table.py` (reads the game image),
  `scripts/ghidra/WhichFunc.java`, `DumpEntryChain.java`,
  `FindTexErrXrefs.java`, `ScanPlacementConstants.java`.
- The expected-literal pairs now inside `scripts/test_maple_literals.py`, as
  a port-owned allow-list file; the senkosp value asserts split out of the
  kit host tests (Goal 3), as senkosp-side test files.
- `Makefile` (top level), `README.md`, `CLAUDE.md`, `docs/`.

**senkosp-only** (stays; not kit material until a second game needs it)

- Texture arena-fit: `scripts/pktx_vq.py`, `shrink_vq.py`, `vq_tuner.py`,
  `decode_pvr_vq.py`, `list_pak_textures.py`, `pak_coverage.py`,
  `texerrsave_postmortem.py`.
- LZ4 streaming experiment (knob off by default): `loader/lz4bench.c`,
  `shims/include/lz4_lay.h`, `shims/src/lz4_lay.c`, `lz4_mem.c`,
  `gd_lz4.inc.c`, `shims/test/test_lz4_lay.c`, `tools/lz4pak/`, `tools/t10b/`,
  and the LZ4 block of `shims/Makefile`.
- `CONTROLS_TASK.MD`, `1.png`–`4.png`, `.gitignore`, `LICENSE` (the kit gets
  its own copy).

## 8. Tool pins the kit records (copied with citations from senkosp tooling.md)

sh-elf-gcc 15.2.0 (dc-chain) at `/opt/toolchains/dc/sh-elf`; KallistiOS
`705c8629` (v2.2.0-932); mkdcdisc at commit `2b98b0d` (2026-09-20), built in
the port's `tools/mkdcdisc/build`; KOS `utils/scramble`; mkisofs 3.02a09
(Homebrew cdrtools); 7zz (Homebrew sevenzip); chdman (Homebrew rom-tools);
Homebrew python 3.14.3; Pillow 12.3.0 (offline asset generation only, never a
build dependency); Ghidra 12.1.2; the instrumented Flycast fork
(`../flycast4naomi2dreamcast`, built app at `build/Flycast.app`, headless).
The builder copies the exact entries, versions and install steps rather than
re-deriving them.

## 9. Deliverables

1. The kit repo: §7 "Kit" files, rule Makefiles, `README.md` with §6, `CLAUDE.md`,
   `LICENSE`, `.gitignore` (`tools/`, `build/`, `*.dat`, `roms/`, `bios/`),
   `docs/kb/tooling.md` (§8), this spec, the plan; `make test` green; tag `v0.1.0`.
2. senkosp on the kit: submodule at `kit/`, moved files deleted, Makefiles
   and scripts pointed at the kit, README build steps updated (submodule
   init), tooling.md entry with baseline and post-extraction hashes and the
   fresh-clone result; merged to `main`; pushed.
3. Umbrella playbook (`../naomi2dreamcast/docs/kb/port-playbook.md`): one
   paragraph saying ports from here on consume the kit and where its
   contract lives.
4. ausfache: `docs/kb/00-status.md` and `CLAUDE.md` note the kit shipped and
   its tag; nothing else.

## 10. Left to the builder

- Makefile include mechanism and variable names; how scripts receive the
  port root and the port's Python module; submodule path name (`kit/`
  suggested); kit tag naming after `v0.1.0`.
- Whether `extract_mie_blobs.py` and the gdemu deploy test need any change
  beyond paths.
- Order of the moves (one directory per commit is fine); the plan decides.
- A ROM-free synthetic self-check for the patch-table mechanism, only if it
  is a few lines; otherwise the port-side test covers it.

## 11. Risks

- The loader build may not be deterministic across clean rebuilds for a
  reason unrelated to the kit. The control in §5 step 1 catches it before
  any move; the rule is "control-test when stuck on does it work at all".
- Script path plumbing is where mistakes will hide. Everything on the gate
  path is caught by the hashes; scripts off the gate path (capture, parse,
  Ghidra, deploy) are covered by their moved self-tests plus one cheap smoke
  each where one exists (a 60 s headless leg of senkosp's disc; the cartlog
  parser over an existing log).
- `feat/vmu-persistence` touches `loader/menu.c`, the Makefile and scripts;
  it will need a rebase onto the kit layout. Accepted cost of "extract now".
- senkosp's `JVS_M`-style names and comments inside kit `jvs.c` read as
  senkosp's; harmless for bytes, confusing for the next port. Rename is a
  later, gated clean-up; the README says so.
