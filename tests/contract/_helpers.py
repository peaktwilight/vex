"""Shared helpers for the contract test suite.

Kept out of ``conftest.py`` because pytest's conftest files are not
importable as regular modules (they are loaded by the pytest plugin system
with a synthetic module name).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable


VEX_RUN_CONTRACT = os.environ.get("VEX_RUN_CONTRACT") == "1"

RUN_CONTRACT_REASON = (
    "contract tests opt-in only: set VEX_RUN_CONTRACT=1 "
    "(and ensure docker / gcloud / uvx are on PATH)"
)


def run_vex_init(
    main: Callable[[list[str]], int],
    tmp: Path,
    template: str,
    project: str = "demo",
) -> Path:
    """Run ``vex init <template> <project>`` inside ``tmp`` and return the path."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp)
        exit_code = main(["init", template, project])
    finally:
        os.chdir(original_cwd)
    assert exit_code == 0, f"vex init {template} {project} failed with exit={exit_code}"
    project_path = tmp / project
    assert project_path.exists(), f"scaffold did not create {project_path}"
    return project_path


def run_vex_in(
    main: Callable[[list[str]], int],
    cwd: Path,
    *argv: str,
) -> int:
    """Run ``vex <argv...>`` with ``cwd`` as the working directory."""
    original_cwd = Path.cwd()
    try:
        os.chdir(cwd)
        return main(list(argv))
    finally:
        os.chdir(original_cwd)
