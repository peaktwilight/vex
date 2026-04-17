from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vex.cli import main


class CliTests(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(argv)
        return code, buffer.getvalue()

    def test_help_without_args(self) -> None:
        code, output = self.run_cli([])
        self.assertEqual(code, 0)
        self.assertIn("AI-native workflow tool for Python apps.", output)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_dev_command_uses_script_alias(self, run_command: object, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text(
                "[tool.vex.scripts]\n"
                'dev = "python -m http.server"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["dev", "--bind", "127.0.0.1"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        run_command.assert_called_once_with(
            ["uv", "run", "sh", "-c", "python -m http.server --bind 127.0.0.1"],
            cwd=None,
        )

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_add_command_delegates_to_uv(self, run_command: object, _uv_bin: object) -> None:
        code, _output = self.run_cli(["add", "fastapi", "pydantic", "--dev"])
        self.assertEqual(code, 0)
        run_command.assert_called_once_with(["uv", "add", "--dev", "fastapi", "pydantic"], cwd=None)

    def test_run_requires_command(self) -> None:
        code, output = self.run_cli(["run"])
        self.assertEqual(code, 2)
        self.assertIn("requires a command", output)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_python_install_command(self, run_command: object, _uv_bin: object) -> None:
        code, _output = self.run_cli(["python", "install", "3.12"])
        self.assertEqual(code, 0)
        run_command.assert_called_once_with(["uv", "python", "install", "3.12"], cwd=None)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_python_path_uses_uv_find(self, run_command: object, _uv_bin: object) -> None:
        code, _output = self.run_cli(["python", "path"])
        self.assertEqual(code, 0)
        run_command.assert_called_once_with(["uv", "python", "find"], cwd=None)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_run_resolves_vex_script_alias(self, run_command: object, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text(
                "[tool.vex.scripts]\n"
                'dev = "python -m http.server"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["run", "dev", "--bind", "127.0.0.1"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        run_command.assert_called_once_with(
            ["uv", "run", "sh", "-c", "python -m http.server --bind 127.0.0.1"],
            cwd=None,
        )

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_test_command_uses_script_alias(self, run_command: object, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text(
                "[tool.vex.scripts]\n"
                'test = "python -m unittest discover -s tests"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["test", "-k", "cli"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        run_command.assert_called_once_with(
            ["uv", "run", "sh", "-c", "python -m unittest discover -s tests -k cli"],
            cwd=None,
        )

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_lint_command_falls_back_to_ruff(self, run_command: object, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["lint", "src"])
            finally:
                os.chdir(original_cwd)
        self.assertEqual(code, 0)
        run_command.assert_called_once_with(
            ["uv", "run", "--with", "ruff", "ruff", "check", ".", "src"],
            cwd=None,
        )

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command")
    def test_init_appends_vex_config(self, run_command: object, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            def fake_run(argv: list[str], cwd: object = None) -> int:
                target = Path(temp_dir) / "demo"
                target.mkdir()
                (target / "pyproject.toml").write_text(
                    "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n",
                    encoding="utf-8",
                )
                return 0

            run_command.side_effect = fake_run
            try:
                code, _output = self.run_cli(["init", "demo", "--app"])
            finally:
                os.chdir(original_cwd)

            pyproject_text = (Path(temp_dir) / "demo" / "pyproject.toml").read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn("[tool.vex]", pyproject_text)
        self.assertIn("package-mode = false", pyproject_text)
        self.assertIn('test = "pytest"', pyproject_text)
        self.assertIn('lint = "ruff check ."', pyproject_text)
        self.assertIn('format = "ruff format ."', pyproject_text)
        self.assertIn('typecheck = "mypy ."', pyproject_text)
        self.assertIn('dev = "python -m http.server 8000"', pyproject_text)
        self.assertIn('benchmark = "python -m timeit -n 1000 -r 5 \'1+1\'"', pyproject_text)
        self.assertIn('eval = "python -m pytest -q"', pyproject_text)

    def test_init_agent_creates_template_files(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["init", "agent", "support-agent"])
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "support-agent"
            pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
            has_main = (root / "src" / "support_agent" / "main.py").exists()
            has_eval = (root / "src" / "support_agent" / "eval.py").exists()
            has_prompt = (root / "prompts" / "system.md").exists()
            has_dataset = (root / "evals" / "datasets" / ".gitkeep").exists()
            has_cases = (root / "evals" / "datasets" / "cases.jsonl").exists()
            has_eval_runner = (root / "evals" / "run_eval.py").exists()
            has_deploy_targets = (root / "deploy.targets.toml").exists()

        self.assertEqual(code, 0)
        self.assertIn('template = "agent"', pyproject_text)
        self.assertIn('dev = "python -m support_agent.main"', pyproject_text)
        self.assertIn('benchmark = "python -m support_agent.benchmark"', pyproject_text)
        self.assertIn('eval = "python evals/run_eval.py --input {input}"', pyproject_text)
        self.assertIn('[project.optional-dependencies]', pyproject_text)
        self.assertIn('"pydantic-ai>=0.0.0"', pyproject_text)
        self.assertTrue(has_deploy_targets)
        self.assertTrue(has_main)
        self.assertTrue(has_eval)
        self.assertTrue(has_prompt)
        self.assertTrue(has_dataset)
        self.assertTrue(has_cases)
        self.assertTrue(has_eval_runner)

    def test_init_inference_api_creates_template_files(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["init", "inference-api", "inference-service"])
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "inference-service"
            pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
            has_api = (root / "src" / "inference_service" / "api.py").exists()
            has_eval = (root / "src" / "inference_service" / "eval.py").exists()
            has_cases = (root / "evals" / "datasets" / "cases.jsonl").exists()
            has_eval_runner = (root / "evals" / "run_eval.py").exists()
            has_deploy_targets = (root / "deploy.targets.toml").exists()

        self.assertEqual(code, 0)
        self.assertIn('template = "inference-api"', pyproject_text)
        self.assertIn('dev = "python -m inference_service.api"', pyproject_text)
        self.assertIn('eval = "python evals/run_eval.py --input {input}"', pyproject_text)
        self.assertIn('"fastapi>=0.111"', pyproject_text)
        self.assertTrue(has_deploy_targets)
        self.assertTrue(has_api)
        self.assertTrue(has_eval)
        self.assertTrue(has_cases)
        self.assertTrue(has_eval_runner)

    def test_init_rejects_two_paths_without_template(self) -> None:
        code, output = self.run_cli(["init", "foo", "bar"])
        self.assertEqual(code, 2)
        self.assertIn("accepts only one path", output)

    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_reports_healthy_project(self, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.env]\npath = \".venv\"\n\n"
                "[tool.vex.scripts]\n"
                'test = "pytest"\n',
                encoding="utf-8",
            )
            (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
            (root / ".venv").mkdir()
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["doctor"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        self.assertIn("OK  uv found", output)
        self.assertIn("OK  found [tool.vex] configuration", output)
        self.assertIn("OK  found uv.lock", output)

    @patch("vex.cli.uv_bin", return_value=None)
    def test_doctor_reports_missing_setup(self, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["doctor"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 1)
        self.assertIn("ERR uv not found", output)
        self.assertIn("ERR missing pyproject.toml", output)

    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_reports_missing_ai_setup(self, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.env]\npath = \".venv\"\n\n"
                "[tool.vex.scripts]\n"
                'test = "pytest"\n',
                encoding="utf-8",
            )
            (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
            (root / ".venv").mkdir()
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["doctor", "ai"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 1)
        self.assertIn("WARN missing AI workflow script 'dev'", output)
        self.assertIn("WARN missing AI workflow script 'eval'", output)
        self.assertIn("WARN missing [tool.vex.policy] configuration", output)

    @patch("vex.cli.sandbox_backend", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_reports_healthy_setup(self, _uv_bin: object, _sandbox_backend: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runtime_root = root / "engine" / "vex-ai-runtime"
            (runtime_root / "schemas").mkdir(parents=True)
            (runtime_root / "schemas" / "vex-model-schema.json").write_text(
                '{"schema":"vex-model/v1","schema_version":"v1","runtime":"vex-ai-runtime","engine":"onnxruntime"}\n',
                encoding="utf-8",
            )
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.env]\npath = \".venv\"\n\n"
                "[tool.vex.scripts]\n"
                'dev = "python -m demo.main"\n'
                'benchmark = "python -m demo.benchmark"\n'
                'eval = "python evals/run_eval.py --input {input}"\n'
                'test = "pytest"\n\n'
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'network = "deny"\n',
                encoding="utf-8",
            )
            (root / "deploy.targets.toml").write_text(
                "[profiles.default]\n"
                'image = "ghcr.io/example/demo"\n',
                encoding="utf-8",
            )
            (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
            (root / ".venv").mkdir()
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["doctor", "ai"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        self.assertIn("OK  found AI workflow script 'dev'", output)
        self.assertIn("OK  found AI workflow script 'benchmark'", output)
        self.assertIn("OK  found AI workflow script 'eval'", output)
        self.assertIn("OK  found deploy.targets.toml with default profile", output)
        self.assertIn("OK  runtime path resolved to", output)
        self.assertIn("OK  found shared model schema in runtime", output)
        self.assertIn("OK  sandbox backend detected: docker", output)

    def test_policy_prints_config(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex.policy]\n"
                'network = "deny"\n'
                "sandbox = true\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["policy"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        self.assertIn("network = deny", output)
        self.assertIn("sandbox = True", output)

    def test_policy_set_get_unset_roundtrip(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text("[tool.vex]\nmanaged = true\n", encoding="utf-8")
            os.chdir(temp_dir)
            try:
                set_code, set_output = self.run_cli(["policy", "set", "network", "allow", "--type", "str"])
                get_code, get_output = self.run_cli(["policy", "get", "network"])
                unset_code, unset_output = self.run_cli(["policy", "unset", "network"])
            finally:
                os.chdir(original_cwd)

            override_path = root / ".vex" / "policy.json"
            override = json.loads(override_path.read_text(encoding="utf-8"))

        self.assertEqual(set_code, 0)
        self.assertIn("Set policy override network=allow", set_output)
        self.assertEqual(get_code, 0)
        self.assertIn("allow", get_output)
        self.assertEqual(unset_code, 0)
        self.assertIn("Unset policy override network", unset_output)
        self.assertNotIn("network", override)

    @patch("vex.cli.run_command", return_value=0)
    def test_run_sandbox_uses_unsafe_fallback_when_enabled(self, run_command: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                "unsafe_fallback = true\n"
                'sandbox_backend = "none"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["run", "--sandbox", "echo", "hello"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        self.assertIn("unsafe local execution", output)
        run_command.assert_called_once_with(["sh", "-c", "echo hello"], cwd=root.resolve())

    @patch("vex.cli.run_command", return_value=0)
    def test_run_sandbox_preserves_single_quoted_shell_string(self, run_command: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                "unsafe_fallback = true\n"
                'sandbox_backend = "none"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["run", "--sandbox", "echo hi"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        run_command.assert_called_once_with(["sh", "-c", "echo hi"], cwd=root.resolve())

    def test_package_model_writes_manifest(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "model.onnx").write_bytes(b"fake-model")
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["package-model", "model.onnx", "--out-dir", "dist/model"])
            finally:
                os.chdir(original_cwd)

            manifest_path = root / "dist" / "model" / "vex-model.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("Wrote model artifact manifest", output)
        self.assertEqual(manifest["schema"], "vex-model/v1")
        self.assertEqual(manifest["schema_version"], "v1")
        self.assertEqual(manifest["runtime"], "vex-ai-runtime")
        self.assertEqual(manifest["engine"], "onnxruntime")
        self.assertEqual(manifest["model_path"], "models/model.onnx")

    @patch("vex.cli.runtime_compatibility_check", return_value=(False, "bad manifest"))
    def test_package_model_fails_on_compatibility_error(self, _compat: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "model.onnx").write_bytes(b"fake-model")
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["package-model", "model.onnx", "--out-dir", "dist/model"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 2)
        self.assertIn("bad manifest", output)

    @patch("vex.cli.schema_drift_warning", return_value="WARN schema drift detected")
    @patch("vex.cli.runtime_compatibility_check", return_value=(True, "Runtime compatibility check passed"))
    def test_package_model_prints_schema_drift_warning(self, _compat: object, _drift: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "model.onnx").write_bytes(b"fake-model")
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["package-model", "model.onnx", "--out-dir", "dist/model"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        self.assertIn("WARN schema drift detected", output)

    @patch("vex.cli.runtime_compatibility_check", return_value=(True, "Runtime compatibility check passed"))
    def test_schema_validate_model_success(self, _compat: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "build" / "model-artifact").mkdir(parents=True)
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["schema", "validate-model"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        self.assertIn("Runtime compatibility check passed", output)

    @patch(
        "vex.cli.runtime_compatibility_check",
        return_value=(True, "Skipped runtime compatibility check (vex-ai-runtime path not found)"),
    )
    def test_schema_validate_model_strict_runtime_requires_runtime(self, _compat: object) -> None:
        code, _output = self.run_cli(["schema", "validate-model", "--strict-runtime"])
        self.assertEqual(code, 2)

    @patch("vex.cli.schema_drift_warning", return_value="WARN schema drift detected")
    @patch("vex.cli.runtime_compatibility_check", return_value=(True, "Runtime compatibility check passed"))
    def test_schema_validate_model_prints_schema_warning(self, _compat: object, _drift: object) -> None:
        code, output = self.run_cli(["schema", "validate-model"])
        self.assertEqual(code, 0)
        self.assertIn("WARN schema drift detected", output)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_benchmark_writes_report(self, run_command: object, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "benchmark",
                        "--command",
                        "python -c 'print(1)'",
                        "--runs",
                        "2",
                        "--warmup",
                        "1",
                        "--out",
                        "artifacts/bench/latest.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

            report_path = Path(temp_dir) / "artifacts" / "bench" / "latest.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("Benchmark report written", output)
        self.assertEqual(report["schema"], "vex-benchmark/v1")
        self.assertEqual(len(report["timings_ms"]), 2)
        self.assertEqual(run_command.call_count, 3)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_eval_writes_report(self, run_command: object, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text('{"input":"a"}\n{"input":"b"}\n', encoding="utf-8")
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["eval", "--command", "python -c 'print(1)'", "--out", "artifacts/evals/latest.json"])
            finally:
                os.chdir(original_cwd)

            report = json.loads((root / "artifacts" / "evals" / "latest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("Eval report written", output)
        self.assertEqual(report["schema"], "vex-eval/v1")
        self.assertEqual(report["dataset_case_count"], 2)
        run_command.assert_called_once()

    def test_eval_requires_command_or_script(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "pyproject.toml").write_text("[tool.vex]\nmanaged=true\n", encoding="utf-8")
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["eval"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 2)
        self.assertIn("requires --command", output)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command_capture", return_value=(0, "score=1\n", ""))
    def test_eval_per_case_uses_dataset_cases(self, run_capture: object, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text(
                '{"input":"a","expect_contains":"score"}\n{"input":"b"}\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "eval",
                        "--per-case",
                        "--command",
                        "python -c 'print({input})'",
                        "--out",
                        "artifacts/evals/per-case.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads((root / "artifacts" / "evals" / "per-case.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("mode=per-case", output)
        self.assertEqual(report["mode"], "per-case")
        self.assertEqual(report["dataset_case_count"], 2)
        self.assertEqual(report["passed"], 2)
        self.assertEqual(run_capture.call_count, 2)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command_capture")
    def test_eval_per_case_supports_exact_and_json_path(self, run_capture: object, _uv_bin: object) -> None:
        run_capture.side_effect = [
            (0, "expected", ""),
            (0, '{"score": {"value": 42}}', ""),
        ]
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text(
                '{"input":"first","expect_exact":"expected"}\n'
                '{"input":"second","expect_json_path":"score.value","expect_json_equals":42}\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    [
                        "eval",
                        "--per-case",
                        "--command",
                        "python -c 'print({input})'",
                        "--out",
                        "artifacts/evals/per-case-rich.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads((root / "artifacts" / "evals" / "per-case-rich.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["results"][0]["exact_ok"], True)
        self.assertEqual(report["results"][1]["json_path_ok"], True)

    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.run_command", return_value=0)
    def test_deploy_docker_builds_image(self, run_command: object, _docker: object) -> None:
        code, _output = self.run_cli(["deploy", "docker", "--image", "ghcr.io/acme/vex", "--tag", "dev"])
        self.assertEqual(code, 0)
        called_argv = run_command.call_args.kwargs.get("argv") if hasattr(run_command.call_args, "kwargs") else None
        if called_argv is None:
            called_argv = run_command.call_args.args[0]
        self.assertEqual(called_argv, ["docker", "build", "-t", "ghcr.io/acme/vex:dev", "."])

    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.run_command", return_value=0)
    def test_deploy_docker_uses_profile_overrides(self, run_command: object, _docker: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "deploy.targets.toml").write_text(
                "[profiles.prod]\n"
                'image = "ghcr.io/acme/vex-prod"\n'
                'tag = "2026"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["deploy", "docker", "--profile", "prod"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        called_argv = run_command.call_args.args[0]
        self.assertEqual(called_argv, ["docker", "build", "-t", "ghcr.io/acme/vex-prod:2026", "."])

    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.run_command", return_value=0)
    def test_deploy_profile_supports_inheritance_and_env(self, run_command: object, _docker: object) -> None:
        original_cwd = os.getcwd()
        previous_repo = os.environ.get("VEX_IMAGE_REPO")
        os.environ["VEX_IMAGE_REPO"] = "ghcr.io/acme"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "deploy.targets.toml").write_text(
                "[profiles.default]\n"
                'image = "${VEX_IMAGE_REPO}/base"\n'
                'tag = "latest"\n\n'
                "[profiles.prod]\n"
                'inherit = "default"\n'
                'tag = "2027"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["deploy", "docker", "--profile", "prod"])
            finally:
                os.chdir(original_cwd)
                if previous_repo is None:
                    del os.environ["VEX_IMAGE_REPO"]
                else:
                    os.environ["VEX_IMAGE_REPO"] = previous_repo

        self.assertEqual(code, 0)
        called_argv = run_command.call_args.args[0]
        self.assertEqual(called_argv, ["docker", "build", "-t", "ghcr.io/acme/base:2027", "."])

    def test_deploy_cloud_run_writes_scaffold(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["deploy", "cloud-run", "--service", "demo-svc", "--region", "us-east1"])
            finally:
                os.chdir(original_cwd)

            content = (Path(temp_dir) / "deploy" / "cloud-run.yaml").read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn("Wrote Cloud Run scaffold", output)
        self.assertIn("name: demo-svc", content)

    @patch("vex.cli.detect_gcloud_project", return_value="demo-project")
    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    @patch("vex.cli.shutil.which")
    def test_deploy_check_reports_ready_state(
        self,
        which_mock: object,
        _uv_bin: object,
        _docker: object,
        _project: object,
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/bin/tool" if name in {"gcloud", "modal"} else None
        code, output = self.run_cli(["deploy", "check"])
        self.assertEqual(code, 0)
        self.assertIn("OK  uv available", output)
        self.assertIn("OK  docker-compatible CLI found: docker", output)
        self.assertIn("OK  gcloud CLI found", output)
        self.assertIn("OK  modal CLI found", output)

    @patch("vex.cli.detect_gcloud_project", return_value=None)
    @patch("vex.cli.docker_like_bin", return_value=None)
    @patch("vex.cli.uv_bin", return_value=None)
    @patch("vex.cli.shutil.which", return_value=None)
    def test_deploy_check_reports_missing_tools(
        self,
        _which: object,
        _uv_bin: object,
        _docker: object,
        _project: object,
    ) -> None:
        code, output = self.run_cli(["deploy", "check"])
        self.assertEqual(code, 1)
        self.assertIn("WARN uv not found", output)
        self.assertIn("WARN docker/podman not found", output)
        self.assertIn("WARN gcloud CLI not found", output)

    @patch("vex.cli.run_command", return_value=0)
    @patch("vex.cli.shutil.which", return_value="/usr/bin/gcloud")
    def test_deploy_cloud_run_apply_invokes_gcloud(self, _which: object, run_command: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["deploy", "cloud-run", "--apply", "--service", "svc", "--region", "us-west1"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        called_argv = run_command.call_args.args[0]
        self.assertEqual(called_argv[0:4], ["gcloud", "run", "services", "replace"])

    @patch("vex.cli.run_command", return_value=0)
    @patch("vex.cli.shutil.which")
    def test_deploy_modal_run_invokes_modal_cli(self, which_mock: object, run_command: object) -> None:
        which_mock.side_effect = lambda name: "/usr/bin/modal" if name == "modal" else None
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["deploy", "modal", "--run", "--app-name", "demo-app"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        called_argv = run_command.call_args.args[0]
        self.assertEqual(called_argv[0:2], ["modal", "deploy"])


if __name__ == "__main__":
    unittest.main()
