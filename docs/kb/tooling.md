# Tooling

Every tool the kit's rules and scripts need: pins, install steps, usage. The
sections after "Pins" and "Headless launch rule" are copied verbatim from the
reference port's record, `../senkosp2dreamcast/docs/kb/tooling.md`, with
their citations; only paths were edited (kit files now read `kit/...`, run
from the port root; senkosp-only scripts read `../senkosp2dreamcast/scripts/...`)
and the deploy line's game name. They record senkosp's history: "this repo",
"this project" and unqualified KB paths (`docs/kb/...`, `captures/...`,
`task-N-report.md`) in them mean senkosp's tree at `afab584`. Install
locations under `tools/` (`tools/kos`, `tools/mkdcdisc`, `tools/img4dc`,
`tools/ghidra_12.1.2_PUBLIC`, `tools/dcload-serial`) are the consuming port's
gitignored `tools/`.

## Pins

From spec §8 (`docs/superpowers/specs/2026-11-03-port-kit-extraction-design.md`);
versions and steps as senkosp recorded them (citations are senkosp
`docs/kb/tooling.md` lines at `1aac566`, or the section below).

| Tool | Pin | Where | Install, citation |
|---|---|---|---|
| sh-elf-gcc (dc-chain) | 15.2.0 (`sh-elf-gcc --version` → `sh-elf-gcc (GCC) 15.2.0`) | `/opt/toolchains/dc/sh-elf` (machine-wide) | §sh-elf / KOS toolchain below; built with KOS's toolchain builder (senkosp `README.md` §Requirements) |
| KallistiOS | `705c862957b2f6091a6ce4784943744daecc3e2b` (v2.2.0-932) | the port's `tools/kos` (gitignored) + its `environ.sh` | §Decoupling from ../cleopatra below; `loader/rules.mk` `KOS_PIN ?= 705c8629` refuses to link any other commit |
| KOS `utils/scramble` | the KOS pin above | `tools/kos/utils/scramble/scramble` | §CDI mastering → Installs ("already built (arm64) in the KOS checkout"; no build command was recorded) |
| mkdcdisc | `2b98b0d` (`2b98b0d9480e364e3517355648fbc3b49fb19882`, v0.0.4, 2026-09-20) | the port's `tools/mkdcdisc/build/mkdcdisc` | `git clone https://gitlab.com/simulant/mkdcdisc.git tools/mkdcdisc && git -C tools/mkdcdisc checkout 2b98b0d && (cd tools/mkdcdisc && meson setup build && ninja -C build)`; check: `git -C tools/mkdcdisc rev-parse --short HEAD` → `2b98b0d`. Deps Homebrew `meson`, `ninja`, `libisofs`. Build command and deps from senkosp tooling.md:2926-2934, whose own recipe used `git clone --depth 1` (current HEAD, not the pin; it was `2b98b0d` on 2026-09-25). Build-required for `make cdi` (:3059-3060) |
| img4dc / cdi4dc | 0.5b, `d28df15` (2023-04-15) | the port's `tools/img4dc/build/cdi4dc/cdi4dc` | §CDI mastering → Installs |
| mkisofs | 3.02a09 | Homebrew `cdrtools` | §CDI mastering → Installs |
| 7zz | Homebrew `sevenzip` | `/opt/homebrew/bin/7zz` | donor extraction, §GDI mastering below |
| chdman | Homebrew `rom-tools` | PATH | GD-ROM romset → `.dat` only (`../naomi2dreamcast/tools/dat-extract`; senkosp tooling.md:294) |
| python3 | Homebrew python 3.14 (3.14.3 recorded 2026-08, :203; 3.14.7 at the 2026-11-03 gate) | `/opt/homebrew/bin/python3` | stdlib only for every build-time script |
| Pillow | 12.3.0 | `python3 -m pip install --user --break-system-packages pillow` | offline asset generation only (`kit/scripts/gen_menu_assets.py`), never a build dependency; §T9 menu asset generator below |
| Ghidra | 12.1.2 + Homebrew OpenJDK (26.0.1 recorded) | the port's `tools/ghidra_12.1.2_PUBLIC` (or `GHIDRA_HOME`) | §Ghidra below; `kit/scripts/ghidra/run.sh` |
| Instrumented Flycast | the fork `../flycast4naomi2dreamcast` (sibling of the port) | `build/Flycast.app` in the fork checkout | §Instrumented Flycast below (build recipe: senkosp tooling.md §Decoupling, :2593-2613, and the 2026-10-02 rebuild, :3231-3246); always headless (next section) |
| dcload-serial / dc-tool-ser (optional, serial link) | 1.0.7, `e4b29bf` | the port's `tools/dcload-serial` | §dcload-serial below |

## Headless launch rule

- Every kit launcher exports `FLYCAST_HEADLESS="${FLYCAST_HEADLESS:-1}"`
  (`scripts/capture_leg.sh`, `capture_dc_leg.sh`, `capture_naomi_splash.sh`,
  and through `capture_dc_leg.sh` also `capture_rawfb_leg.sh`;
  `test_vmu_untouched.sh attract`). The fork treats any set
  `FLYCAST_HEADLESS` as headless (`../flycast4naomi2dreamcast`
  `core/sdl/sdl.cpp:842`, `getenv != nullptr`).
