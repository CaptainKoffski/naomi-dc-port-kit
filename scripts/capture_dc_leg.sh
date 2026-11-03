#!/bin/bash
set -euo pipefail
leg="${1:?usage: capture_dc_leg.sh <leg-name> [gdi-path]}"
port="${PORT_ROOT:-$PWD}"
[ -f "$port/scripts/port_def.py" ] || { echo "capture_dc_leg.sh: $port is not a port root (scripts/port_def.py not found; run from the port root or set PORT_ROOT)" >&2; exit 2; }
bin="${FLYCAST_BIN:-$port/../flycast4naomi2dreamcast/build/Flycast.app/Contents/MacOS/Flycast}"
gdi="${2:-$port/build/disc.gdi}"
log="$port/captures/$leg.log"
mkdir -p "$(dirname "$log")"
[ -e "$log" ] && { echo "refusing to overwrite existing $log" >&2; exit 1; }
defaults write com.flyinghead.Flycast ApplePersistenceIgnoreState -bool YES
export FLYCAST_HEADLESS="${FLYCAST_HEADLESS:-1}"   # the fork never shows a window unless asked
# exec: caller's $! is Flycast's PID -- kill that, never by name (other projects run Flycast too)
# pvr.rend=0: a leftover pvr.rend = 4 (Vulkan) in emu.cfg segfaults the fork bundle (no MoltenVK), docs/kb/tooling.md §Headless launch rule;
# extra args ("${@:3}") follow, so a caller can override.
FLYCAST_CARTLOG="$log" exec "$bin" -config config:rend.vsync=no -config config:pvr.rend=0 "${@:3}" "$gdi" \
    > "${log%.log}.stdout.log" 2>&1
