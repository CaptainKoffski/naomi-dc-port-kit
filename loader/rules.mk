# Loader build rules, included from the port's loader/Makefile (cwd = <port>/loader).
# The port sets, before the include: KIT, OBJS (ordered link list), CFLAGS
# additions (-I flags, $(DEFS)), DAT; KOS_PIN optional.
# Port inputs at their conventional places: main.c, menu_layout.h, splash.png,
# controls_pad.png, controls_stick.png, menu_sheet.pal8, logo_strip.pal8 (here),
# ../scripts/build_patch_table.py.
# The port's Makefile provides the rule for ../build/bios_data.bin (embedded
# here as bios_data.o): the BIOS-derived bytes the loader places, laid out as
# the port's shim_iface.h BIOS_DATA_*_OFF names document (senkosp: Naomi BIOS
# 0x60000 slice + kernel pieces A/B/C; Cleopatra: 0x60000 slice + 0x70 bytes
# @0x1ffd00). The composition is per game.
# Patch table: the port's scripts/build_patch_table.py; any further inputs its
# generator reads, the port declares as extra prerequisites of ../build/patch_table.h.
# Requires: KOS_BASE from the environment (source tools/kos/environ.sh).
TARGET = loader.elf
KOS_PIN ?= 705c8629
$(if $(KOS_PIN),,$(error loader/rules.mk: KOS_PIN is empty))
.PHONY: kos-pin-check
.DEFAULT_GOAL := all
all: ../build/1ST_READ.BIN
include $(KOS_BASE)/Makefile.rules
# Order-only: the check runs every time, but a phony prerequisite must not
# force a relink.
$(TARGET): $(OBJS) | kos-pin-check
	kos-cc -o $(TARGET) $(OBJS)
kos-pin-check:
	@h=$$(git -C $(KOS_BASE) rev-parse HEAD); case $$h in $(KOS_PIN)*) ;; *) echo "KOS at $(KOS_BASE) is $$h, kit pins $(KOS_PIN)" >&2; exit 1;; esac
# Kit loader sources. Same recipes as the KOS %.o pattern rules (.S: no
# CFLAGS). KOS Makefile.rules has no header-dependency tracking, so header
# prerequisites are declared explicitly (the port does the same for main.o).
handoff.o: $(KIT)/loader/handoff.S
	kos-cc -c $< -o $@
naomi_crc.o: $(KIT)/loader/naomi_crc.c
	kos-cc $(CFLAGS) $(CPPFLAGS) -c $< -o $@
menu.o: $(KIT)/loader/menu.c $(KIT)/loader/menu.h $(KIT)/loader/ctl_lib.h menu_layout.h \
        ../build/patch_table.h ../shims/include/shim_iface.h
	kos-cc $(CFLAGS) $(CPPFLAGS) -c $< -o $@
ctl_lib.o: $(KIT)/loader/ctl_lib.c $(KIT)/loader/ctl_lib.h menu_layout.h
	kos-cc $(CFLAGS) $(CPPFLAGS) -c $< -o $@
# The shim's raw-ATA GD driver, built into the loader as well so the loader can
# rehearse the exact runtime disc path before handoff (freestanding C, no shim
# dependencies). Explicit rule, not the KOS %.o pattern: the object must land
# here, not in shims/src, and GD_LOADER_BUILD=1 drops the driver's SHIM_ERR
# store -- SHIM_ERR (0x8c014000) is inside this loader's own image (KOS naomi
# LOAD_OFFSET == SHIM_BASE == 0x8c010000), so writing it would corrupt the
# loader that is about to draw the error screen.
gd.o: $(KIT)/shims/src/gd.c ../shims/include/shim_iface.h
	kos-cc $(CFLAGS) $(CPPFLAGS) -DGD_LOADER_BUILD=1 -c $< -o $@