- Every unattended kit launcher passes `-config config:pvr.rend=0`: a leftover
  `pvr.rend = 4` (Vulkan) in `emu.cfg` segfaults the fork bundle, which is
  built without MoltenVK (senkosp tooling.md:3244-3246, "Launch gotcha
  added"; ausfache `docs/kb/tooling.md:39-40`). It sits right after
  `-config config:rend.vsync=no`; a caller's extra arguments
  (`capture_dc_leg.sh`'s third and later) follow, so they can override it.
- `test_vmu_untouched.sh play` is headed on purpose (the tester plays and
  quits Flycast) and keeps the caller's renderer.

## Instrumented Flycast

*Source: senkosp `docs/kb/tooling.md:8-287` (commit `1aac566`; unchanged since `afab584`).*

- **Binary (since 2026-09-21):**
  `../flycast4naomi2dreamcast/build/Flycast.app/Contents/MacOS/Flycast`
  (Mach-O arm64), built in the fork checkout itself — full recipe in
  senkosp `docs/kb/tooling.md` §"Decoupling from ../cleopatra (2026-09-21)". Before that date the
  project ran the reused build at
  `../cleopatra/tools/flycast-src/build/Flycast.app` (checkout commit
  `625425f72`, Phase 5 Task 2, rebuilt 2026-08-23 — see below); originally
  the same build the senkosp assessment v9 capture used
  (`../naomi2dreamcast/assessments/senkosp.md` §1, then `f014a410c`).
- **Source of truth:** `../flycast4naomi2dreamcast` (fork) — now also the
  only checkout this project uses.
  **Note (2026-08-22):** `../cleopatra/tools/flycast-src` and
  `../flycast4naomi2dreamcast` are two independent checkouts of the same
  `origin` remote (`CaptainKoffski/flycast4naomi2dreamcast`) and can drift —
  found 13 commits apart (Cleopatra-side instrumentation pushed directly
  from the `flycast-src` checkout, never pulled into the standalone one).
  Reconciled via `git stash` / fast-forward pull / `git stash pop` before
  this task's edits landed; before any future fork edit, `git fetch && git
  log --oneline HEAD..origin/master` in `flycast4naomi2dreamcast` to catch
  this early. Commit in `flycast4naomi2dreamcast` (source of truth), push,
  then `git pull --ff-only` in `flycast-src` before rebuilding — do not edit
  `flycast-src` directly and leave it uncommitted.
  **Phase 4 Task 1 fork commits:**
  `0166c5b77` — maple `trig=` tag (`maple_SB_MDST_Write`→`reg`,
  `maple_vblank`'s `SB_MDTSEL==1` branch→`vbl`) threaded into `MDODMA`/
  `MAPLEPC`/`MIERESP`; `cartlog_sp_sample()`/`cartlog_sp_water()`
  (`cartlog.cpp`, `SPWATER` emitted at the existing ~10s `cartlog_sample()`
  tick). `0d55a1812` — follow-up: per-event `sp=` on `MDODMA`/`MAPLEPC`
  lines, added after the whole-run `SPWATER` aggregate proved unable to
  separate the task-cluster floor from a third low-SP region — **identified
  2026-08-22 (Phase 4 Task 4) as the Naomi BIOS's own stack**, sampled before
  the BIOS hands the machine to the game, not a game stack at all
  (`docs/kb/boot-binary.md` §SP — two stacks, addenda 2026-08-22).
  The per-event `sp=` field remains the right construction regardless: it is
  what let `sp_consistent` be scoped to fn-confirmed PCs and so exclude the
  BIOS.
  **Phase 4 Task 2 fork commit:** `6e3522822` — `cartlog_shimwatch2()`
  (`naomi.cpp`), a baseline-and-compare write-watch over senkosp's own
  shim-home window (`mem_b` `0x00010000`–`0x00017fff`, P1
  `0x8c010000`–`0x8c018000`), reusing the existing whole-RAM handoff
  baseline `cartlog_main_base` rather than a second private snapshot buffer.
  Emits `SHIMWATCH2 addr= was= now=` at the same `cartlog_sample()` cadence.
  No checkout drift this time (`git fetch && git log --oneline
  HEAD..origin/master` in both checkouts was clean before this edit landed).
  `docs/kb/phase4-conversion.md` §Shim home (V2s).
  **Phase 5 Task 2 fork commit:** `79182301d` in `flycast4naomi2dreamcast`
  (canonical) — `gd_crc32()` (CRC-32/IEEE, same variant as the shim's
  `shim_crc32`/Python `zlib.crc32`) plus two `cartlog()` call sites in
  `gdromv3.cpp`: `GDPIO` after the PIO refill's `libGDR_ReadSector` (before
  `read_params.start_sector += sector_count`) and `GDDMA` after
  `DmaBuffer::fill`'s `libGDR_ReadSector` (before `params.start_sector +=
  count`) — drive-truth CRCs for `kit/scripts/check_stream_crc.py` (Task 3).
  Both format strings end in `\n`, one deliberate departure from the task
  brief's snippet: every existing `cartlog()` call site in this fork
  (`naomi.cpp`, `maple_if.cpp`) terminates its line with `\n` (`cartlog()`
  is a raw `vfprintf`, no auto-newline — `cartlog.cpp`), and Task 3's
  parser reads `GDPIO`/`GDDMA` as one record per line; the brief's snippet
  omitted `\n` on both calls, which the smoke leg confirms would have run
  every record together into a single unparseable line.
  **No push this task** (task instruction: do not push either repo), so
  this checkout (`flycast-src`) could not `git pull --ff-only` from
  `origin` the way the drift note above prescribes. Instead: added the
  canonical fork as a scratch local remote inside `flycast-src`
  (`git remote add phase5canon /Users/captainkoffski/AntigravityProjects/flycast4naomi2dreamcast`),
  `git fetch phase5canon master`, `git cherry-pick 79182301d` (clean,
  `flycast-src` had no local commits ahead), then removed the scratch
  remote. Result: `flycast-src` HEAD `625425f72` — same author, message,
  and diff as `79182301d`, different SHA (different commit timestamp/tree
  parent chain from the independent checkout) rather than a true
  fast-forward. Rebuilt at `625425f72`, not `79182301d` — record this
  commit pairing, not just one SHA, if reconciling the two checkouts later.
  **Rebuild (2026-08-23):** `export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`
  then `cmake --build build -j"$(sysctl -n hw.ncpu)"` in `flycast-src`
  (incremental — the configured tree already existed, no reconfigure
  needed), exit 0, only pre-existing linker warnings (`-s` obsolete,
  duplicate static libs, deployment-target mismatches on `libomp`/`libpng`
  dylibs — unrelated to this change). **Smoke leg** (`phase5/probe-smoke`,
  one-call foreground pattern, 60 s unattended attract, killed by PID):
  `captures/phase5/probe-smoke.log` — 241 `GDPIO|GDDMA` lines (129 `GDPIO`,
  112 `GDDMA`), all 241 correctly newline-terminated one-record-per-line
  (verified: 0 lines match two tags concatenated, 0 lines contain a tag
  without starting with it).
  **Phase 5 Task 5 fork commits:** `8b1d45f2e` (sampler) + `a13662ff1`
  (`INSTRUMENTATION.md` row) in `flycast4naomi2dreamcast` (canonical) —
  `cartlog_texerr_tick()` (`core/hw/naomi/naomi.cpp`), a baseline-and-compare
  sampler of senkosp's texture-error classifier cells (`docs/kb/
  phase5-hardware.md` §Texture-error handler: `0x8c1a20a0`/`0x8c1a20a8`/
  `0x8c1a2098`), called from `core/hw/pvr/pvr_regs.cpp`'s existing
  `STARTRENDER`-write `cartlog()` site and throttled to every 64th call.
  Emits `TEXERR idx= code= d98=` once at first sample, then only on change —
  same discipline as `cartlog_shimwatch2`. No checkout drift (`git fetch &&
  git log --oneline HEAD..origin/master` clean in both checkouts before this
  edit). Cherry-picked into `flycast-src` the same way as Task 2 (scratch
  local remote `phase5canon`, `git cherry-pick`, remote removed after): both
  commits landed clean as `875aea8ff` + `b4763c1e8`. **Rebuild (2026-08-23,
  same session):** `export DEVELOPER_DIR=/Applications/Xcode.app/Contents/
  Developer` then `cmake --build build -j"$(sysctl -n hw.ncpu)"` — exit 0,
  same pre-existing linker warnings as the Task 2 rebuild above, nothing new.
  **Instrument control leg** (`phase5/instrument-ctl`, `docs/kb/
  phase5-hardware.md` §Instrument control test has the full account): all
  three `check_stream_crc.py` CHECKs PASS, 8 `TEXERR` lines (baseline +
  legitimate live-surface-count churn + one `code=6` line that turned out to
  be a second, independently-captured occurrence of the texture-error hang,
  fully unattended — see that section), 16,958 `PVRW STARTRENDER` over
  ~296 s (57.3/s, above both cited Phase 4 reference rates — no perf
  collapse).
  **`make`/`DEFS` gotcha found this task, recorded for every future
  diagnostic or release rebuild in this repo:** `shims/Makefile`'s `CFLAGS +=
  $(DEFS)` is not a tracked prerequisite of `$(B)/shim.bin` — `make`'s
  mtime-based check cannot see that command-line flags changed between
  invocations, only that the sources didn't, so a `shim.bin` built with
  different (or no) `DEFS` earlier in a session can be silently reused by a
  later `make gdi DEFS=...`, exit 0, "Nothing to be done", and ship a build
  that does **not** actually have the requested flags compiled in. Caught by
  `strings shims/build/shim.bin | grep SHIMCRC` coming back empty right
  after a "successful" diagnostic build. **Always `make clean` before a
  flag-sensitive build, or verify with `strings`/`nm` that the requested
  macro actually compiled in** — the make exit code proves nothing here.
  **Phase 5 Task 6 fork commits:** `167661363` (one-shot TEXERR
  auto-savestate) + `afc25186f` (`INSTRUMENTATION.md` row) in
  `flycast4naomi2dreamcast` (canonical). `cartlog_texerr_tick()`
  (`core/hw/naomi/naomi.cpp`, emu thread) now arms a one-shot latch
  (`g_texerrSavePending`/`g_texerrSaveCode`, file-scope `std::atomic`) on the
  classifier-cell `0x8c1a20a8`'s 0->nonzero transition, independent of the
  existing print-throttle statics. It does **not** call `dc_savestate()`
  itself: `emu.stop()` (`core/emulator.cpp`) joins the emu thread's own
  `std::async` result via `checkStatus(true)`, which self-join-deadlocks if
  called from the thread being joined — the same reason every existing
  savestate call site (`gui.cpp` hotkey/menu, `gui_saveState()`) runs from
  the SDL/render thread, never the emu thread. New function
  `cartlog_texerr_save_poll()` is called once per frame from
  `mainui_rend_frame()` (`core/ui/mainui.cpp`, confirmed the "Flycast-rend"
  thread by `ThreadName` in `mainui_loop()`); on a pending flag it runs
  `emu.stop(); dc_savestate(0); emu.start();` — the exact sequence
  `gui_saveState(stopRestart=true)` already uses for the `AutoSaveState`
  path (`core/ui/gui.cpp:1635`) — and emits
  `TEXERRSAVE code=<hex> slot=0 <path>` (or `TEXERRSAVE FAILED code=<hex>
  reason=<...>` if `dc_savestateAllowed()` is false or the sequence throws
  `FlycastException`). Index 0 (no user-configured `SavestatePath`) resolves
  through `hostfs::getSavestatePath(0, true)` to
  `~/Library/Application Support/Flycast/data/<contentbasename>.state` —
  same location the Phase 3 canary-snapshot already established (`senkosp.state`,
  §Phase 3: RAM snapshot above); the poll function queries that exact path
  before saving and logs it, rather than reconstructing/guessing it. No
  checkout drift (`git fetch && git log --oneline HEAD..origin/master` clean
  in both checkouts before this edit). Cherry-picked into `flycast-src` the
  same way as Tasks 2/5 (scratch local remote `phase5canon`, `git
  cherry-pick`, remote removed after): both commits landed clean as
  `631e7b9d6` + `c3d0c8451`. **Rebuild:** `export
  DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer` then `cmake
  --build build -j"$(sysctl -n hw.ncpu)"` — exit 0, same pre-existing linker
  warnings as prior rebuilds, nothing new.
  **Sanity leg** (`phase5/task6-sanity`, one-call foreground pattern, 90 s
  unattended attract, `-config Debug:SerialConsoleEnabled=yes`, killed by
  PID): `captures/phase5/task6-sanity.log` — 108,988 lines; 5 `TEXERR`
  lines (cold-start baseline + 4 legitimate live-surface-count changes,
  `code=00000000` throughout — same healthy signature as the Task 5 control
  leg's first samples), 0 `TEXERRSAVE` lines (expected — the trigger
  condition, `code` 0->nonzero, never occurred on this healthy leg; the
  latch logic itself was verified by code read, not by a forced firing, per
  this task's scope). `check_stream_crc.py` — all three CHECKs PASS
  (`shimcrc_match`: 60 records/0 mismatches; `gdread_match`: 256
  verified/4 lowfad/0 mismatches; `coverage_nonzero`: shim=60, drive=260).
  No `abort|crash|signal|disconnected|fatal` in the `.stdout.log`. Build
  confirmed healthy before the soak campaign (docs/kb/phase5-hardware.md
  §Repro campaign has the per-leg soak table).
  **Phase 5 fix-scoping fork commit:** `10de83124` (ARENAHW texture-arena
  high-water walker: `cartlog_arena_tick()` in `core/hw/naomi/naomi.cpp`,
  called from the `STARTRENDER` write path in `core/hw/pvr/pvr_regs.cpp`
  next to `cartlog_texerr_tick()`; `INSTRUMENTATION.md` row in the same
  commit) in `flycast4naomi2dreamcast` (canonical). Cherry-picked into
  `flycast-src` the same way as Tasks 2/5/6 (scratch local remote
  `phase5canon`, removed after) as `b5a275a11`; rebuilt with the same
  `cmake --build build -j"$(sysctl -n hw.ncpu)"` recipe — exit 0, same
  pre-existing linker warnings only. Validated on the Naomi-profile smoke
  leg `phase5/arenahw-smoke` (docs/kb/phase5-hardware.md §High-water
  measurement). The walker is passive and always-on-when-cartlog: any
  future instrumented leg (either profile) keeps emitting `ARENAHW`
  running-max lines for free.
  **Phase 5 fix-scoping local tools:** `../senkosp2dreamcast/scripts/decode_pvr_vq.py` (pure
  stdlib GBIX/PVRT VQ→PNG decoder; usage
  `python3 ../senkosp2dreamcast/scripts/decode_pvr_vq.py senkosp.dat <offset-hex> <out.png>`;
  outputs are ROM-derived — keep under gitignored `captures/`). Fixed
  2026-08-24: the codebook read started 16 B late (32-byte read of the
  16-byte `PVRT` header); control-tested after the fix against
  `/FONT.PAK`'s glyph sheet (clean A–Z/0–9 grid — see
  `docs/kb/phase5-hardware.md` §Fix scoping correction note).
  `../senkosp2dreamcast/scripts/list_pak_textures.py` (added 2026-08-24): lists the ISO root
  (`python3 ../senkosp2dreamcast/scripts/list_pak_textures.py senkosp.dat`) or the `PVRT`
  textures inside one file (`… senkosp.dat STAGE08.PAK`) with absolute
  dat offsets ready for the decoder.
  **Option-2 fix tools (2026-08-24):** `tools/pyenv` — venv created with
  `python3 -m venv tools/pyenv && tools/pyenv/bin/pip install numpy`
  (numpy 2.5.2, Homebrew python 3.14.3; gitignored under `/tools/`).
  `../senkosp2dreamcast/scripts/shrink_vq.py` (run as
  `tools/pyenv/bin/python ../senkosp2dreamcast/scripts/shrink_vq.py`) re-encodes the four
  STAGE08 textures at 512×512 into `build/texpatch/` (gitignored,
  deterministic — fixed k-means seed); `kit/scripts/make_gdi.py` splices
  them at mastering time (md5-guarded both sides), `--no-texpatch` for
  the unpatched reference build. `decode_pvr_vq.py` gained an importable
  `decode()` (CLI unchanged, refactor verified byte-identical on a
  stage08 decode). The flat
  `.dat` is an ISO9660 image: PVD at `.dat 0x808000`, file mapping
  `dat_off = (LBA − 40904) × 2048` — walk recipe and file inventory in
  `docs/kb/phase5-hardware.md` §Fix scoping.
- **BIOS:** `~/Library/Application Support/Flycast/data/naomi.zip` already
  installed (verified 2026-08-13); source copy in this repo: `bios/naomi.zip`.
- **Launch gotchas (macOS, every unattended run):**
  - absolute ROM path (relative → `Cannot stat ...`);
  - `defaults write com.flyinghead.Flycast ApplePersistenceIgnoreState -bool YES`
    once per session (else a prior killed run silently blocks the next boot);
  - `-config config:rend.vsync=no` (unfocused window deadlocks the emu
    thread otherwise);
  - stop by PID only (`$!` of the launcher — it `exec`s Flycast), never
    `pkill -f`/`-x`: other projects run Flycast concurrently (2026-10-04).
    (Old note: stale instance → SH4 vmem `Verify Failed`; not reproduced
    with two healthy instances side by side, 2026-10-04.)
- **Screenshots:** env `FLYCAST_SHOT=/abs/path.png` (+ optional
  `FLYCAST_SHOT_EVERY=N` frames, default 60); `kill -USR1 <pid>` = reliable
  on-demand single grab. 640×480 RGB PNG. Copy the file before reading —
  it is overwritten continuously.
- **Phase 7 Task 1 fork commit + drift reconciliation (2026-09-03):** The
  drift check before this task's edit (`git fetch && git log --oneline
  HEAD..origin/master`) came back clean in both checkouts individually, but
  each was ahead of `origin/master` by a *different, non-ancestor* history —
  real divergence, not just "behind". Root cause: `flycast-src` held a
  local-only commit `044a2fb6c` (Phase 6 black-gap recon,
  `core/hw/pvr/pvr_regs.cpp`) made by editing that checkout directly and
  never ported back to the canonical fork — the same failure mode flagged in
  the 2026-08-22 note above, recurred. **Reconciliation (controller-directed
  R4):** `git format-patch -1 044a2fb6c --stdout` from `flycast-src`, applied
  clean via `git am` in `flycast4naomi2dreamcast` as `d1a30ed91`, pushed.
  Gate before touching `flycast-src`: `git fetch && git diff origin/master
  HEAD --stat` — empty, confirming no other content had silently drifted.
  Only then: `flycast-src`'s `master` ref moved to the new `origin/master`
  (`git update-ref refs/heads/master origin/master` — `git reset --hard` was
  blocked by the environment's destructive-command guard). Safety basis
  (fix round, R7 — the gate diff alone proves content equality, not
  working-tree/index safety): the empty gate diff above shows `origin/master`
  and `flycast-src`'s old tree were content-identical, and the **post-op
  `git status`** (clean, only the pre-existing, unrelated `core/deps/Syphon`
  submodule diff — present before and after) is what actually confirms
  `update-ref` left the working tree and index untouched, since moving a
  ref touches neither by itself. Old SHA `044a2fb6c` stays reachable via
  reflog, not deleted. `flycast-src` is fast-forwardable from the fork
  again.
  **This task's fork commit:** `7ba6f1745` in `flycast4naomi2dreamcast`
  (canonical), pulled `--ff-only` into `flycast-src` clean (no cherry-pick
  workaround needed this time). Widens `cartlog_shimwatch2()`
  (`core/hw/naomi/naomi.cpp`) from the shim-home-only window to also cover
  the DreamShell isoldr slot `0x8c003800`–`0x8c00bfff` (skipping the
  game-owned `0x8c00c000`–`0x8c010000` gap — boot stack/VBR/scratch,
  `docs/kb/boot-binary.md`), capped at 64 emitted `SHIMWATCH2` lines + one
  `SHIMWATCH2 CAP` line. Adds a boot-scoped SP
  low-water (`sp_boot_min`, `core/hw/naomi/cartlog.cpp`) restricted to
  `0x8c000000`–`0x8c010000`, emitted as `bootmin=` on the existing `SPWATER`
  line. New GD-command SP feed: `cartlog_sp_sample(Sh4cntx.r[15])` at the top
  of `gd_process_spi_cmd()` (`core/hw/gdrom/gdromv3.cpp:731`) — the SPI/
  PACKET command dispatch entry (`cartlog.h` already included there from the
  Phase 5 Task 2 GDPIO/GDDMA probes, no new include needed). **Rebuild:**
  `cmake --build build -j"$(sysctl -n hw.ncpu)"` in `flycast-src` — exit 0,
  only the same pre-existing linker warnings as every prior rebuild (`-s`
  obsolete, duplicate static libs, `libomp`/`libpng` deployment-target
  mismatches).
  **Fix round (2026-09-03, controller ruling R6):** `cartlog_shimwatch2()`'s
  64-line cap had no per-address dedup and `emitted` was cumulative across
  the ~10s ticks — a byte that diverges once and stays diverged re-counted
  against the cap on every tick, so the cap could exhaust on a handful of
  real addresses and silently suppress new ones later in the run. Fixed
  with a per-address seen-bitmap (`static u8 seen[(0x18000 - 0x3800 + 7) /
  8]`, indexed by `i - LO1`, covers both windows plus the skipped gap —
  wasted bits there, trivial indexing); test-and-set before emitting,
  `emitted` increments only on first sight of an address. Cap semantics now
  "first 64 unique addresses". Fork commit `f821cdc3c` in
  `flycast4naomi2dreamcast` (canonical), pulled `--ff-only` into
  `flycast-src` clean. **Rebuild:** `cmake --build build
  -j"$(sysctl -n hw.ncpu)"` — exit 0, only `naomi.cpp.o` recompiled +
  relink, same pre-existing linker warnings, nothing new.

## Ghidra — 12.1.2

*Source: senkosp `docs/kb/tooling.md:298-414` (commit `1aac566`; unchanged since `afab584`).*

- Expected at `tools/ghidra_12.1.2_PUBLIC/` (gitignored; on this rig a
  symlink to the original install in `../cleopatra/tools/`) + OpenJDK via
  `export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"`. Any Ghidra 12.1.2
  unzip works — set `GHIDRA_HOME` if it lives elsewhere. Not
  exercised in Phase 1; Phase 3 sets up this repo's own project dir +
  scripts (below).

### Phase 3: this repo's Ghidra project (Task 3 onward)

Everything here is driven by the committed wrapper `kit/scripts/ghidra/run.sh`
(it exports the openjdk PATH itself and defaults
`GHIDRA_HOME=tools/ghidra_12.1.2_PUBLIC`; override the env var
if the install moves). Java in use: **OpenJDK 26.0.1 (Homebrew)**.

**1. The working image — the boot slice.** Static analysis runs on the main
load only (`.dat` offset 0 → RAM `0x8c020000`, entry `0x8c021000`), not the
251 MB `.dat`:

```sh
head -c 1515512 senkosp.dat > tools/boot.bin
md5 tools/boot.bin      # 07008ad629d628c519635dbc113487f5
md5 senkosp.dat         # 6283cf5c75d7fc32740a8e8e54d10aa8
head -c 1515512 senkosp.dat | cmp - tools/boot.bin && echo reproduces
```

1,515,512 B = the main load size from `game.md` §Parsed .dat header
(`0x171ff8`). `tools/` is gitignored — `boot.bin` is ROM content, **never
committed**, always regenerable by the line above.

**2. Import (full auto-analysis, once).** Project dir `tools/ghidra-proj`
(gitignored — it embeds ROM bytes), program name **`senkosp3`**:

```sh
kit/scripts/ghidra/run.sh import
# = analyzeHeadless tools/ghidra-proj senkosp3 -import tools/boot.bin -overwrite \
#     -processor "SuperH4:LE:32:default" -loader BinaryLoader -loader-baseAddr 0x8c020000
```

No `-noanalysis` on import — full SH-4 auto-analysis is what follows
`jmp @rN` through literal pools.

**3. Run a script** (always `-noanalysis`, so the DB is not re-analyzed):

```sh
kit/scripts/ghidra/run.sh script FindMmioXrefs.java
kit/scripts/ghidra/run.sh script DisasmRange.java 0x8c029ee8 0x8c029f5c force
```

Committed scripts (`scripts/ghidra/`, all headlessly re-runnable):
`FindMmioXrefs` (MMIO literal-pool xref reporter), `ScanBiosTargets`
(BIOS-range flow refs + pool constants), `DumpEntryChain` (entry walk + SP
writes), `ScanPlacementConstants` (corridor/VRAM placement constants),
`Decomp`, `DisasmRange` (`… force` force-disassembles an undefined span),
`DisasmEntry`, `FindRefsTo`, `WhichFunc`, `ListPoolWords`, `ExportToXML`,
`CallTree` (recursive caller tree following direct and pool-word computed
calls; added 2026-08-26 for the arena free-path recon; DB mutation note:
the 2026-08-26 recon also force-disassembled the scene-code windows
`0x8c1592xx–0x8c159axx`, `0x8c0b5b90–e8`, `0x8c087270–0x8c087830` — same
monotonic-additions caveat as the Task 4 spans).

**Savestate post-mortem (2026-08-26):** `../senkosp2dreamcast/scripts/texerrsave_postmortem.py`
— pure-python (stdlib) offline attribution of every VRAM texture-arena
block in a TEXERRSAVE Flycast savestate to its source texture on the
disc (RZIP-container decompress, RAM/VRAM location by content anchoring,
arena list walk, byte-exact match against all TXTR records + all
LZSS-decompressed PKTX entries). Run:
`tools/pyenv/bin/python3 ../senkosp2dreamcast/scripts/texerrsave_postmortem.py [state] [dat]`.
No installs needed; the LZSS decoder semantics are documented in
`phase5-hardware.md` §Ghidra + savestate recon.

**DB mutation caveat, stated because it affects reproducibility:** the
`senkosp3` DB carries the *force-disassembly* additions Task 4 made
(`DisasmRange … force` over the undefined hardware-driver and RTC spans).
Those are monotonic additions to the listing. Their non-effect is argued for
**`FindMmioXrefs` only**: it counts *defined data*, and `run.sh script`
passes `-noanalysis`, so nothing promotes the recovered code's pool words to
defined data — boot-binary.md §Coverage limits documents that exact
non-effect (re-running the scan after the force-disassembly still reported
`rtc` = 3). **No equivalent argument is made for `DumpEntryChain`**: it walks
disassembled instructions, so a DB with more disassembly *could* in principle
walk further. Its output reproduced exactly here, but that is an observation
on this DB, not a proof of DB-independence.

**Fresh-checkout status — untested, stated plainly.** The spec's exit
criterion 4 asks for a re-run *from a fresh checkout* (given the gitignored
ROM). That path is: regenerate `tools/boot.bin` (step 1), `run.sh import`
(step 2, full auto-analysis), then the scripts (step 3) — **it has not been
exercised**. Two things a fresh checkout would not have: the Task 4
force-disassembly state, and any reference output to diff against
(`tools/` is gitignored, so `tools/mmio-xrefs.txt` does not exist until the
scan regenerates it). `00-status.md` criterion 4 carries this as a `[~]`.

**Reproduction check (Task 13, exit criterion 4 — 2026-08-22).** Both
reporting scripts were re-run from the committed harness and diffed
mechanically, not eyeballed:

```sh
kit/scripts/ghidra/run.sh script FindMmioXrefs.java  > /tmp/mmio-rerun.txt
kit/scripts/ghidra/run.sh script DumpEntryChain.java > /tmp/entry-rerun.txt
# strip the "INFO  <script>.java> " prefix + Ghidra harness banner, then diff
```

- `FindMmioXrefs`: **73 payload lines identical** to the copy of its own
  earlier output kept at `tools/mmio-xrefs.txt` — **gitignored, not
  committed** (it is derived ROM content; the scan above is what regenerates
  it) — 72 hits + `TOTAL hits=72`; per-block counts
  reproduce boot-binary.md's table exactly — `wdt` 43, `maple` 11, `g1dma`
  10, `rtc` 3, `cart` 3, `scif` 2, `pvr_fb` 0. Only difference in the raw
  files: the Ghidra/JVM banner (timings, JDK warnings).
- `DumpEntryChain`: all **35** instruction lines quoted in boot-binary.md
  §Entry chain match address-for-address and mnemonic-for-mnemonic, and all
  three `<== writes r15` lines carry the same values (`0xac00f400`,
  `0x8c00f400`, `0x8c00f000` via `8c170c14`). One documentation fix fell out
  of this run: the `Stack region: …` line was never script output — it is a
  derived value, now labelled as such in boot-binary.md §Stack region.

## sh-elf / KOS toolchain (Phase 4 Task 6; KOS in-repo since 2026-09-21)

*Source: senkosp `docs/kb/tooling.md:932-969` (commit `1aac566`; unchanged since `afab584`).*

- **sh-elf (dc-chain):** `/opt/toolchains/dc/sh-elf/bin/` — machine-wide
  install, not per-repo. `sh-elf-gcc --version` → `sh-elf-gcc (GCC) 15.2.0`.
  Used directly by `kit/shims/rules.mk` (`CC`/`NM`/`OBJCOPY` point at this path)
  and indirectly by KOS's `kos-cc` wrapper (below).
- **KOS (since 2026-09-21):** `tools/kos` — gitignored in-repo checkout,
  KallistiOS commit `705c8629` (v2.2.0-932); clone + build recipe in
  §"Decoupling from ../cleopatra (2026-09-21)" below. (Until that date the
  build reused `../cleopatra/tools/kos` — same commit, same environ.sh
  settings.) `source tools/kos/environ.sh` before any `make -C
  loader` or top-level `make loader`/`make test`; sets `KOS_BASE` to the
  `tools/kos` path (absolute), `KOS_CC_BASE=/opt/toolchains/dc/sh-elf`,
  `KOS_ARCH=dreamcast`, `KOS_SUBARCH` unset (defaults to `pristine` — this
  loader boots as a normal DC homebrew via GDEMU, not native Naomi).
  `kos-cc --version` → `sh-elf-gcc (GCC) 15.2.0` (kos-cc wraps sh-elf-gcc
  with KOS's include/lib paths).
- **BIOS used by the loader build:** `bios/naomi/epr-21576h.ic27`
  (senkosp2dreamcast's own copy, not Cleopatra's — same filename, Naomi
  Japan bios0), md5 `d1e4be4862f1f9592b17a042abc5831e`.
- **Finding (Task 6, load-address collision):** KOS's default link origin
  for this pristine-subarch target is `0x8c010000`
  (`tools/kos/utils/ldscripts/shlelf.xc` line 10,
  `LOAD_OFFSET = ... 0x8c010000`) — confirmed empirically:
  `sh-elf-nm loader/loader.elf` places `_start`/`__executable_start` at
  `0x8c010000` and `_main` at `0x8c010158`, with a combined text+data+bss
  footprint of 838,704 B (`sh-elf-size loader/loader.elf`), i.e. the running
  loader occupies roughly `0x8c010000`–`0x8c0dc000`. This is the SAME
  address as senkosp's `SHIM_BASE` (`shims/include/shim_iface.h`) and
  overlaps `GAME_LOAD_ADDR` (`0x8c020000`) too. Cleopatra never hit this
  because its shim home was `0x8cfc0000` (near RAM top, far from
  `LOAD_OFFSET`); senkosp's shim home moved to low RAM (spec-pinned,
  `docs/kb/phase4-conversion.md` §Shim home) specifically because
  Cleopatra's old high placement collides with senkosp's own relocated heap
  (`docs/kb/relocation-map.md` §Provenance). The loader code that would
  `memcpy` the shim into place is present (Task 6 copies it in, from
  Cleopatra) but kept behind `#if 0` — this collision is why it must stay
  disabled until a later task resolves it (see task-6-report.md).

## Decoupling from ../cleopatra (2026-09-21)

*Source: senkosp `docs/kb/tooling.md:2532` + `:2542-2563` (commit `1aac566`), the KOS recipe only.*

- **KOS at `tools/kos`** (gitignored): same commit as the previously
  reused cleopatra checkout —
  `git -C ../cleopatra/tools/kos rev-parse HEAD` = `705c862957b2f…`
  (v2.2.0-932-g705c8629, banner identifies as v2.3.0). Install:

  ```sh
  git clone https://github.com/KallistiOS/KallistiOS.git tools/kos
  git -C tools/kos checkout 705c862957b2f6091a6ce4784943744daecc3e2b
  # environ.sh = doc/environ.sh.sample with ONE change: KOS_BASE set to
  # the absolute path of tools/kos (verified: that was also the only
  # export-line delta in cleopatra's environ.sh)
  . tools/kos/environ.sh
  make -C tools/kos/kernel -j8 && make -C tools/kos/addons -j8
  make -C tools/kos/examples/dreamcast/hello   # test-serial payload
  ```

  Two caveats, both hit on first build: (1) top-level `make -C tools/kos`
  dies in `utils/` — `makeip` wants `png.h`, `vqenc` wants `jpeglib.h`
  (no Homebrew libpng/libjpeg here); the utils are NOT needed (IP.BIN
  comes from the donor), hence kernel+addons built directly. (2)
  `environ_dreamcast.sh` probes unset `KOS_SUBARCH` and kills `set -u`
  shells — source from a normal shell.

## GDI mastering (Task 8) — `make gdi`

*Source: senkosp `docs/kb/tooling.md:971-1051` (commit `1aac566`; unchanged since `afab584`).*

- **Donor archive:** `[GDI] Dolphin Blue.7z` (44 MB) at this repo's root
  (historically copied from `../cleopatra/`:
  `cp "../cleopatra/[GDI] Dolphin Blue.7z" .` — any copy of the same
  megavolt85 release archive works) — gitignored (`*.7z` line
  added to `.gitignore`; `git check-ignore -v "[GDI] Dolphin Blue.7z"`
  confirms). Same donor, same B5 max-clone structure and extraction method as
  Cleopatra's own recipe (`../cleopatra/docs/kb/tooling.md` §"Reference
  self-boot GDIs"): `kit/scripts/make_gdi.py` extracts it into `build/donor/`
  itself via `/opt/homebrew/bin/7zz` (brew `sevenzip`), cached — re-extracted
  only if any of the five donor files is missing.
- **Build:** `make gdi` (top-level target, `Makefile`) → `loader` then
  `python3 kit/scripts/make_gdi.py` → `build/disc.gdi` + four tracks. Exit 0;
  deterministic (four runs from clean, identical md5s — recorded in
  `docs/kb/phase4-conversion.md` §First DC boot).
- **`kit/scripts/make_gdi.py`** — adapted from `../cleopatra/scripts/make_gdi.py`
  byte-for-byte except the cart source (`senkosp.dat`), the IP.BIN identity
  fields, and track04's payload; the B5 clone strategy, the donor extraction,
  and the CART_FAD/CART_SIZE cross-check against `shims/include/shim_iface.h`
  are unchanged. That cross-check caught a real bug on the first run — see
  `docs/kb/phase4-conversion.md` §First DC boot for the `CART_SIZE` fix.
- **Track 4 re-laid out: cart first, loader last (2026-10-04, branch
  `gdi-track4-fit`).** Donor order `[loader @ LBA 450000][cart]` made our
  track04 (124,454 sectors) end at LBA 574,454 — 25,304 sectors past the
  GD-ROM high-density area (ends LBA 549150 = lead-out FAD 549300 − 150,
  `../flycast4naomi2dreamcast/core/imgread/common.h:148`). GDEMU's default
  `image_tests = 1` rejects such images ("relaxed to allow oversized media"
  only when 0 — https://gdemu.wordpress.com/operation/gdemu-operation/)
  → straight back to the BIOS (operator report, GDEMU-clone fw 5.15b: boots
  only with `image_tests = 0`). Every GDI since Task 8 had this layout,
  hence this overrun; Flycast never enforced the limit.
  - **The loader can't move below LBA 450000.** First attempt shifted all
    of track 4 (and the FS extent) to 400000: real-BIOS Flycast
    (`UseReios = no`) dropped to the BIOS menu without ever reading the
    file. Bisect (`captures/track4/var-{A..D}-1`, same bytes, only the
    .gdi track-4 start / FS extent varied): gdi 450000 + extent 450000 →
    reads FAD 450150; gdi **400000** + extent 450000 → reads it too (TOC
    start irrelevant); extent 400000 or **449000** → never read. Matches
    GDIBuilder: the boot file "must be at least 100 minutes into the disc"
    (100 × 60 × 75 = 450,000 —
    https://projects.sappharad.com/tools/gdibuilder.html) and "placed at
    the end of the final data track" (https://github.com/Sappharad/GDIbuilder).
  - **Fix:** track04 = `[cart][--lz4 blob][zero pad][loader]`, track 4 at
    LBA 320000 (disc.gdi line rewritten), cart at CART_FAD **320150**
    (was 451878; `shim_iface.h`), loader at the donor's LBA 450000 (track03
    back to donor-verbatim; `check_boot_extent()` asserts the FS extent),
    image ends at LBA 451728. 7,274 sectors (~14 MB) between cart end and
    loader hold the blob; `make_gdi.py` asserts both the blob/loader
    overlap and the ≤ 549150 end.
- **`kit/scripts/capture_dc_leg.sh <leg> [gdi-path]`** — DC-profile leg launcher
  (clone of `kit/scripts/capture_leg.sh`, no `FLYCAST_ENTRYPC`/BIOSEXEC export,
  GDI default `build/disc.gdi`, separate `<leg>.stdout.log`). Same launch
  gotchas as §"Instrumented Flycast" above (`ApplePersistenceIgnoreState`,
  `vsync=no`, pre-launch `pkill`) plus: the DC profile takes the `.gdi` path
  itself as the CLI argument (no ROM/BIOS args — DC HLE boot needs neither).
  **One-call foreground pattern, 600 s hard cap (Task 6):** the agent
  Bash tool clamps a leg's execution to 600000 ms regardless of a larger
  requested `timeout`, so a `sleep 600` leg's own kill tail
  (`kill -USR1`/`sleep 5`/`kill -9`/`wait`) can get cut by the tool's own
  SIGTERM (exit 143) — captures completed fine when this happened, but keep
  unattended-leg `sleep` ≤ ~550 s under this pattern, or split launch/kill
  across two tool calls for longer legs (full account:
  `docs/kb/phase5-hardware.md` §Repro campaign (Task 6)).
- **Screenshot in this session — two working mechanisms, two caveats found
  (Task 8):**
  - `screencapture -x` (macOS): failed every attempt —
    `could not create image from display` — a Screen Recording TCC
    permission this session's process does not hold. Needs a human to grant
    it in System Settings; not fixable from inside the session.
  - `FLYCAST_SHOT=/abs/path.png` + `kill -USR1 <pid>`
    (§"Instrumented Flycast" above) worked, but the render/present pipeline
    was **severely throttled** for a backgrounded/occluded window in this
    session: it delivered only a handful of real frames over roughly two
    minutes before stalling, rather than the normal continuous 60 Hz. A
    control-test capture of a known-good disc (`../cleopatra/build/disc.gdi`,
    same method) hit the identical stall, confirming it is this session's
    render-pipeline throttling, not any particular disc. Budget several
    minutes, not seconds, for a DC-profile screenshot in this environment;
    `docs/kb/phase4-conversion.md` §First DC boot has the full account and
    the resulting (torn-frame) evidence.

## CDI mastering — `make cdi` (2026-09-24)

*Source: senkosp `docs/kb/tooling.md:2694-2768` (commit `1aac566`; unchanged since `afab584`); the "Installs" and "Layout" subsections.*

Burnable **data/data MIL-CD** image for testers with CD-Rs (they asked;
generic GDI→CDI converters can't work on this port: the shim streams the
cart from a BAKED absolute FAD and the cart is raw sectors past the FS,
not a file — any file-level conversion drops or relocates it). The CDI is
mastered fresh by `kit/scripts/make_cdi.py`; `make release` now emits both
zips (`[GDI] …` and `[CDI] Senko no Ronde Special.zip`).

### Installs

- **img4dc / cdi4dc 0.5b** — `tools/img4dc` (gitignored under `/tools/`),
  shallow clone of https://github.com/Kazade/img4dc (the Unix-portable
  fork of SiZiOUS's originals; upstream `sizious/img4dc` hard-requires
  `windows.h` in common/console), HEAD `d28df15` (2023-04-15). Build:
  `mkdir tools/img4dc/build && cd tools/img4dc/build && cmake ..
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 && make
  cdi4dc` (Homebrew cmake 4.x refuses the project's
  `cmake_minimum_required(3.0)` without the policy flag). Binary:
  `tools/img4dc/build/cdi4dc/cdi4dc`.
- **mkisofs 3.02a09** — already present (Homebrew `cdrtools 3.02a09`).
  Plain MSINFO-0 invocation only (`-iso-level 1 -V SENKOSP -G ip.bin`);
  no `-C` offsets needed for the data/data layout.
- **scramble** — Marcus Comstedt's 1ST_READ scrambler, already built
  (arm64) in the KOS checkout: `tools/kos/utils/scramble/scramble`.

### Layout (all in `kit/scripts/make_cdi.py`)

**Round 2 (SHIPPED): audio/data** — the mature scene layout
(BootDreams-era convention; also what mkdcdisc emits today:
dreamcast.wiki "Creating a bootable Dreamcast disc"). Session 1 =
silent audio track (generated by cdi4dc itself); session 2 = one
mode-2 data track at **LBA 11702** = our ISO (`mkisofs -C 0,11702` —
all FS extents absolute): LBA 11702–11717 IP.BIN, then the ISO9660 FS
holding scrambled `1ST_READ.BIN`, zero-padded to a fixed 1792-sector
region (the CD analogue of the GDI donor's 3,538,944 B boot region),
then — since branch `soft-reset-cdi` (2026-10-10) — a **plain**
`1ST_READ.BIN` zero-padded to 1728 sectors (`shim_iface.h`
`LOADER_SECS`, the GDI boot region) that the soft-reset warm boot reads
back (`LOADER_FAD` CDI arm = 150 + 11702 + 1792 = **13644**; the FS copy
is scrambled, useless to the shim — `input-map.md` §Warm boot to the
menu), then the texpatched cart image and the optional `--lz4` blob,
same append math as `make_gdi.py`. **Cart FAD = 150 + 11702 + 1792 +
1728 = 15372** (13644 through tag 0.18.0; Makefile `CD_CART_FAD`, baked
via `make cdi` → `CDI=1` → `-DCART_FAD`; `BLOB_FAD` derives from
`CART_FAD` in `shim_iface.h`, so LZ4 tracks automatically). The plain
copy sits BEFORE the cart, not after it like the blob, so its FAD is a
compile-time constant whether or not `--lz4` is on. `make_cdi.py`
asserts the header's `#elif CART_FAD == 15372` → `LOADER_FAD 13644` arm
and `LOADER_SECS == 1728`, and pins both region offsets with `f.tell()`
asserts while writing; the image grew 292 → 296 MB. Pre-plain-copy
layout verified against the built image (2026-09-24): PVD at data-track
sector 16, root dir extent absolute LBA 11725, `1ST_READ` extent 11726,
cart first sector byte-equal to `senkosp.dat` at data-track sector 1792
— the plain copy shifts only the cart (now data-track sector 3520).
New layout verified functionally: leg `softreset/cdi-wb2` warm-boots the
loader from FAD 13644 three times, and the operator's GDEmu round
(2026-10-11) does the same on real hardware (`input-map.md` §Warm boot,
CDI).

**Round 1 (SUPERSEDED 2026-09-24, same day): data/data via `cdi4dc
-d`** — MSINFO-0 data track in session 1 (cart FAD 1942), 300-sector
IP+PVD boot track in session 2 (citation:
`tools/img4dc/cdi4dc/src/cdidata.c` `write_data_header_boot_track`).
Booted in Flycast + real BIOS (`cdi/boot-smoke2`) but **died on real
hardware via GDEMU** — see §Hardware round 1 below. cdi4dc's own
banner calls this mode beta; GDEMU data/data-CDI incompatibilities are
a documented class (dreamcast-talk t=16956: a data/data CDI can boot
burned on a real DC yet not boot on GDEMU).

IP.BIN = donor track03 head + the exact `make_gdi` branding + iplogo,
plus the CD device string: `0x25..0x2D` `GD-ROM1/1` → `CD-ROM1/1`
(citation: makeip `src/field.c:39` — community IP.BIN builder's CD
template value; the device-info CRC at 0x20 covers 0x40–0x4F only, so
the string edit needs no re-CRC).

## dcload-serial + dc-tool-ser — serial upload link (Task 25, 2026-09-02)

*Source: senkosp `docs/kb/tooling.md:1400-1474` (commit `1aac566`; unchanged since `afab584`).*

- **Install:** `tools/dcload-serial` (gitignored under `/tools/`) — shallow
  clone of https://github.com/KallistiOS/dcload-serial, HEAD `e4b29bf`
  (2026-07-15), VERSION 1.0.7. Deps were already present: sh-elf at
  `/opt/toolchains/dc/sh-elf` (Makefile.cfg's default TARGETPREFIX matches
  verbatim) and Homebrew libelf 0.8.13_1 at the macOS-arm64 default paths.
  Zero config edits.
- **Build:** bare `make` in the checkout builds everything we need, then
  fails at the final `1st_read.bin` step (`/utils/scramble` — a KOS-path
  scramble tool; env not sourced). Expected and harmless: the SCRAMBLED
  binary is for burned MIL-CD CD-Rs only. GD-area track04 boot takes the
  UNSCRAMBLED `target-src/1st_read/loader.bin` (15,724 B, `-Ttext=0x8c010000`
  per its Makefile — exactly where the donor bootstrap loads 1ST_READ.BIN).
  Per `1st_read/loader.s`, it relocates dcload proper to `0x8c004000`
  (dcload.x: ram ORIGIN 0x8c004000 LENGTH 0xb400) and the exception stub to
  `0x8c00f400`, so uploaded programs own `0x8c010000+`. Host tool:
  `host-src/tool/dc-tool-ser` (1.0.7, `-h` verified).
- **Boot GDI:** `python3 kit/scripts/make_dcload_gdi.py` → `build/dcload/`
  (B5 donor-clone reusing make_gdi.py's donor cache + brand_ip; track04 =
  loader.bin zero-padded to the donor boot region; IP title
  "DCLOAD-SERIAL 1.0.7" is what GDmenu will display). `make deploy-dcload`
  masters + copies to its own card slot — default `/Volumes/GDEMU/04`
  (created if absent; GDEMU stops scanning at the first missing folder
  number, so slots must stay contiguous), override with `DCLOAD_CARD=`.
- **Known-good payload:** KOS `examples/dreamcast/hello/hello.elf`
  (`tools/kos`; originally `../cleopatra/tools/kos`, rebuilt 2026-09-02 —
  same KOS commit and environ.sh settings the loader build sources). Its `printf` routes through dcload's console
  syscalls back over the cable — upload + execute + return traffic = two-way
  link proof in one leg.
- **Upload command (Mac side):**
  `tools/dcload-serial/host-src/tool/dc-tool-ser -t /dev/cu.usbserial-XXXX
  -x tools/kos/examples/dreamcast/hello/hello.elf`
  Default 57600 8N1 = dcload's boot rate; fewest variables for the control
  leg (the cable is proven at 115200 — raise with `-b` only after the
  control passes). **NEVER run dc-tool with the serial-SD dongle attached**
  — same SCIF pins (standing release-build rule, Makefile header).
- **HARDWARE control leg PASS (2026-09-02, operator + Mac, Task #25
  CLOSED):** `captures/phase6/dcload-hello.log` — GDEMU slot 04 → dcload
  banner → `dc-tool-ser -t /dev/cu.usbserial-110 -x hello.elf`: all 9 ELF
  sections delivered (201,296 B in 27.82 s, effective 7,234 B/s at 57600 —
  LZO chunks doing the work), executed at 0x8c010000, KOS v2.3.0 booted on
  silicon (real maple enumeration: 2 controllers + 2 VMUs; 640x480 VGA),
  `Hello world!` echoed back through dcload's console, `Program returned 0`
  → clean return to dcload, ready for the next upload. Two-way serial
  upload link fully proven end-to-end.
- **GAME-VIA-DCLOAD leg PASS (2026-09-02, operator + Mac):**
  `captures/phase6/dcload-game.log` — the full port booted from a
  cable-delivered loader: boot dcload (slot 04) → GDEMU button-swap back
  to the game disc (slot 03) → `dc-tool-ser -x loader/loader.elf`
  (release build, 875,412 B in 34.24 s — 25.5 KB/s effective, LZO eats
  the splash data) → executes at 0x8c010000, shim streams the cart from
  the swapped-in disc, attract reached (operator report; release loader
  is serial-silent, so the quiet dc-tool console post-execute is
  expected). Proves the iteration workflow: code changes travel over the
  cable (~35 s), the 251 MB cart stays on the card; the disc only needs
  re-mastering when DATA changes (e.g. texpatch config). The GDEMU
  runtime disc swap + raw-register cart reads post-swap work fine.
  **Characterized-benign quirk, dcload path only:** video signal drops
  during NOW LOADING (operator's monitor auto-offed, then re-locked for
  attract) — that window is the game's from-scratch SPG reprogram
  (`pc=8c032140`, §Black-gap control test); on this path the upstream
  video state is dcload's init rather than the BIOS's, so the rewrite is
  a real mode transition instead of a same-values no-op. Self-recovers;
  disc boots unaffected. **FALSIFIED 2026-09-07 (phase 7 T8 recon):**
  the "same-values no-op / disc boots unaffected" half is wrong — the
  ernula-lili VGA boot census shows the takeover mode-set changing
  SPG_LOAD/CONTROL/HBLANK/VBLANK/WIDTH/STARTX/STARTY for real on disc
  boots too (525→531-line raster), and the operator reports the drop on
  GDEMU disc boots. See phase7-polishing.md §T8.
- **Debug recipe going forward:** build `make loader SERIAL=1` and upload
  THAT loader.elf with `dc-tool-ser -p -x` (`-p` = dumb terminal: raw
  SCIF shim/loader chatter displays directly instead of confusing the
  dcload console protocol). Same disc in the drive serves both release
  and debug uploads — the disc's own boot region is bypassed.

## VMU canary harness (Task 29, 2026-09-03)

*Source: senkosp `docs/kb/tooling.md:1476-1528` (commit `1aac566`; unchanged since `afab584`).*

Cleopatra's VMU-safety harness ported near-verbatim
(`../cleopatra/scripts/test_vmu_untouched.sh`; design spec
`../cleopatra/docs/superpowers/specs/2026-07-26-vmu-safety-design.md` — the
oracle citations there are against the exact Flycast build we run, the
sibling repo's `tools/flycast-src`). Two deltas only:

- `BIN` points at the sibling repo's Flycast (this repo has no local
  flycast checkout).
- attract window default 90 s → **150 s** (senkosp's BIOS anim +
  NOW LOADING stream is slower than Cleopatra; the log must show the
  engine executing, not just BIOS, for the leg to mean anything).

Protocol unchanged: 3 × 128 KB `0xA5` canaries (A1/A2/B2) + all-zero
control (B1) in a temp dir; transient `-config` redirect
(`Dreamcast.VMUPath`, `PerGameVmu=no`, `UsePhysicalVmuMemory=no`,
vsync off, controller+VMU pinned on ports A/B); graceful osascript quit
(NOT kill -9 — buffered VMU fwrite could hide a write = false PASS);
PASS iff canaries byte-identical AND control auto-formatted (control
test: proves redirect/attachment/hash wiring in the same run).

- **`make test-vmu` PASS (2026-09-03, first run, release candidate
  disc.gdi of 2026-09-02):** all three canaries unchanged, control B1
  auto-formatted. Leg depth confirmed from the log tail: game's SPG
  reprogram (`pc=8c032140`) and AICA ARM reset both fired → engine code
  ran, maple path live, zero VMU writes.
- **`make test-vmu-play`** = same script, headed; operator plays as
  long as they like then quits Flycast (Task 30, pre-release gate).
- **`make test-vmu-play` PASS (2026-09-03, operator session, Task 30):**
  headed run, operator played then quit; verdict verified forensically —
  zero `/tmp/vmu-canary.*` dirs left behind, and the script deletes its
  temp dir ONLY on the PASS branch (FAIL or any mid-run abort keeps it),
  so the run provably reached "PASS: no VMU writes". Session breadth is
  operator-driven (paths exercised = whatever the session covered — the
  standing caveat of every dynamic layer). Tripwire gate 3/3 green.
- **Composite-fix leg set (2026-09-03, Task 31):** `phase6/comp-leg`,
  `comp-dbg`, `comp-dbg2`, `rel-comp3`, `rel-vga0` — pre-fix control,
  the mode-word-hook failure measurement, the sense-hook 15 kHz proof,
  release-build screenshot leg, and the VGA regression census. Verdicts
  + register tables: docs/kb/phase6-release.md §Composite fix.
- **Geometry-fix legs (2026-09-03, Task 31 round 2):** `phase6/geo-comp3`,
  `geo-vga0` — VIDEO-GEOM-HOOK verification (KOS NTSC geometry end-state,
  no vblank starvation on the 525-line frame, VGA census unchanged).
  docs/kb/phase6-release.md §Composite round 2.
- **Task 31 hardware PASS (2026-09-03, operator):** composite = synced +
  centered (sense hook + geometry hook), VGA = no regression. Closes the
  cable-variance coverage leg; docs/kb/phase6-release.md §Composite.
- **Task 32 DreamShell leg (2026-09-03, operator): characterized
  known-fail as flagged.** isoldr serves syscall reads (NAOMI magic
  passed) but the raw-ATA rehearsal halts loud (`r=-6` GD_E_CHECK, sense
  5 ILLEGAL REQUEST) — docs/kb/phase6-release.md §DreamShell. Port is
  GDEMU/optical-only; documented limitation, no fix planned.

## T9 menu asset generator (2026-09-12, branch phase7-t9)

*Source: senkosp `docs/kb/tooling.md:2168-2256` (commit `1aac566`; unchanged since `afab584`).*

- **Pillow install:** `python3 -m pip install --user pillow` refused
  (PEP 668 externally-managed environment, same class of block T7
  round 2 hit); fallback actually run:
  `python3 -m pip install --user --break-system-packages pillow` →
  **Pillow 12.3.0** (`python3 -c "import PIL; print(PIL.__version__)"`
  printed `12.3.0`). Generator-only rule unchanged: Pillow renders
  `loader/menu_sheet.png` + `loader/controls.png` offline
  (`kit/scripts/gen_menu_assets.py`, rerun after any `scripts/menu_def.py`
  edit); `kit/loader/rules.mk` itself still builds those PNGs into blobs
  with stdlib+sips only (`kit/scripts/bmp2rgb565.py`'s own header comment
  states the rule) — no PIL import anywhere under `loader/` or in any
  build-time script. A pre-existing `tools/venv-pil` (Pillow 12.3.0,
  from the retired T7 splash-text pipeline) was left alone; this task
  used the simpler `--user --break-system-packages` install instead of
  reviving that venv, since Step 1 asked for the exact command to be
  recorded, not venv reuse.
- **New generator scripts:** `scripts/menu_def.py` (settings rows +
  layout constants, the single source — transcribed verbatim from
  `docs/kb/phase7-polishing.md` §T9 RECON) and
  `kit/scripts/gen_menu_assets.py` (Pillow renderer; emits the two PNGs +
  `loader/menu_layout.h`). Both offline/dev-machine only, never run by
  `make gdi`; their outputs are committed like `splash.png`'s sibling
  blobs.
- **Value-chip dedup (sheet space, not style):** 8 settings rows ×
  their value counts = 41 (row, value) pairs, but only 22 distinct
  value strings (point-vs-human/cpu share "1".."5"; both round-time-vs
  rows share "50".."120"). At the spec'd 288×28 px per chip, 41 unique
  chips would need more area than the whole 640×768 sheet holds (41 ×
  288 × 28 = 330,624 px² alone); the generator caches rendered chips by
  exact text and reuses the rect for every row/value that shares it —
  22 chips fit with room to spare (packer bottom 720/768 px, 93.8%).
  `MENU_SET_VALUE[row][i]` entries for two different rows can therefore
  point at the identical sheet rect; that's intended, not a bug.
- **`make_gdi.py` boot-size guard:** a `len(ldr) <= BOOT_FILE_SIZE`
  assert already existed right after `ldr` is read (Phase 4,
  `f84a5558`) — the brief's "missing size guard" premise was stale.
  Rather than add a second, redundant assert at the write site (no
  code mutates `ldr` in between), the existing assert's message was
  upgraded to print the actual byte counts; still one guard, still
  fires before any of the track-copy/brand/patch work runs (fail
  fast), still exactly the diagnostic the brief wanted.
- **Blob linkage note (verified, not just built):** `make gdi` right
  after this task's Makefile wiring does NOT grow `1ST_READ.BIN` —
  `menu_sheet_blob.o`/`controls_blob.o` link clean (their
  `_menu_sheet_bin`/`_menu_sheet_bin_end`/`_controls_bin`/`_controls_bin_end`
  symbols are present and correctly named, confirmed via `sh-elf-nm`
  on the standalone `.o` files) but get discarded by the SH4 target's
  `-Wl,--gc-sections` (`tools/kos/environ_dreamcast.sh:34`)
  because nothing in the current C sources references them yet — that
  wiring is Task 5's `menu.o`. Verified the plumbing is correct anyway:
  a throwaway link with `-Wl,-u,_menu_sheet_bin -Wl,-u,_controls_bin`
  (forces the symbols live without a real reference, reverted
  immediately, never committed) grew `1ST_READ.BIN` to exactly
  884,304 + 983,040 + 614,400 = 2,481,744 B — still under the
  3,538,016 B ceiling — confirming both blobs are wired correctly and
  fit once Task 5 references them.

- **Menu sheet goes 8bpp palettized (2026-10-24, `feat/controls-library`,
  commit `3bb534f`).**
  - **Format:** `loader/menu_sheet.pal8` uses the logo's layout (the logo's
    pal8 note is in `00-status.md` §Menu logo; it had no tooling entry). That
    is a 512-byte palette of 256 × RGB565-LE, then 640 × `SHEET_H` 8bpp
    indices, row-major (`SHEET_H` 1280 since `e8f7727`; blob 819,712 B).
  - **Generator:** `kit/scripts/gen_menu_assets.py` renders the RGB sheet as
    before. It then snaps every channel to the RGB565 grid (truncation:
    `& 0xF8` / `& 0xFC` / `& 0xF8`, what the old RGB565 blob stored). It
    asserts the snapped sheet has ≤ 256 colours (197 today), so the
    following `quantize(256, dither=NONE)` is lossless and the blob decodes
    to exactly the old RGB565 sheet. Past 256 colours the generator fails
    instead of going lossy silently. It writes the decoded sheet as
    `loader/menu_sheet.png`, which is the preview and the source for the
    previews' crops.
  - **Self-check:** `kit/scripts/test_gen_menu_sheet.py` (in `make test`) checks
    that the blob's palette lookup equals `rgb565()` of the PNG for every
    one of the 640×1280 pixels (exhaustive since `5611201`; it was a
    strided sample before the final review), ~0.5 s.
  - **Build:** `kit/loader/rules.mk` `menu_sheet_blob.o: menu_sheet.pal8`
    objcopies the blob straight in (`sh-elf-objcopy -I binary -O elf32-shl
    -B sh4`, symbols renamed to `_menu_sheet_bin`/`_menu_sheet_bin_end`),
    the same rule as `logo_blob.o`. No sips or `bmp2rgb565.py` step is
    involved.
  - **Consumer:** `kit/loader/menu.c` `blit()` looks up a palette filled once at
    `menu_run` entry. The page bins, the splash and the logo paths are
    unchanged.
  - **Effect:** the loader went from 3,536,144 to 3,045,188 B, against the
    1728-sector limit of 3,538,944. The emulator proof that the on-target
    blit matches the old sheet is §Legs: ctl-library/boot-smoke1.

## `make deploy` — `gdemu_deploy.py` (2026-10-24)

*Source: senkosp `docs/kb/tooling.md:3338-3357` (commit `1aac566`; unchanged since `afab584`).*

Copied from `../tetkiwam2dreamcast` (commit 335cc3d; design + GDMenu
two-volume notes in its commit message). `make deploy` builds the CDI then
the GDI and calls `python3 kit/scripts/gdemu_deploy.py "$(GAMEDIR)"
build/disc.gdi build/cdi/disc.cdi`: it finds the `[GDI]`/`[CDI]` folders by
`name.txt` or creates them, rewrites `LIST.INI` in both of `01/`'s GDMenu
volumes, runs `dot_clean`, and ejects (`CARD=`, `NOEJECT=1` optional). The
self-check is `python3 kit/scripts/test_gdemu_deploy.py`, which needs cdrtools
(mkisofs/isoinfo, already recorded under §CDI mastering).

- **Hardware, user report 2026-10-24:** the first run went to slots 06/07
  because 04 was empty. **GDEMU hides every folder past a gap in the
  numbering**, so they didn't show up until the gap was closed by hand. Since
  then the script puts a new folder in the lowest free number; the self-check
  covers a gap, and it fails against the old max+1 code. After the gap was
  closed, the GDI and the CDI both booted on the Dreamcast (user report).
- On the real card `isoinfo -x /LIST.INI` prints "Short read" and nothing
  else: GDMenu's `track01.iso` is shorter than the volume size its header
  claims. Read the list by walking the root directory record instead.
