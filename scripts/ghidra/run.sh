#!/bin/sh
# Re-runnable Ghidra headless harness for the boot-binary analysis.
# Run from the port root (or set PORT_ROOT). Usage:
#   kit/scripts/ghidra/run.sh import              # import tools/boot.bin + full auto-analysis
#   kit/scripts/ghidra/run.sh script NAME.java [args...]
# Scripts are found in the kit's scripts/ghidra and the port's scripts/ghidra.
# Project name: $GHIDRA_PROJECT, else port_def.GHIDRA_PROJECT (required).
# ROM content: tools/boot.bin and tools/ghidra-proj are gitignored (/tools/). Never commit.
set -e
KIT="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${PORT_ROOT:-$PWD}"
[ -f "$PORT/scripts/port_def.py" ] || { echo "run.sh: $PORT is not a port root (scripts/port_def.py not found; run from the port root or set PORT_ROOT)" >&2; exit 2; }
GHIDRA_HOME="${GHIDRA_HOME:-$PORT/tools/ghidra_12.1.2_PUBLIC}"
PROJ="$PORT/tools/ghidra-proj"
NAME="${GHIDRA_PROJECT:-$(python3 "$KIT/scripts/kitpath.py" port_def GHIDRA_PROJECT)}"
BOOT="$PORT/tools/boot.bin"
HL="$GHIDRA_HOME/support/analyzeHeadless"

# openjdk from brew (see docs/kb/tooling.md §Ghidra) — Java 21+.
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"

[ -x "$HL" ] || { echo "ERROR: analyzeHeadless not found: $HL" >&2; exit 1; }
[ -f "$BOOT" ] || { echo "ERROR: boot slice missing: $BOOT  (head -c <boot-slice length from the port's KB> <the port's .dat> > tools/boot.bin)" >&2; exit 1; }
mkdir -p "$PROJ"

case "${1:-}" in
  import)
    # No -noanalysis => full SH-4 auto-analysis (follows jmp @rN via literal pools).
    "$HL" "$PROJ" "$NAME" -import "$BOOT" -overwrite \
      -processor "SuperH4:LE:32:default" \
      -loader BinaryLoader -loader-baseAddr 0x8c020000
    ;;
  script)
    [ -n "${2:-}" ] || { echo "usage: $0 script NAME.java [args...]" >&2; exit 1; }
    SCRIPT="$2"; shift 2
    # Ghidra separates -scriptPath entries with ';' (support/analyzeHeadlessREADME.md:203)
    "$HL" "$PROJ" "$NAME" -process boot.bin -noanalysis \
      -scriptPath "$KIT/scripts/ghidra;$PORT/scripts/ghidra" -postScript "$SCRIPT" "$@"
    ;;
  *) echo "usage: $0 import | script NAME.java [args...]" >&2; exit 1 ;;
esac