# Syscall GD backend, loader build: direct-vector calls (no gdstack -- see
# gd_sys.c header: GD_STACK_TOP sits inside the running loader image).
gd_sys.o: $(KIT)/shims/src/gd_sys.c ../shims/include/shim_iface.h
	kos-cc $(CFLAGS) $(CPPFLAGS) -DGD_LOADER_BUILD=1 -c $< -o $@
# Phase 4 Task 9: patch_table.h resolves shim symbol ADDRESSES from shim.map;
# a shim rebuild moves every symbol, so the table must regenerate whenever the
# map changes. Running the generator before `make -C shims` shipped a table
# pointing into the middle of moved functions in Cleopatra (2026-07-21:
# deterministic mid-print wedge in Flycast, self-inflicted; same class of bug
# applies here -- ../scripts/build_patch_table.py depends on shim.map too, but
# `make` only re-runs a rule when ITS OWN prerequisite changed, not
# transitively, so this rule needs the same shim.map dependency Cleopatra's
# does). The generator ALSO reads shim_iface.h (mirror offsets), ../$(DAT)
# (the old-byte verify source -- NOT boot.bin, task-9-brief.md: entries span
# both images and dat_offset is uniformly a raw .dat offset) and
# reloc_patchset.json (the 4 reloc words, single source; declared by the
# port) -- all four must be deps or an offset/value move in one of them
# regenerates main.o but not the table (loader patches point at stale
# offsets; links and boots wrong, no error). The mechanism the port's rows
# run on is $(KIT)/scripts/patchgen.py -- a dep for the same reason.
../build/patch_table.h: ../shims/build/shim.map ../scripts/build_patch_table.py \
                        ../shims/include/shim_iface.h ../$(DAT) $(KIT)/scripts/patchgen.py
	cd .. && python3 scripts/build_patch_table.py
# shim.bin embedded as _shim_bin / _shim_bin_end (C's leading-underscore prefix;
# raw objcopy names verified with sh-elf-nm against the ../shims/build/shim.bin path).
shim_blob.o: ../shims/build/shim.bin
	sh-elf-objcopy -I binary -O elf32-shl -B sh4 \
	  --redefine-sym _binary____shims_build_shim_bin_start=_shim_bin \
	  --redefine-sym _binary____shims_build_shim_bin_end=_shim_bin_end \
	  $< $@
# The port's Makefile provides ../build/bios_data.bin (header comment);
# .DELETE_ON_ERROR keeps a failed recipe (its size check) from leaving a
# short blob behind.
.DELETE_ON_ERROR:
# Embedded as _bios_data / _bios_data_end (C's leading-underscore prefix).
bios_data.o: ../build/bios_data.bin
	sh-elf-objcopy -I binary -O elf32-shl -B sh4 \
	  --redefine-sym _binary____build_bios_data_bin_start=_bios_data \
	  --redefine-sym _binary____build_bios_data_bin_end=_bios_data_end \
	  $< $@
# Boot splash: the real Naomi BIOS logo frame (BIOS property, not game
# content -- same epr-21576h.ic27 Cleopatra captured it from, reused as-is).
# splash.png is gitignored (BIOS-rendered output, same category as the BIOS
# ROM) -- regenerate with kit/scripts/capture_naomi_splash.sh <the port's .dat>
# if ever missing.
# sips is stock macOS; converter is stdlib-only.
../build/splash.bin: splash.png $(KIT)/scripts/bmp2rgb565.py
	mkdir -p ../build
	sips -s format bmp splash.png --out ../build/splash.bmp > /dev/null
	python3 $(KIT)/scripts/bmp2rgb565.py ../build/splash.bmp $@
splash_blob.o: ../build/splash.bin
	sh-elf-objcopy -I binary -O elf32-shl -B sh4 \
	  --redefine-sym _binary____build_splash_bin_start=_splash_bin \
	  --redefine-sym _binary____build_splash_bin_end=_splash_bin_end \
	  $< $@
