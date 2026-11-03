"""Locate the kit and the consuming port; load the port's per-game modules.

CLI (for shell scripts and Makefiles): kitpath.py <module> <NAME> prints
port_value(port_module(module), NAME), or exits naming what is missing."""
import importlib.util
import os
from pathlib import Path


def kit_root():
    return Path(__file__).resolve().parent.parent


def port_root():
    root = Path(os.environ.get("PORT_ROOT") or Path.cwd())
    if not (root / "scripts" / "port_def.py").is_file():
        raise SystemExit(f"kitpath: {root} is not a port root: scripts/port_def.py not found "
                         "(run from the port root or set PORT_ROOT)")
    return root


def port_module(name):
    path = port_root() / "scripts" / f"{name}.py"
    if not path.is_file():
        raise SystemExit(f"kitpath: {path} not found")
    spec = importlib.util.spec_from_file_location(f"port_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def port_value(module, name):
    if not hasattr(module, name):
        raise SystemExit(f"{module.__file__}: {name} is required")
    return getattr(module, name)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: kitpath.py <module> <NAME>")
    print(port_value(port_module(sys.argv[1]), sys.argv[2]))
