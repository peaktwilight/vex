"""Contract: ``vex deploy modal`` writes a ``deploy/modal_app.py`` that
``ast.parse`` accepts.

We deliberately do not try to fully import the file: the generated module
imports ``modal`` at top level, which triggers a login / token check when the
package is actually imported. ``ast.parse`` is a sufficient syntax contract.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import pytest
except ImportError:  # pragma: no cover - unit-only CI job without pytest
    pytest = None  # type: ignore[assignment]

from _helpers import RUN_CONTRACT_REASON, VEX_RUN_CONTRACT, run_vex_in, run_vex_init  # noqa: E402

if pytest is not None:
    pytestmark = [
        pytest.mark.contract,
        pytest.mark.skipif(not VEX_RUN_CONTRACT, reason=RUN_CONTRACT_REASON),
    ]


def test_modal_app_imports(tmp_workspace: Path, vex_main) -> None:
    project = run_vex_init(vex_main, tmp_workspace, "agent", "demo")

    exit_code = run_vex_in(vex_main, project, "deploy", "modal", "--app-name", "test")
    assert exit_code == 0, "vex deploy modal (scaffold-only mode) should exit 0"

    modal_app = project / "deploy" / "modal_app.py"
    assert modal_app.exists(), f"expected modal scaffold at {modal_app}"

    source = modal_app.read_text(encoding="utf-8")
    # ast.parse is enough — the real modal SDK needs credentials to actually
    # import, and we intentionally don't require a Modal login here.
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.Import) and any(alias.name == "modal" for alias in node.names)
        for node in ast.walk(tree)
    ), "scaffold should `import modal`"

    # Sanity: the app name we requested flowed through.
    assert 'name="test"' in source, "--app-name test should be embedded as modal.App(name=...)"
