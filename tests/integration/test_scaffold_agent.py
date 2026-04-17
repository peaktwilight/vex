"""End-to-end scaffold integration test.

This test does the full happy-path a user would run after installing vex:

    $ vex init agent demo
    $ uv sync --extra agent --python 3.12
    $ python -c "from demo.agent import build_agent; ..."

It is deliberately an *integration* test: it does NOT mock subprocess or uv.
Because it really shells out to ``uv`` and resolves the scaffolded project's
dependency tree, it is gated behind the ``integration`` pytest marker and
skipped by default. Select it explicitly with:

    pytest tests/integration -m integration
    # or
    VEX_RUN_INTEGRATION=1 pytest tests/integration -m integration
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import pytest
except ImportError:  # pragma: no cover - unit suite runs without pytest installed
    pytest = None  # type: ignore[assignment]

from vex.cli import main


def _integration_marker(cls: type) -> type:
    """Apply ``@pytest.mark.integration`` when pytest is available.

    Under ``python -m unittest discover -s tests`` pytest may not be installed
    (the unit job doesn't install the dev extras). In that case we skip the
    decorator entirely and rely on :data:`RUN_INTEGRATION` to gate execution.
    """

    if pytest is None:
        return cls
    return pytest.mark.integration(cls)


RUN_INTEGRATION = os.environ.get("VEX_RUN_INTEGRATION") == "1"


@_integration_marker
@unittest.skipUnless(
    RUN_INTEGRATION,
    "integration test opt-in only: set VEX_RUN_INTEGRATION=1 or run with `pytest -m integration`",
)
class ScaffoldAgentIntegrationTests(unittest.TestCase):
    """Verify `vex init agent demo` produces a project that actually syncs and imports."""

    def test_scaffold_syncs_and_build_agent_is_importable(self) -> None:
        if shutil.which("uv") is None:
            self.skipTest("uv binary not found on PATH")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "demo"

            # 1. Scaffold the agent template via the real CLI entrypoint.
            original_cwd = Path.cwd()
            try:
                os.chdir(tmp_path)
                exit_code = main(["init", "agent", "demo"])
            finally:
                os.chdir(original_cwd)

            self.assertEqual(exit_code, 0, "vex init agent demo should succeed")
            self.assertTrue(
                (project / "src" / "demo" / "agent.py").exists(),
                "scaffold must produce src/demo/agent.py",
            )

            # 2. Materialize the project's venv with the agent extra.
            sync = subprocess.run(
                ["uv", "sync", "--extra", "agent", "--python", "3.12"],
                cwd=project,
                capture_output=True,
                text=True,
                timeout=360,
            )
            self.assertEqual(
                sync.returncode,
                0,
                f"uv sync failed:\nstdout:\n{sync.stdout}\nstderr:\n{sync.stderr}",
            )

            venv_python = project / ".venv" / "bin" / "python"
            self.assertTrue(
                venv_python.exists(),
                f"expected venv python at {venv_python}, uv sync output:\n"
                f"{sync.stdout}\n{sync.stderr}",
            )

            # 3. Import the scaffolded agent inside the venv and swap in a
            #    PydanticAI TestModel so the call graph is exercised without
            #    touching a real LLM.
            snippet = (
                "from pydantic_ai.models.test import TestModel;"
                "from demo.agent import build_agent;"
                "agent = build_agent();"
                "agent.override(model=TestModel());"
                "print('ok')"
            )
            result = subprocess.run(
                [str(venv_python), "-c", snippet],
                cwd=project,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"import/override failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )
            self.assertIn("ok", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    # Allow `python tests/integration/test_scaffold_agent.py` as a manual run,
    # but do not invoke the integration path under a plain unittest discovery
    # run by default - require the env var to opt in.
    if not RUN_INTEGRATION:
        print("set VEX_RUN_INTEGRATION=1 to run this test", file=sys.stderr)
        sys.exit(0)
    unittest.main()
