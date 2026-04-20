"""Contract: ``uvx --from inspect-ai inspect --help`` resolves and surfaces
the ``eval`` subcommand.

This is the minimum contract `vex eval --adapter inspect` relies on — the
Inspect AI adapter shells out to ``uvx --from inspect-ai inspect eval ...``.
If PyPI drops the package or the entry-point name changes, this guard
catches it before a real evaluation run does.
"""

from __future__ import annotations

import subprocess

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import pytest
except ImportError:  # pragma: no cover - unit-only CI job without pytest
    pytest = None  # type: ignore[assignment]

from _helpers import RUN_CONTRACT_REASON, VEX_RUN_CONTRACT  # noqa: E402

if pytest is not None:
    pytestmark = [
        pytest.mark.contract,
        pytest.mark.skipif(not VEX_RUN_CONTRACT, reason=RUN_CONTRACT_REASON),
    ]


def test_uvx_inspect_ai_resolves(uvx_bin: str) -> None:
    result = subprocess.run(
        [uvx_bin, "--from", "inspect-ai", "inspect", "--help"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "uvx --from inspect-ai inspect --help failed to resolve:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert "eval" in result.stdout, (
        "inspect --help stdout did not mention `eval` subcommand:\n"
        f"{result.stdout}"
    )
