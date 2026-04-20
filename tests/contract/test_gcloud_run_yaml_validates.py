"""Contract: the YAML that ``vex deploy cloud-run`` emits is at least
schema-acceptable to ``gcloud run services replace --dry-run``.

We cannot fully dry-run against a real project in CI (no credentials), so the
assertion is negative: stderr must not mention YAML schema problems. Auth /
"project does not exist" complaints are allowed through — those mean gcloud
got past the YAML parse step.

The scaffold is written to ``deploy/cloud-run.yaml`` (see
``scaffold_cloud_run`` in ``src/vex/cli.py``), NOT the ``service.yaml`` name
mentioned in the issue sketch. This test codifies the actual filename the
CLI produces.
"""

from __future__ import annotations

import re
import subprocess
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


# Patterns that would indicate gcloud actually rejected the scaffolded YAML
# (as opposed to failing for a reason we don't care about here — missing
# credentials or a non-existent project). We phrase them as fragments
# gcloud emits on real schema problems; bare "YAML" / "yaml" is too broad
# because gcloud's own usage lines mention YAML file positional args.
YAML_FAIL_SIGNALS = (
    re.compile(r"invalid\s+(?:yaml|value|spec|service|configuration)", re.IGNORECASE),
    re.compile(r"failed to parse", re.IGNORECASE),
    re.compile(r"yaml[:\s]+.*(?:error|parse|unmarshal)", re.IGNORECASE),
    re.compile(r"unmarshal", re.IGNORECASE),
    re.compile(r"unknown field", re.IGNORECASE),
    re.compile(r"schema\s+(?:error|violation)", re.IGNORECASE),
)


def test_gcloud_run_yaml_validates(tmp_workspace: Path, vex_main, gcloud_bin: str) -> None:
    project = run_vex_init(vex_main, tmp_workspace, "inference-api", "demo")

    exit_code = run_vex_in(
        vex_main, project, "deploy", "cloud-run", "--service", "test"
    )
    assert exit_code == 0, "vex deploy cloud-run (scaffold-only) should exit 0"

    yaml_path = project / "deploy" / "cloud-run.yaml"
    assert yaml_path.exists(), f"expected cloud-run scaffold at {yaml_path}"

    # --dry-run validates shape; --project dummy ensures we never accidentally
    # mutate a real project even when credentials happen to be configured.
    result = subprocess.run(
        [
            gcloud_bin,
            "run",
            "services",
            "replace",
            str(yaml_path),
            "--dry-run",
            "--project",
            "dummy",
            "--region",
            "us-central1",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=60,
    )

    combined = f"{result.stdout}\n{result.stderr}"
    matches = [p.pattern for p in YAML_FAIL_SIGNALS if p.search(combined)]
    assert not matches, (
        "gcloud reported YAML schema problems on the scaffolded cloud-run.yaml:\n"
        f"matched signals: {matches}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
