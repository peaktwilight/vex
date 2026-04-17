"""Thin wrapper so `vex eval` can invoke the package eval harness."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

PACKAGE_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

for entry in PACKAGE_SRC.iterdir():
    if entry.is_dir() and (entry / "eval.py").exists():
        runpy.run_module(f"{entry.name}.eval", run_name="__main__")
        break
else:
    raise SystemExit("no package eval module found")
