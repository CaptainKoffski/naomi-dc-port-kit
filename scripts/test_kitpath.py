# run: python3 scripts/test_kitpath.py  (from any cwd)
import os, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitpath


def refuses(f, *needles):
    try:
        f()
    except SystemExit as e:
        assert all(n in str(e) for n in needles), e
        return
    raise AssertionError("no SystemExit")


def port(tmp, body="CART_SIZE = 7\n"):
    (Path(tmp) / "scripts").mkdir()
    (Path(tmp) / "scripts" / "port_def.py").write_text(body)


def test_port_root_refuses_non_port(tmp):
    os.environ.pop("PORT_ROOT", None)
    os.chdir(tmp)
    refuses(kitpath.port_root, "port_def.py", str(Path(tmp).resolve()))


def test_port_root_env_override(tmp):
    port(tmp)
    os.environ["PORT_ROOT"] = tmp
    try:
        assert kitpath.port_root() == Path(tmp)
    finally:
        del os.environ["PORT_ROOT"]


def test_port_module_and_value(tmp):
    port(tmp)
    os.environ["PORT_ROOT"] = tmp
    try:
        m = kitpath.port_module("port_def")
        assert kitpath.port_value(m, "CART_SIZE") == 7
        refuses(lambda: kitpath.port_value(m, "NOPE"), "NOPE")
        refuses(lambda: kitpath.port_module("menu_def"), "menu_def.py")
    finally:
        del os.environ["PORT_ROOT"]


def test_cli(tmp):
    port(tmp, 'X = "v"\n')
    env = dict(os.environ, PORT_ROOT=tmp)
    cli = [sys.executable, str(Path(__file__).resolve().parent / "kitpath.py"), "port_def"]
    r = subprocess.run(cli + ["X"], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout == "v\n", r
    r = subprocess.run(cli + ["NOPE"], env=env, capture_output=True, text=True)
    assert r.returncode != 0 and "NOPE is required" in r.stderr, r


def test_kit_root():
    assert (kitpath.kit_root() / "scripts" / "kitpath.py").exists()


here = os.getcwd()
for t in (test_port_root_refuses_non_port, test_port_root_env_override, test_port_module_and_value,
          test_cli):
    with tempfile.TemporaryDirectory() as d:
        t(d)
        os.chdir(here)
test_kit_root()
print("ok")
