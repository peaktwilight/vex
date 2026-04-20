"""Shared fixtures and markers for the contract test suite.

Contract tests verify that vex's argv is still accepted by the real external
tools it shells out to (``docker``, ``gcloud``, ``modal``, ``uvx`` + registry
tools). They are expensive relative to the unit suite: each test spins up a
fresh scaffold, pulls at least one image, or resolves a uvx tool tree.

Contract tests are opt-in in both directions:

* The ``contract`` pytest marker is registered in ``pyproject.toml``;
  ``addopts`` excludes it from the default ``pytest tests/`` run.
* Every test is additionally decorated with
  ``@pytest.mark.skipif(not os.environ.get("VEX_RUN_CONTRACT"))`` so a
  stray ``pytest -m contract`` run without the env var still skips
  cleanly.

Shared helpers live in :mod:`tests.contract._helpers` because pytest
conftest modules are not importable as regular Python modules.

Select the suite with either::

    VEX_RUN_CONTRACT=1 pytest tests/contract -m contract
    VEX_RUN_CONTRACT=1 uv run pytest tests/contract -m contract -v
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Iterator

import pytest

# Ensure ``tests/contract/`` is on sys.path so test modules (and this
# conftest) can ``from _helpers import ...`` without needing a package
# ``__init__.py`` gymnastics. pytest's rootdir/importmode handling does not
# inject the conftest's directory onto sys.path by default.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _helpers import RUN_CONTRACT_REASON, VEX_RUN_CONTRACT  # type: ignore[import-not-found]  # noqa: E402


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Iterator[Path]:
    """Yield an isolated tempdir to run scaffold/deploy commands in."""
    yield tmp_path


@pytest.fixture
def vex_main():
    """Return the ``vex.cli.main`` entry point.

    Imported lazily so the contract suite can still be collected in an
    environment where ``vex`` isn't installed (collection runs even for
    skipped tests).
    """
    from vex.cli import main

    return main


def _require_binary(name: str) -> None:
    if shutil.which(name) is None:
        pytest.skip(f"{name!r} not on PATH; contract test requires it")


@pytest.fixture
def docker_bin() -> str:
    _require_binary("docker")
    return "docker"


@pytest.fixture
def gcloud_bin() -> str:
    _require_binary("gcloud")
    return "gcloud"


@pytest.fixture
def uvx_bin() -> str:
    _require_binary("uvx")
    return "uvx"


def pytest_collection_modifyitems(config, items) -> None:  # noqa: ARG001
    """Auto-skip ``@pytest.mark.contract`` items when ``VEX_RUN_CONTRACT`` is unset.

    Each test also carries its own ``@pytest.mark.skipif`` (belt-and-braces in
    case somebody imports the test module directly), but adding the skip here
    means a plain ``pytest -m contract`` run without the env var surfaces a
    single, readable skip reason instead of per-test clutter.
    """
    if VEX_RUN_CONTRACT:
        return
    skip_marker = pytest.mark.skip(reason=RUN_CONTRACT_REASON)
    for item in items:
        if "contract" in item.keywords:
            item.add_marker(skip_marker)
