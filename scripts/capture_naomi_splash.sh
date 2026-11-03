#!/bin/sh
# NAOMI boot-splash frame capture -- ported from ../cleopatra's
# scripts/capture_naomi_splash.sh; boots the port's flat .dat image (the splash
# is BIOS-drawn, any Naomi title shows it). Emits naomi_boot_s*.png in the
# cwd; pick the full-logo frame and copy it to loader/splash.png.
#   capture_naomi_splash.sh <image.dat>
ROM="${1:?usage: capture_naomi_splash.sh <image.dat>}"
PORT="${PORT_ROOT:-$PWD}"
[ -f "$PORT/scripts/port_def.py" ] || { echo "capture_naomi_splash.sh: $PORT is not a port root (scripts/port_def.py not found; run from the port root or set PORT_ROOT)" >&2; exit 2; }
BIN="${FLYCAST_BIN:-$PORT/../flycast4naomi2dreamcast/build/Flycast.app/Contents/MacOS/Flycast}"
export FLYCAST_HEADLESS="${FLYCAST_HEADLESS:-1}"   # the fork never shows a window unless asked
PNG="${TMPDIR:-/tmp}/naomi_boot.png"
LOG="${TMPDIR:-/tmp}/naomi_boot.log"
# stale $PNG from a prior run would be re-served as "this run's frames" if
# Flycast dies before writing its first dump (cleopatra final review)
rm -f naomi_boot_s*.png "$PNG"
# kill by PID only: a name match would also kill other projects' instances
FPID=
for try in 1 2 3 4; do
  [ -n "$FPID" ] && { kill -9 "$FPID" 2>/dev/null; sleep 10; }
  FLYCAST_SHOT="$PNG" FLYCAST_SHOT_EVERY=15 \
    "$BIN" "$ROM" -config config:rend.vsync=no > "$LOG" 2>&1 &
  FPID=$!
  sleep 8
  grep -q "Verify Failed" "$LOG" && { echo "try$try flake"; continue; }
  break
done
i=0
while [ $i -lt 45 ]; do
  i=$((i+1)); sleep 1
  cp "$PNG" "naomi_boot_s$i.png" 2>/dev/null
done
kill -9 "$FPID" 2>/dev/null
md5 naomi_boot_s*.png | awk '{print $NF, $4}' | sort -k2 | uniq -f1 | sort -V
