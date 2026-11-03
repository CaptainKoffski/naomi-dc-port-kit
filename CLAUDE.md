# naomi-dc-port-kit

The game-agnostic core of the Naomi -> Dreamcast static-binary-conversion ports:
shims, loader, mastering, capture and test tooling. A port consumes it as a git
submodule at `kit/`.

- **Spec:** `docs/superpowers/specs/2026-11-03-port-kit-extraction-design.md`
- **Plan:** `docs/superpowers/plans/2026-11-03-port-kit-extraction.md`
- **Contract** (what a port supplies): `README.md`. **Tool pins:**
  `docs/kb/tooling.md`. **Status:** `docs/kb/00-status.md`.
- **Citations:** unqualified citations in kit sources (`docs/kb/...`,
  `task-N-brief.md`, phase documents, `loader/main.c`, `shims/src/main.c`)
  refer to the reference port's tree, `../senkosp2dreamcast` at commit
  `afab584`, the base the kit was extracted from.

Rules:
- Every hardware/behavioral claim carries a citation; primary sources
  (emulator/kernel/library source) outrank wikis.
- Record every tool install in `docs/kb/tooling.md` (version, flags, exact steps).
- Never commit or upload copyrighted bytes: ROMs, BIOS, disc images, donor
  tracks, game-derived data, including test fixtures.
- Always launch the Flycast fork (`../flycast4naomi2dreamcast`) with
  `FLYCAST_HEADLESS=1`.
- The kit never names a game: every per-game value comes from the port, with no
  fallback.
- Gate: senkosp (`../senkosp2dreamcast`) rebuilt against the kit must produce
  byte-identical `shim.bin`, `1ST_READ.BIN` and disc tracks
  (`scripts/gate_hashes.sh check gd` / `check cd` in senkosp).

Consumers: `../senkosp2dreamcast` (worked example, first consumer),
`../ausfache2dreamcast` (next).
