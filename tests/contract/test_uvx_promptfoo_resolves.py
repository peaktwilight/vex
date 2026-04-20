"""Contract: ``uvx promptfoo --help`` resolves.

`vex eval --adapter promptfoo` shells out to ``uvx promptfoo eval ...``;
this test guards the resolve path (tool name, PyPI availability) without
executing an actual eval.
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


def test_uvx_promptfoo_resolves(uvx_bin: str) -> None:
    result = subprocess.run(
        [uvx_bin, "promptfoo", "--help"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "uvx promptfoo --help failed to resolve:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
