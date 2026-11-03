#!/bin/bash
# Naomi-profile capture-leg launcher: one leg = one instrumented run -> captures/<leg>.log
# Launch gotchas per docs/kb/tooling.md §"Instrumented Flycast".
set -euo pipefail
leg="${1:?usage: capture_leg.sh <leg-name> <rom-path>}"
rom="${2:?usage: capture_leg.sh <leg-name> <rom-path>}"
kit="$(cd "$(dirname "$0")/.." && pwd)"
port="${PORT_ROOT:-$PWD}"
[ -f "$port/scripts/port_def.py" ] || { echo "capture_leg.sh: $port is not a port root (scripts/port_def.py not found; run from the port root or set PORT_ROOT)" >&2; exit 2; }
bin="${FLYCAST_BIN:-$port/../flycast4naomi2dreamcast/build/Flycast.app/Contents/MacOS/Flycast}"
# the game's boot entry (port_def.ENTRY_PC) arms the BIOSEXEC watch; an exported override wins (canary use)
FLYCAST_ENTRYPC="${FLYCAST_ENTRYPC:-$(python3 "$kit/scripts/kitpath.py" port_def ENTRY_PC)}"
log="$port/captures/$leg.log"
mkdir -p "$(dirname "$log")"
# ponytail: legs are primary data — never clobber; rename/delete a bad leg by hand
[ -e "$log" ] && { echo "refusing to overwrite existing $log" >&2; exit 1; }
defaults write com.flyinghead.Flycast ApplePersistenceIgnoreState -bool YES
export FLYCAST_HEADLESS="${FLYCAST_HEADLESS:-1}"   # the fork never shows a window unless asked
# exec: caller's $! is Flycast's PID -- kill that, never by name (other projects run Flycast too)
# pvr.rend=0: a leftover pvr.rend = 4 (Vulkan) in emu.cfg segfaults the fork bundle (no MoltenVK), docs/kb/tooling.md §Headless launch rule
FLYCAST_ENTRYPC="$FLYCAST_ENTRYPC" FLYCAST_CARTLOG="$log" \
    exec "$bin" -config config:rend.vsync=no -config config:pvr.rend=0 "$rom"
