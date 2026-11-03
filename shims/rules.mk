# Shim build rules, included from the port's shims/Makefile (cwd = <port>/shims).
# The port sets, before the include: KIT, SRCS (ordered link list -- shim.ld
# concatenates .text* in input order, so the order IS the binary), INC (-I
# flags), DEFS; B (default build) optional.
CC = /opt/toolchains/dc/sh-elf/bin/sh-elf-gcc
NM = /opt/toolchains/dc/sh-elf/bin/sh-elf-nm
OBJCOPY = /opt/toolchains/dc/sh-elf/bin/sh-elf-objcopy
CFLAGS = -ml -m4-single-only -ffreestanding -nostdlib -Os -Wall -Wextra -fno-tree-loop-distribute-patterns $(INC)
CFLAGS += $(DEFS)   # debug toggles, e.g. make DEFS='-DSHIM_SERIAL=1 -DSHIM_TRACE=1'
B ?= build

.PHONY: all shim-tests clean
# Pin the default goal: a rule the port defines ahead of its own targets (e.g.
# a conditional decoder-object rule) would otherwise BE the default goal and a
# bare `make -C shims` would stop after that object.
.DEFAULT_GOAL := all
all: $(B)/shim.bin $(B)/shim.map

shim-tests:
	mkdir -p $(B)
	cc $(INC) -o $(B)/test_iface $(KIT)/shims/test/test_shim_iface.c && $(B)/test_iface
	# gd.c compiles its MMIO half out under HOST_TEST -- the test links the real
	# gd_plan the shim runs, so a divergence is a link/assert failure, not a copy.
	cc -DHOST_TEST $(INC) -o $(B)/test_gd_math $(KIT)/shims/test/test_gd_math.c $(KIT)/shims/src/gd.c && $(B)/test_gd_math

$(B)/shim.elf: $(SRCS) $(KIT)/shims/shim.ld
	mkdir -p $(B)
	$(CC) $(CFLAGS) -Wl,-T,$(KIT)/shims/shim.ld -Wl,-Map,$(B)/shim.map.tmp -o $@ $(SRCS)
$(B)/shim.bin: $(B)/shim.elf
	$(OBJCOPY) -O binary $< $@
$(B)/shim.map: $(B)/shim.elf
	$(NM) $< > $@
clean:
	rm -rf $(B)
