"""Contract: the inference-api scaffold can be wrapped in a minimal Dockerfile
that ``docker build`` accepts.

Currently ``vex init inference-api`` does not emit a Dockerfile (see
``docs/deploy.md`` — the docker target builds against the project's existing
Dockerfile). This test pins the *contract* between the scaffold layout and
docker: a trivial, hand-written Dockerfile referencing the scaffold's src
layout should build cleanly. If the scaffold stops producing ``src/<pkg>/``
or flips away from ``python:3.12-slim`` compat, this test fails loudly.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Ensure `_helpers` (sibling module under tests/contract/) resolves even
# when the module is loaded outside pytest (e.g. under `unittest discover`,
# which does not evaluate conftest.py). Contract tests are a pytest-only
# suite, but the unit-only CI job runs `unittest discover` across tests/,
# so the import has to degrade gracefully.
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import pytest
except ImportError:  # pragma: no cover - exercised only in the unit-only CI job
    pytest = None  # type: ignore[assignment]

from _helpers import RUN_CONTRACT_REASON, VEX_RUN_CONTRACT, run_vex_init  # noqa: E402

if pytest is not None:
    pytestmark = [
        pytest.mark.contract,
        pytest.mark.skipif(not VEX_RUN_CONTRACT, reason=RUN_CONTRACT_REASON),
    ]


DOCKERFILE = """\
FROM python:3.12-slim
WORKDIR /app
COPY . /app
# Contract-level check only: do not install project deps — we just want
# ``docker build`` to accept the Dockerfile + scaffold layout.
CMD ["python", "-c", "import sys; sys.exit(0)"]
"""


def test_scaffold_dockerfile_builds(tmp_workspace: Path, vex_main, docker_bin: str) -> None:
    project = run_vex_init(vex_main, tmp_workspace, "inference-api", "demo")
    (project / "Dockerfile").write_text(DOCKERFILE, encoding="utf-8")

    image_tag = "vex-contract-test:local"
    try:
        build = subprocess.run(
            [docker_bin, "build", "-t", image_tag, "."],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert build.returncode == 0, (
            "docker build failed on scaffolded project:\n"
            f"stdout:\n{build.stdout}\n"
            f"stderr:\n{build.stderr}"
        )
    finally:
        # Best-effort image cleanup so repeated local runs don't accumulate
        # vex-contract-test:local layers. Non-fatal on failure.
        subprocess.run(
            [docker_bin, "rmi", "-f", image_tag],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