# T9 pre-game menu: sprite sheet (settings screen) + the two controls
# pages, all our
# own generated art (kit/scripts/gen_menu_assets.py from the port's
# scripts/menu_def.py --
# copyright rule, CLAUDE.md). The sheet is an 8bpp palettized blob written
# by the generator (menu_sheet.pal8: 256 x RGB565-LE palette then indices,
# the logo_strip.pal8 layout) and objcopied straight in; the controls pages
# use the sips+bmp2rgb565 pattern as the splash rule above.
menu_sheet_blob.o: menu_sheet.pal8
	sh-elf-objcopy -I binary -O elf32-shl -B sh4 \
	  --redefine-sym _binary_menu_sheet_pal8_start=_menu_sheet_bin \
	  --redefine-sym _binary_menu_sheet_pal8_end=_menu_sheet_bin_end \
	  $< $@
# Two controls pages (HKT-7700 pad / HKT-7300 stick); the menu blits the
# label chips from menu_sheet on top of whichever page is showing.
../build/ctl_pad.bin: controls_pad.png $(KIT)/scripts/bmp2rgb565.py
	mkdir -p ../build
	sips -s format bmp controls_pad.png --out ../build/ctl_pad.bmp > /dev/null
	python3 $(KIT)/scripts/bmp2rgb565.py ../build/ctl_pad.bmp $@ 640 480
ctl_pad_blob.o: ../build/ctl_pad.bin
	sh-elf-objcopy -I binary -O elf32-shl -B sh4 \
	  --redefine-sym _binary____build_ctl_pad_bin_start=_ctl_pad_bin \
	  --redefine-sym _binary____build_ctl_pad_bin_end=_ctl_pad_bin_end \
	  $< $@
../build/ctl_stick.bin: controls_stick.png $(KIT)/scripts/bmp2rgb565.py
	mkdir -p ../build
	sips -s format bmp controls_stick.png --out ../build/ctl_stick.bmp > /dev/null
	python3 $(KIT)/scripts/bmp2rgb565.py ../build/ctl_stick.bmp $@ 640 480
ctl_stick_blob.o: ../build/ctl_stick.bin
	sh-elf-objcopy -I binary -O elf32-shl -B sh4 \
	  --redefine-sym _binary____build_ctl_stick_bin_start=_ctl_stick_bin \
	  --redefine-sym _binary____build_ctl_stick_bin_end=_ctl_stick_bin_end \
	  $< $@
# Top-menu logo, already palettized+RGB565 by kit/scripts/gen_menu_assets.py
# (blob format: menu.c draw_logo comment) -- objcopy only, no conversion
# step. Gitignored (official game logo art, branded -- copyright rule,
# CLAUDE.md); regenerate with gen_menu_assets.py, which needs the gitignored
# logo.png at repo root.
logo_blob.o: logo_strip.pal8
	sh-elf-objcopy -I binary -O elf32-shl -B sh4 \
	  --redefine-sym _binary_logo_strip_pal8_start=_logo_bin \
	  --redefine-sym _binary_logo_strip_pal8_end=_logo_bin_end \
	  $< $@
../build/1ST_READ.BIN: $(TARGET)
	mkdir -p ../build
	sh-elf-objcopy -R .stack -O binary $(TARGET) $@
clean:
	rm -f $(TARGET) $(OBJS) ../build/1ST_READ.BIN ../build/bios_data.bin ../build/patch_table.h \
	  ../build/splash.bin ../build/splash.bmp \
	  ../build/ctl_pad.bin ../build/ctl_pad.bmp ../build/ctl_stick.bin ../build/ctl_stick.bmp
# splash.bin MUST die on clean: the T7 round-2 text bake edited it in place,
# and a surviving copy is "up to date" to make -- round 3 shipped the stale
# baked splash that way (operator caught it on hardware). Same reason the
# two T9 controls-page .bins are listed here too.
