"""
Build a watchface end to end:

    python tools/build.py Retro            # assets + zeus build + flat zip
    python tools/build.py Retro --assets   # only regenerate assets/previews

Steps:
  1. <Face>/design.py      draws assets, previews, writes the layout block
  2. zeus build            -> <Face>/dist/*.zab   (Zepp app / zeus preview)
  3. zepp.package          -> <Face>/dist/<appName>.zip (ZeppOS Player, AmazFaces)
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from zepp.package import package  # noqa: E402


def zeus_cmd():
    local = os.path.join(REPO, "node_modules", ".bin",
                         "zeus.cmd" if os.name == "nt" else "zeus")
    if os.path.exists(local):
        return local
    found = shutil.which("zeus")
    if not found:
        raise SystemExit("zeus not found - run `npm install` in the repo root")
    return found


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    face = os.path.abspath(os.path.join(REPO, args[0]))
    design = os.path.join(face, "design.py")
    if not os.path.exists(design):
        raise SystemExit(f"{design} not found")

    subprocess.run([sys.executable, design], check=True)
    if "--assets" in sys.argv:
        return

    dist = os.path.join(face, "dist")
    shutil.rmtree(dist, ignore_errors=True)
    subprocess.run([zeus_cmd(), "build"], cwd=face, check=True)
    print("wrote", package(face))


if __name__ == "__main__":
    main()
