# naomi-dc-port-kit

The game-agnostic core of the Naomi -> Dreamcast static-binary-conversion ports:
shims, loader, mastering, capture and test tooling, extracted from the
senkosp2dreamcast port so further ports can share it.

A port consumes the kit as a git submodule at `kit/`. The port's Makefiles
include the kit's `shims/rules.mk` and `loader/rules.mk`; kit scripts run from
the port root and read per-game values from the port's `scripts/port_def.py`
and `scripts/menu_def.py`.

## Contract: what a port supplies

filled in when the extraction completes (see the spec §6)
