"""Contract: the argv that ``vex run --sandbox`` emits is accepted by a real
docker engine against ``python:3.12-slim``.

The unit suite already tests ``build_sandbox_argv`` in isolation. This test
takes the extra step of piping the resolved argv through ``docker run`` so
we catch things like image-tag drift, flag incompatibilities with the
installed docker version, or a policy default that docker refuses.

Pre-conditions (enforced by the workflow):

* ``python:3.12-slim`` is pre-pulled (the policy default image)
* ``docker`` is on PATH
* We're running inside ``tmp_workspace`` with a scaffolded project so
  ``vex run`` can resolve ``project_root()`` and load its policy.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import pytest
except ImportError:  # pragma: no cover - unit-only CI job without pytest
    pytest = None  # type: ignore[assignment]

from _helpers import RUN_CONTRACT_REASON, VEX_RUN_CONTRACT, run_vex_init  # noqa: E402

if pytest is not None:
    pytestmark = [
        pytest.mark.contract,
        pytest.mark.skipif(not VEX_RUN_CONTRACT, reason=RUN_CONTRACT_REASON),
    ]


def test_sandbox_argv_against_real_docker(
    tmp_workspace: Path, vex_main, docker_bin: str
) -> None:
    project = run_vex_init(vex_main, tmp_workspace, "inference-api", "demo")

    # Shell out rather than calling main() in-process: handle_run resolves
    # project_root() via os.getcwd(), and subprocess gives us clean stdout
    # capture without fighting pytest's capture layer.
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(Path(__file__).resolve().parents[2] / "src")
        + os.pathsep
        + env.get("PYTHONPATH", "")
    )
    result = subprocess.run(
        [sys.executable, "-m", "vex", "run", "--sandbox", "echo contract-test"],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=180,
        env=env,
    )

    assert result.returncode == 0, (
        "vex run --sandbox failed against real docker:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert "contract-test" in result.stdout, (
        "expected sandboxed command to print 'contract-test' on stdout:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
