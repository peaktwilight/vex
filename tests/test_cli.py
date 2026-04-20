from __future__ import annotations

import contextlib
import io
import json
import logging
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

    @patch.dict(os.environ, {}, clear=True)
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
                code, _output = self.run_cli(["dev", "--no-reload", "--bind", "127.0.0.1"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        run_command.assert_called_once_with(
            ["uv", "run", "sh", "-c", "python -m http.server --bind 127.0.0.1"],
            cwd=None,
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True)
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_dev_banner_prints_openai_when_openai_key_set(
        self, _run_command: object, _uv_bin: object
    ) -> None:
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
                _code, output = self.run_cli(["dev", "--no-reload"])
            finally:
                os.chdir(original_cwd)

        self.assertIn("provider=openai", output)
        self.assertNotIn("provider=ollama", output)

    @patch.dict(os.environ, {}, clear=True)
    @patch("vex.cli.shutil.which")
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_dev_banner_prints_ollama_when_ollama_on_path(
        self, _run_command: object, _uv_bin: object, which: object
    ) -> None:
        which.return_value = "/usr/local/bin/ollama"
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
                _code, output = self.run_cli(["dev", "--no-reload"])
            finally:
                os.chdir(original_cwd)

        self.assertIn("provider=ollama", output)
        self.assertNotIn("ollama not on PATH", output)

    @patch.dict(os.environ, {}, clear=True)
    @patch("vex.cli.shutil.which")
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_dev_banner_prints_install_pointer_when_no_keys_and_no_ollama(
        self, _run_command: object, _uv_bin: object, which: object
    ) -> None:
        which.return_value = None
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
                _code, output = self.run_cli(["dev", "--no-reload"])
            finally:
                os.chdir(original_cwd)

        self.assertIn("provider=ollama", output)
        self.assertIn("ollama not on PATH", output)
        self.assertIn("https://ollama.com", output)

    @patch.dict(os.environ, {}, clear=True)
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_dev_flags_are_not_leaked_into_script_args(
        self, run_command: object, _uv_bin: object
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text(
                "[tool.vex.scripts]\n"
                'dev = "python -m http.server"\n',
                encoding="utf-8",
            )
            (Path(temp_dir) / "extra").mkdir()
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    ["dev", "--no-reload", "--watch", "extra", "--bind", "127.0.0.1"]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        run_command.assert_called_once_with(
            ["uv", "run", "sh", "-c", "python -m http.server --bind 127.0.0.1"],
            cwd=None,
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True)
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_dev_no_provider_check_suppresses_banner(
        self, _run_command: object, _uv_bin: object
    ) -> None:
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
                _code, output = self.run_cli(["dev", "--no-provider-check", "--no-reload"])
            finally:
                os.chdir(original_cwd)

        self.assertNotIn("[vex dev] provider=", output)

    def test_resolve_dev_watch_paths_includes_flag_paths(self) -> None:
        from vex.cli import resolve_dev_watch_paths

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "extra").mkdir()
            paths = resolve_dev_watch_paths(["extra"], root)

        resolved = [p.name for p in paths]
        self.assertIn("src", resolved)
        self.assertIn("extra", resolved)

    def test_resolve_dev_watch_paths_reads_pyproject_dev_watch(self) -> None:
        from vex.cli import resolve_dev_watch_paths

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "prompts").mkdir()
            (root / "pyproject.toml").write_text(
                "[tool.vex.dev]\nwatch = [\"prompts\"]\n",
                encoding="utf-8",
            )
            paths = resolve_dev_watch_paths([], root)

        resolved = [p.name for p in paths]
        self.assertIn("src", resolved)
        self.assertIn("prompts", resolved)

    def test_resolve_dev_watch_paths_skips_missing_paths(self) -> None:
        from vex.cli import resolve_dev_watch_paths

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = resolve_dev_watch_paths(["does-not-exist"], root)

        self.assertEqual(paths, [])

    @patch.dict(os.environ, {}, clear=True)
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_uv", return_value=0)
    def test_dev_falls_back_to_no_reload_when_watchfiles_missing(
        self, run_uv: object, _uv_bin: object
    ) -> None:
        from vex.cli import run_dev_with_reload

        uv_args = ["run", "sh", "-c", "python -m http.server"]
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir, contextlib.redirect_stdout(buffer):
            code = run_dev_with_reload(uv_args, [Path(temp_dir)], watchfiles_module=None)

        self.assertEqual(code, 0)
        run_uv.assert_called_once_with(uv_args)
        self.assertIn("watchfiles", buffer.getvalue())

    @patch.dict(os.environ, {}, clear=True)
    def test_resolve_dev_provider_prefers_openai_then_anthropic_then_ollama(self) -> None:
        from vex.cli import resolve_dev_provider

        self.assertEqual(resolve_dev_provider({"OPENAI_API_KEY": "sk-x"}), "openai")
        self.assertEqual(
            resolve_dev_provider({"ANTHROPIC_API_KEY": "sk-ant-x"}),
            "anthropic",
        )
        self.assertEqual(
            resolve_dev_provider(
                {"OPENAI_API_KEY": "sk-x", "ANTHROPIC_API_KEY": "sk-ant-x"}
            ),
            "openai",
        )
        self.assertEqual(resolve_dev_provider({}), "ollama")

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
        import ast
        import json as _json

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["init", "agent", "support-agent"])
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "support-agent"
            pkg = root / "src" / "support_agent"
            pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
            agent_src = (pkg / "agent.py").read_text(encoding="utf-8")
            settings_src = (pkg / "settings.py").read_text(encoding="utf-8")
            main_src = (pkg / "main.py").read_text(encoding="utf-8")
            eval_src = (pkg / "eval.py").read_text(encoding="utf-8")
            env_example = (root / ".env.example").read_text(encoding="utf-8")
            cases_text = (root / "evals" / "datasets" / "cases.jsonl").read_text(encoding="utf-8")

            has_prompt = (root / "prompts" / "system.md").exists()
            has_dataset = (root / "evals" / "datasets" / ".gitkeep").exists()
            has_eval_runner = (root / "evals" / "run_eval.py").exists()
            has_deploy_targets = (root / "deploy.targets.toml").exists()

        self.assertEqual(code, 0)
        self.assertIn('template = "agent"', pyproject_text)
        self.assertIn("package-mode = true", pyproject_text)
        self.assertIn('dev = "python -m support_agent.main"', pyproject_text)
        self.assertIn('benchmark = "python -m support_agent.benchmark"', pyproject_text)
        self.assertIn('eval = "python evals/run_eval.py --input {input}"', pyproject_text)
        self.assertIn('[project.optional-dependencies]', pyproject_text)
        self.assertIn('"pydantic-ai>=0.0.0"', pyproject_text)
        self.assertIn('observability = [', pyproject_text)
        self.assertIn('"logfire>=3.0"', pyproject_text)
        self.assertTrue(has_deploy_targets)
        self.assertTrue(has_prompt)
        self.assertTrue(has_dataset)
        self.assertTrue(has_eval_runner)

        self.assertIn("from pydantic_ai import Agent", agent_src)
        self.assertIn("@agent.tool", agent_src)
        self.assertIn("lookup_faq", agent_src)
        self.assertIn("BaseSettings", settings_src)
        self.assertIn("resolve_provider", settings_src)
        self.assertIn("ollama", settings_src)
        self.assertIn("build_agent", main_src)
        self.assertIn('if os.environ.get("LOGFIRE_TOKEN"):', main_src)
        self.assertIn("import logfire", main_src)
        self.assertIn("logfire.configure()", main_src)
        self.assertIn("logfire.instrument_pydantic_ai()", main_src)
        self.assertIn("except ImportError:", main_src)
        self.assertIn("asyncio.run", eval_src)
        self.assertIn("OPENAI_API_KEY", env_example)
        self.assertIn("VEX_OLLAMA_MODEL", env_example)
        self.assertIn("LOGFIRE_TOKEN=pylf_v1_...", env_example)
        self.assertIn("OTEL_EXPORTER_OTLP_ENDPOINT=", env_example)
        self.assertIn("OTEL_EXPORTER_OTLP_HEADERS=", env_example)

        for name, source in [
            ("agent.py", agent_src),
            ("settings.py", settings_src),
            ("main.py", main_src),
            ("eval.py", eval_src),
        ]:
            with self.subTest(file=name):
                ast.parse(source)

        case_lines = [line for line in cases_text.splitlines() if line.strip()]
        self.assertGreaterEqual(len(case_lines), 3)
        for line in case_lines:
            parsed = _json.loads(line)
            self.assertIn("input", parsed)

    def test_init_agent_produces_portable_python_floor(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["init", "agent", "portable-agent"])
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "portable-agent"
            pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
            python_version = (root / ".python-version").read_text(encoding="utf-8").strip()

        self.assertEqual(code, 0)
        self.assertIn('requires-python = ">=3.11"', pyproject)
        self.assertEqual(python_version, "3.12")

    def test_init_agent_default_framework_is_pydantic_ai(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["init", "agent", "default-fw"])
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "default-fw"
            pkg = root / "src" / "default_fw"
            pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
            has_agent_py = (pkg / "agent.py").exists()
            has_graph_py = (pkg / "graph.py").exists()

        self.assertEqual(code, 0)
        self.assertIn('framework = "pydantic-ai"', pyproject)
        self.assertIn('"pydantic-ai>=0.0.0"', pyproject)
        self.assertTrue(has_agent_py)
        self.assertFalse(has_graph_py)

    def test_init_agent_langgraph_writes_graph_py(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    ["init", "agent", "lg-agent", "--framework", "langgraph"]
                )
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "lg-agent"
            pkg = root / "src" / "lg_agent"
            has_graph_py = (pkg / "graph.py").exists()
            graph_src = (pkg / "graph.py").read_text(encoding="utf-8") if has_graph_py else ""
            has_agent_py = (pkg / "agent.py").exists()

        self.assertEqual(code, 0)
        self.assertTrue(has_graph_py)
        self.assertFalse(has_agent_py)
        self.assertIn("StateGraph", graph_src)
        self.assertIn("ToolNode", graph_src)
        self.assertIn("lookup_faq", graph_src)

    def test_init_agent_langgraph_sets_framework_config(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    ["init", "agent", "lg-config", "--framework", "langgraph"]
                )
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "lg-config"
            pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn('framework = "langgraph"', pyproject)
        self.assertIn('"langgraph>=0.2"', pyproject)

    def test_init_agent_langgraph_pyproject_has_langchain_deps(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    ["init", "agent", "lg-deps", "--framework", "langgraph"]
                )
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "lg-deps"
            pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn('"langchain-openai>=0.2"', pyproject)
        self.assertIn('"langchain-anthropic>=0.2"', pyproject)
        self.assertNotIn("pydantic-ai", pyproject)

    def test_init_agent_claude_sdk_writes_agent_py(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    ["init", "agent", "claude-sdk", "--framework", "claude-agent-sdk"]
                )
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "claude-sdk"
            pkg = root / "src" / "claude_sdk"
            has_agent_py = (pkg / "agent.py").exists()
            has_graph_py = (pkg / "graph.py").exists()
            agent_src = (pkg / "agent.py").read_text(encoding="utf-8") if has_agent_py else ""

        self.assertEqual(code, 0)
        self.assertTrue(has_agent_py)
        self.assertFalse(has_graph_py)
        self.assertIn("from claude_agent_sdk import", agent_src)
        self.assertIn("ClaudeAgent", agent_src)
        self.assertIn("lookup_faq", agent_src)

    def test_init_agent_claude_sdk_pyproject_has_claude_dep(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    ["init", "agent", "claude-dep", "--framework", "claude-agent-sdk"]
                )
            finally:
                os.chdir(original_cwd)

            root = Path(temp_dir) / "claude-dep"
            pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn('framework = "claude-agent-sdk"', pyproject)
        self.assertIn('"claude-agent-sdk>=0.1.60"', pyproject)
        self.assertNotIn("pydantic-ai", pyproject)
        self.assertNotIn("langgraph", pyproject)

    def test_init_agent_all_frameworks_generate_valid_python(self) -> None:
        import ast

        original_cwd = os.getcwd()
        cases = [
            ("pydantic-ai", "fw-pa", "fw_pa"),
            ("langgraph", "fw-lg", "fw_lg"),
            ("claude-agent-sdk", "fw-cs", "fw_cs"),
        ]
        for framework, dir_name, pkg_name in cases:
            with self.subTest(framework=framework):
                with tempfile.TemporaryDirectory() as temp_dir:
                    os.chdir(temp_dir)
                    try:
                        code, _output = self.run_cli(
                            ["init", "agent", dir_name, "--framework", framework]
                        )
                    finally:
                        os.chdir(original_cwd)

                    root = Path(temp_dir) / dir_name
                    pkg = root / "src" / pkg_name
                    py_sources: list[tuple[str, str]] = []
                    for py_file in sorted(pkg.glob("*.py")):
                        py_sources.append((str(py_file), py_file.read_text(encoding="utf-8")))
                    run_eval_path = root / "evals" / "run_eval.py"
                    py_sources.append(
                        (str(run_eval_path), run_eval_path.read_text(encoding="utf-8"))
                    )

                    self.assertEqual(code, 0)
                    # must have generated at least the package files plus run_eval
                    self.assertGreaterEqual(len(py_sources), 4)
                    for name, source in py_sources:
                        ast.parse(source)  # raises if invalid

    def test_init_agent_rejects_framework_without_agent_template(self) -> None:
        code, output = self.run_cli(
            ["init", "inference-api", "bad-combo", "--framework", "langgraph"]
        )
        self.assertEqual(code, 2)
        self.assertIn("--framework is only valid with", output)

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

    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_reports_framework_in_config(self, _uv_bin: object) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.env]\npath = \".venv\"\n\n"
                "[tool.vex.scripts]\n"
                'dev = "python -m demo.main"\n'
                'eval = "python evals/run_eval.py --input {input}"\n'
                'test = "pytest"\n\n'
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'network = "deny"\n\n'
                "[tool.vex.ai]\n"
                'template = "agent"\n'
                'framework = "langgraph"\n',
                encoding="utf-8",
            )
            (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
            (root / ".venv").mkdir()
            os.chdir(temp_dir)
            try:
                _code, output = self.run_cli(["doctor", "ai"])
            finally:
                os.chdir(original_cwd)

        self.assertIn("OK  framework: langgraph", output)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-testkey"}, clear=False)
    @patch("vex.cli.sandbox_image_cached", return_value=True)
    @patch("vex.cli.sandbox_backend", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_reports_healthy_setup(
        self, _uv_bin: object, _sandbox_backend: object, _image_cached: object
    ) -> None:
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
        self.assertIn("OK  sandbox image cached locally", output)
        self.assertIn("OK  hosted provider credential detected: openai (OPENAI_API_KEY)", output)

    @patch.dict(os.environ, {}, clear=True)
    @patch("vex.cli.shutil.which", return_value=None)
    @patch("vex.cli.sandbox_image_cached", return_value=None)
    @patch("vex.cli.sandbox_backend", return_value="none")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_warns_when_no_provider_and_no_ollama(
        self,
        _uv_bin: object,
        _sandbox_backend: object,
        _image_cached: object,
        _which: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = false\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["doctor", "ai"])
            finally:
                os.chdir(original_cwd)

        self.assertNotEqual(code, 0)
        self.assertIn(
            "WARN no hosted provider keys set and 'ollama' not on PATH",
            output,
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-testkey"}, clear=False)
    @patch("vex.cli.sandbox_image_cached", return_value=True)
    @patch("vex.cli.sandbox_backend", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_runtime_missing_is_soft_for_scaffolded_project(
        self,
        _uv_bin: object,
        _sandbox_backend: object,
        _image_cached: object,
    ) -> None:
        original_cwd = os.getcwd()
        os.environ.pop("VEX_AI_RUNTIME_PATH", None)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.env]\npath = \".venv\"\n\n"
                "[tool.vex.scripts]\n"
                'dev = "python -m demo.main"\n'
                'benchmark = "python -m demo.benchmark"\n'
                'eval = "python evals/run_eval.py --input {input}"\n\n'
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
        self.assertIn("INFO runtime path not resolved", output)
        self.assertNotIn("WARN runtime path", output)

    @patch.dict(os.environ, {"VEX_AI_RUNTIME_PATH": "/definitely/not/a/real/path"}, clear=False)
    @patch("vex.cli.sandbox_image_cached", return_value=True)
    @patch("vex.cli.sandbox_backend", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_runtime_missing_errors_when_env_var_set(
        self,
        _uv_bin: object,
        _sandbox_backend: object,
        _image_cached: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = true\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["doctor", "ai"])
            finally:
                os.chdir(original_cwd)

        self.assertNotEqual(code, 0)
        self.assertIn(
            "WARN VEX_AI_RUNTIME_PATH=/definitely/not/a/real/path does not exist",
            output,
        )

    @patch.dict(os.environ, {}, clear=True)
    @patch("vex.cli.shutil.which", return_value=None)
    @patch("vex.cli.sandbox_image_cached", return_value=None)
    @patch("vex.cli.sandbox_backend", return_value="none")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_validates_eval_dataset_and_deploy_env(
        self,
        _uv_bin: object,
        _sandbox_backend: object,
        _image_cached: object,
        _which: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = false\n",
                encoding="utf-8",
            )
            datasets_dir = root / "evals" / "datasets"
            datasets_dir.mkdir(parents=True)
            (datasets_dir / "good.jsonl").write_text(
                '{"input": "a"}\n{"input": "b"}\n',
                encoding="utf-8",
            )
            (datasets_dir / "broken.jsonl").write_text(
                '{"input": "ok"}\n{not json\n{"no_input": true}\n',
                encoding="utf-8",
            )
            (root / "deploy.targets.toml").write_text(
                "[profiles.default]\n"
                'image = "${VEX_IMAGE_REPO}/demo"\n'
                'region = "${VEX_DEPLOY_REGION}"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                _code, output = self.run_cli(["doctor", "ai"])
            finally:
                os.chdir(original_cwd)

        self.assertIn("OK  eval dataset evals/datasets/good.jsonl: 2 cases valid", output)
        self.assertIn("WARN evals/datasets/broken.jsonl", output)
        self.assertIn("invalid JSON", output)
        self.assertIn(
            "WARN deploy.targets.toml references unbound env vars: "
            "VEX_DEPLOY_REGION, VEX_IMAGE_REPO",
            output,
        )

    @patch.dict(os.environ, {"LOGFIRE_TOKEN": "pylf_v1_fake"}, clear=True)
    @patch("vex.cli.shutil.which", return_value=None)
    @patch("vex.cli.sandbox_image_cached", return_value=None)
    @patch("vex.cli.sandbox_backend", return_value="none")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_reports_observability_logfire(
        self,
        _uv_bin: object,
        _sandbox_backend: object,
        _image_cached: object,
        _which: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = false\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                _code, output = self.run_cli(["doctor", "ai"])
            finally:
                os.chdir(original_cwd)

        self.assertIn("OK  observability: logfire", output)
        self.assertNotIn("WARN no observability configured", output)

    @patch.dict(
        os.environ,
        {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://user:pass@collector.example.com:4318/v1/traces"},
        clear=True,
    )
    @patch("vex.cli.shutil.which", return_value=None)
    @patch("vex.cli.sandbox_image_cached", return_value=None)
    @patch("vex.cli.sandbox_backend", return_value="none")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_reports_observability_otel(
        self,
        _uv_bin: object,
        _sandbox_backend: object,
        _image_cached: object,
        _which: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = false\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                _code, output = self.run_cli(["doctor", "ai"])
            finally:
                os.chdir(original_cwd)

        self.assertIn("OK  observability: otel endpoint=collector.example.com:4318", output)
        # Credentials and path must be stripped from the reported host.
        self.assertNotIn("user:pass", output)
        self.assertNotIn("/v1/traces", output)
        self.assertNotIn("WARN no observability configured", output)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-testkey"}, clear=True)
    @patch("vex.cli.shutil.which", return_value=None)
    @patch("vex.cli.sandbox_image_cached", return_value=None)
    @patch("vex.cli.sandbox_backend", return_value="none")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    def test_doctor_ai_warns_no_observability_soft(
        self,
        _uv_bin: object,
        _sandbox_backend: object,
        _image_cached: object,
        _which: object,
    ) -> None:
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
                "sandbox = false\n",
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

        # Missing observability is a soft warning — must not cause non-zero exit
        # (only the provider key is set, and all other AI checks are green).
        self.assertEqual(code, 0)
        self.assertIn(
            "WARN no observability configured "
            "(set LOGFIRE_TOKEN or OTEL_EXPORTER_OTLP_ENDPOINT)",
            output,
        )

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

    @patch("vex.cli.shutil.which")
    @patch("vex.cli.subprocess.run")
    def test_eval_detects_promptfoo_config(
        self, subprocess_run: object, which_mock: object
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/local/bin/uvx" if name == "uvx" else None

        class _Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        def _fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
            output_path = Path(argv[argv.index("--output") + 1])
            output_path.write_text(
                json.dumps(
                    {
                        "results": {
                            "results": [
                                {
                                    "success": True,
                                    "prompt": {"raw": "hello"},
                                    "response": {"output": "hi"},
                                    "provider": {"id": "openai:gpt-4o-mini"},
                                    "latencyMs": 123,
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            return _Completed()

        subprocess_run.side_effect = _fake_run

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "promptfooconfig.yaml").write_text("providers: []\n", encoding="utf-8")
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    ["eval", "--out", "artifacts/evals/promptfoo.json"]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "promptfoo.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertIn("adapter=promptfoo", output)
        self.assertEqual(report["adapter"], "promptfoo")
        self.assertEqual(subprocess_run.call_count, 1)
        invoked_argv = subprocess_run.call_args.args[0]
        self.assertEqual(invoked_argv[:4], ["/usr/local/bin/uvx", "promptfoo", "eval", "-c"])
        self.assertIn("--output", invoked_argv)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command_capture", return_value=(0, "out", ""))
    def test_eval_no_promptfoo_flag_uses_harness(
        self, run_capture: object, _uv_bin: object
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "promptfooconfig.yaml").write_text("providers: []\n", encoding="utf-8")
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text(
                '{"input":"a"}\n', encoding="utf-8"
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "eval",
                        "--no-promptfoo",
                        "--per-case",
                        "--command",
                        "echo {input}",
                        "--out",
                        "artifacts/evals/forced.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "forced.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertIn("mode=per-case", output)
        self.assertEqual(report["adapter"], "harness")
        self.assertEqual(report["mode"], "per-case")
        run_capture.assert_called_once()

    @patch("vex.cli.shutil.which")
    @patch("vex.cli.subprocess.run")
    def test_eval_normalizes_promptfoo_results(
        self, subprocess_run: object, which_mock: object
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/local/bin/uvx" if name == "uvx" else None

        class _Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        fake_payload = {
            "results": {
                "results": [
                    {
                        "success": True,
                        "prompt": {"raw": "case-1"},
                        "response": {"output": "ok"},
                        "provider": "openai:gpt-4o-mini",
                        "latencyMs": 42,
                    },
                    {
                        "success": False,
                        "prompt": {"raw": "case-2"},
                        "response": {"output": "bad"},
                        "provider": {"id": "openai:gpt-4o-mini"},
                    },
                    {
                        "success": True,
                        "vars": {"topic": "cats"},
                        "output": "meow",
                    },
                ]
            }
        }

        def _fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
            output_path = Path(argv[argv.index("--output") + 1])
            output_path.write_text(json.dumps(fake_payload), encoding="utf-8")
            return _Completed()

        subprocess_run.side_effect = _fake_run

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "promptfooconfig.yaml").write_text("providers: []\n", encoding="utf-8")
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    ["eval", "--out", "artifacts/evals/norm.json"]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "norm.json").read_text(encoding="utf-8")
            )

        # 2/3 passed => overall harness would still flag failure (exit 1).
        self.assertEqual(code, 1)
        self.assertEqual(report["schema"], "vex-eval/v1")
        self.assertEqual(report["adapter"], "promptfoo")
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["failed"], 1)
        self.assertAlmostEqual(report["pass_rate"], 66.67, places=2)
        self.assertEqual(len(report["results"]), 3)
        self.assertEqual(report["results"][0]["input"], "case-1")
        self.assertEqual(report["results"][0]["output"], "ok")
        self.assertEqual(report["results"][0]["provider"], "openai:gpt-4o-mini")
        self.assertEqual(report["results"][0]["latency_ms"], 42.0)
        self.assertEqual(report["results"][0]["passed"], True)
        self.assertEqual(report["results"][1]["passed"], False)

    # ------------------------------------------------------------------
    # Inspect AI adapter
    # ------------------------------------------------------------------

    def _write_inspect_log(self, log_dir: Path, payload: dict) -> None:
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "run-1.json").write_text(json.dumps(payload), encoding="utf-8")

    @patch("vex.cli.shutil.which")
    @patch("vex.cli.subprocess.run")
    def test_eval_detects_inspect_config(
        self, subprocess_run: object, which_mock: object
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/local/bin/uvx" if name == "uvx" else None

        class _Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        def _fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
            log_dir = Path(argv[argv.index("--log-dir") + 1])
            self._write_inspect_log(
                log_dir,
                {
                    "eval": {"model": "openai/gpt-4o-mini", "task": "theory"},
                    "results": {"total_samples": 1, "completed_samples": 1},
                    "samples": [
                        {
                            "id": "s1",
                            "input": "hello",
                            "output": {
                                "completion": "hi",
                                "time": 0.123,
                            },
                            "scores": {"accuracy": {"value": "C"}},
                        }
                    ],
                },
            )
            return _Completed()

        subprocess_run.side_effect = _fake_run

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "inspect.yaml").write_text("tasks: []\n", encoding="utf-8")
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    ["eval", "--out", "artifacts/evals/inspect.json"]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "inspect.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertIn("adapter=inspect", output)
        self.assertEqual(report["adapter"], "inspect")
        self.assertEqual(report["schema"], "vex-eval/v1")
        self.assertEqual(subprocess_run.call_count, 1)
        invoked_argv = subprocess_run.call_args.args[0]
        self.assertEqual(
            invoked_argv[:5],
            ["/usr/local/bin/uvx", "--from", "inspect-ai", "inspect", "eval"],
        )
        self.assertIn("--log-dir", invoked_argv)
        self.assertIn("--log-format", invoked_argv)
        self.assertEqual(
            invoked_argv[invoked_argv.index("--log-format") + 1], "json"
        )

    @patch("vex.cli.shutil.which")
    @patch("vex.cli.subprocess.run")
    def test_eval_adapter_flag_forces_inspect(
        self, subprocess_run: object, which_mock: object
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/local/bin/uvx" if name == "uvx" else None

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                # No inspect config file present -> adapter=inspect must error.
                code, output = self.run_cli(["eval", "--adapter", "inspect"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 2)
        self.assertIn("adapter='inspect'", output)
        subprocess_run.assert_not_called()

    @patch("vex.cli.shutil.which")
    @patch("vex.cli.subprocess.run")
    def test_eval_adapter_flag_forces_promptfoo(
        self, subprocess_run: object, which_mock: object
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/local/bin/uvx" if name == "uvx" else None

        class _Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        def _fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
            output_path = Path(argv[argv.index("--output") + 1])
            output_path.write_text(json.dumps({"results": {"results": []}}), encoding="utf-8")
            return _Completed()

        subprocess_run.side_effect = _fake_run

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            # Both configs present; --adapter promptfoo must win.
            (root / "inspect.yaml").write_text("tasks: []\n", encoding="utf-8")
            (root / "promptfooconfig.yaml").write_text(
                "providers: []\n", encoding="utf-8"
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "eval",
                        "--adapter",
                        "promptfoo",
                        "--out",
                        "artifacts/evals/forced-pf.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        self.assertIn("adapter=promptfoo", output)
        invoked_argv = subprocess_run.call_args.args[0]
        self.assertIn("promptfoo", invoked_argv)
        self.assertNotIn("inspect-ai", invoked_argv)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command_capture", return_value=(0, "out", ""))
    def test_eval_adapter_flag_forces_harness(
        self, run_capture: object, _uv_bin: object
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            # Both adapter configs present; --adapter harness must bypass them.
            (root / "inspect.yaml").write_text("tasks: []\n", encoding="utf-8")
            (root / "promptfooconfig.yaml").write_text(
                "providers: []\n", encoding="utf-8"
            )
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text(
                '{"input":"a"}\n', encoding="utf-8"
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    [
                        "eval",
                        "--adapter",
                        "harness",
                        "--per-case",
                        "--command",
                        "echo {input}",
                        "--out",
                        "artifacts/evals/forced-harness.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "forced-harness.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(code, 0)
        self.assertEqual(report["adapter"], "harness")
        run_capture.assert_called_once()

    @patch("vex.cli.shutil.which")
    @patch("vex.cli.subprocess.run")
    def test_eval_normalizes_inspect_results(
        self, subprocess_run: object, which_mock: object
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/local/bin/uvx" if name == "uvx" else None

        class _Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        fake_log = {
            "eval": {"model": "anthropic/claude-4-7-sonnet", "task": "theory"},
            "results": {"total_samples": 3, "completed_samples": 3},
            "samples": [
                {
                    "id": 1,
                    "input": "case-1",
                    "output": {"completion": "answer-1", "time": 0.042},
                    "scores": {"accuracy": {"value": "C"}},
                    "total_time": 0.05,
                },
                {
                    "id": 2,
                    "input": [
                        {"role": "user", "content": "case-2-msg"},
                    ],
                    "output": {
                        "choices": [
                            {"message": {"content": "answer-2"}}
                        ]
                    },
                    "scores": {"accuracy": {"value": "I"}},
                },
                {
                    "id": 3,
                    "input": "case-3",
                    "output": {"completion": "ok"},
                    "scores": {"custom_scorer": {"value": 0.9}},
                },
            ],
        }

        def _fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
            log_dir = Path(argv[argv.index("--log-dir") + 1])
            self._write_inspect_log(log_dir, fake_log)
            return _Completed()

        subprocess_run.side_effect = _fake_run

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "inspect.yaml").write_text("tasks: []\n", encoding="utf-8")
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    ["eval", "--out", "artifacts/evals/inspect-norm.json"]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "inspect-norm.json").read_text(
                    encoding="utf-8"
                )
            )

        # 2/3 passing => adapter run exits non-zero to flag partial failure.
        self.assertEqual(code, 1)
        self.assertEqual(report["schema"], "vex-eval/v1")
        self.assertEqual(report["adapter"], "inspect")
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["failed"], 1)
        self.assertAlmostEqual(report["pass_rate"], 66.67, places=2)
        self.assertEqual(len(report["results"]), 3)
        self.assertEqual(report["results"][0]["input"], "case-1")
        self.assertEqual(report["results"][0]["output"], "answer-1")
        self.assertEqual(
            report["results"][0]["provider"], "anthropic/claude-4-7-sonnet"
        )
        # ``total_time`` = 0.05s wins over ``output.time`` and becomes 50ms.
        self.assertEqual(report["results"][0]["latency_ms"], 50.0)
        self.assertTrue(report["results"][0]["passed"])
        self.assertEqual(report["results"][1]["output"], "answer-2")
        self.assertEqual(report["results"][1]["input"], "case-2-msg")
        self.assertFalse(report["results"][1]["passed"])
        self.assertTrue(report["results"][2]["passed"])
        self.assertEqual(report["results"][2]["score"], 0.9)

    def test_eval_no_promptfoo_flag_still_works_with_deprecation_warning(
        self,
    ) -> None:
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        from unittest.mock import patch as _patch

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "promptfooconfig.yaml").write_text(
                "providers: []\n", encoding="utf-8"
            )
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text(
                '{"input":"a"}\n', encoding="utf-8"
            )
            os.chdir(temp_dir)
            try:
                with (
                    _patch("vex.cli.uv_bin", return_value="uv"),
                    _patch("vex.cli.run_command_capture", return_value=(0, "out", "")),
                    contextlib.redirect_stdout(stdout_buf),
                    contextlib.redirect_stderr(stderr_buf),
                ):
                    from vex.cli import main

                    code = main(
                        [
                            "eval",
                            "--no-promptfoo",
                            "--per-case",
                            "--command",
                            "echo {input}",
                            "--out",
                            "artifacts/evals/deprecated.json",
                        ]
                    )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "deprecated.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(code, 0)
        self.assertEqual(report["adapter"], "harness")
        self.assertIn("--no-promptfoo is deprecated", stderr_buf.getvalue())

    @patch("vex.cli.shutil.which")
    @patch("vex.cli.subprocess.run")
    def test_eval_adapter_auto_prefers_inspect_over_promptfoo(
        self, subprocess_run: object, which_mock: object
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/local/bin/uvx" if name == "uvx" else None

        class _Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        def _fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
            # Only Inspect's argv shape includes --log-dir.
            log_dir = Path(argv[argv.index("--log-dir") + 1])
            self._write_inspect_log(
                log_dir,
                {
                    "eval": {"model": "anthropic/claude-4-7-sonnet"},
                    "results": {"total_samples": 1, "completed_samples": 1},
                    "samples": [
                        {
                            "id": 1,
                            "input": "q",
                            "output": {"completion": "a"},
                            "scores": {"accuracy": {"value": "C"}},
                        }
                    ],
                },
            )
            return _Completed()

        subprocess_run.side_effect = _fake_run

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "inspect.yaml").write_text("tasks: []\n", encoding="utf-8")
            (root / "promptfooconfig.yaml").write_text(
                "providers: []\n", encoding="utf-8"
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    ["eval", "--out", "artifacts/evals/auto.json"]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "auto.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertIn("adapter=inspect", output)
        self.assertEqual(report["adapter"], "inspect")
        invoked_argv = subprocess_run.call_args.args[0]
        # Confirm we never ran promptfoo.
        self.assertNotIn("promptfoo", invoked_argv)
        self.assertIn("inspect-ai", invoked_argv)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command_capture")
    def test_eval_min_pass_rate_gates(
        self, run_capture: object, _uv_bin: object
    ) -> None:
        run_capture.side_effect = [
            (0, "hit", ""),
            (1, "miss", ""),
            (1, "miss", ""),
        ]
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text(
                '{"input":"a","expect_contains":"hit"}\n'
                '{"input":"b","expect_contains":"hit"}\n'
                '{"input":"c","expect_contains":"hit"}\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "eval",
                        "--per-case",
                        "--command",
                        "echo {input}",
                        "--min-pass-rate",
                        "0.5",
                        "--out",
                        "artifacts/evals/gate.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "gate.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 1)
        self.assertEqual(report["passed"], 1)
        self.assertEqual(report["failed"], 2)
        self.assertIn("below --min-pass-rate", output)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command_capture")
    def test_eval_min_pass_rate_passes_when_above_threshold(
        self, run_capture: object, _uv_bin: object
    ) -> None:
        run_capture.side_effect = [
            (0, "hit", ""),
            (0, "hit", ""),
            (1, "miss", ""),
        ]
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text(
                '{"input":"a","expect_contains":"hit"}\n'
                '{"input":"b","expect_contains":"hit"}\n'
                '{"input":"c","expect_contains":"hit"}\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "eval",
                        "--per-case",
                        "--command",
                        "echo {input}",
                        "--min-pass-rate",
                        "0.5",
                        "--out",
                        "artifacts/evals/gate-pass.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        # 2/3 = 66% which is above the 50% gate, but one case hard-failed
        # so the raw harness still exits 1. The gate itself does not fire.
        self.assertEqual(code, 1)
        self.assertNotIn("below --min-pass-rate", output)

    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command_capture", return_value=(0, "hit", ""))
    def test_eval_json_flag_prints_report_to_stdout(
        self, run_capture: object, _uv_bin: object
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text(
                '{"input":"a","expect_contains":"hit"}\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "eval",
                        "--per-case",
                        "--command",
                        "echo {input}",
                        "--json",
                        "--out",
                        "artifacts/evals/json.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        # Must be a single JSON document — parseable without tweaks.
        payload = json.loads(output.strip())
        self.assertEqual(payload["schema"], "vex-eval/v1")
        self.assertEqual(payload["adapter"], "harness")
        self.assertEqual(payload["mode"], "per-case")
        self.assertEqual(payload["passed"], 1)
        # Human-friendly summary suppressed when --json is set.
        self.assertNotIn("Eval report written", output)

    # ------------------------------------------------------------------
    # vex eval --policy
    # ------------------------------------------------------------------

    @patch("vex.cli.sandbox_backend", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_eval_policy_wraps_harness_in_sandbox(
        self,
        run_command: object,
        _uv_bin: object,
        _backend: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'network = "deny"\n'
                'filesystem = "project"\n'
                'sandbox_backend = "docker"\n'
                'sandbox_image = "python:3.12-slim"\n'
                "sandbox_memory_mb = 1024\n"
                "sandbox_pids_limit = 128\n"
                "unsafe_fallback = false\n",
                encoding="utf-8",
            )
            (root / "evals" / "datasets").mkdir(parents=True)
            (root / "evals" / "datasets" / "cases.jsonl").write_text(
                '{"input":"a"}\n', encoding="utf-8"
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    [
                        "eval",
                        "--policy",
                        "--command",
                        "python -c 'print(1)'",
                        "--out",
                        "artifacts/evals/policy.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        run_command.assert_called_once()
        invoked_argv = run_command.call_args.args[0]
        # The sandbox prefix must be the literal docker run --rm ... shape.
        self.assertEqual(invoked_argv[0], "docker")
        self.assertEqual(invoked_argv[1], "run")
        self.assertEqual(invoked_argv[2], "--rm")
        self.assertIn("--network", invoked_argv)
        self.assertIn("--cap-drop", invoked_argv)
        self.assertIn("ALL", invoked_argv)
        self.assertIn("--read-only", invoked_argv)
        # sh -c <command> must appear verbatim at the end.
        self.assertEqual(invoked_argv[-3], "sh")
        self.assertEqual(invoked_argv[-2], "-c")
        self.assertEqual(invoked_argv[-1], "python -c 'print(1)'")

    def test_eval_policy_fails_when_sandbox_disabled(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = false\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "eval",
                        "--policy",
                        "--command",
                        "python -c 'print(1)'",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 2)
        self.assertIn("requires [tool.vex.policy].sandbox = true", output)
        self.assertIn("vex policy set sandbox true --type bool", output)

    @patch("vex.cli.sandbox_backend", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_eval_policy_stamps_report_with_policy_snapshot(
        self,
        _run_command: object,
        _uv_bin: object,
        _backend: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'network = "deny"\n'
                'filesystem = "project"\n'
                'sandbox_backend = "docker"\n'
                'sandbox_image = "python:3.12-slim"\n'
                "sandbox_memory_mb = 1024\n"
                "sandbox_pids_limit = 128\n"
                "unsafe_fallback = false\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    [
                        "eval",
                        "--policy",
                        "--command",
                        "python -c 'print(1)'",
                        "--out",
                        "artifacts/evals/policy-stamp.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "policy-stamp.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "vex-eval/v1")
        self.assertIn("policy", report)
        policy = report["policy"]
        self.assertEqual(policy["enforced"], True)
        self.assertEqual(policy["network"], "deny")
        self.assertEqual(policy["filesystem"], "project")
        self.assertEqual(policy["sandbox_backend"], "docker")
        self.assertEqual(policy["sandbox_image"], "python:3.12-slim")
        self.assertEqual(policy["sandbox_memory_mb"], 1024)
        self.assertEqual(policy["sandbox_pids_limit"], 128)
        self.assertEqual(policy["unsafe_fallback_applied"], False)

    @patch("vex.cli.sandbox_backend", return_value="none")
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_eval_policy_honors_unsafe_fallback(
        self,
        run_command: object,
        _uv_bin: object,
        _backend: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'sandbox_backend = "none"\n'
                "unsafe_fallback = true\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "eval",
                        "--policy",
                        "--command",
                        "python -c 'print(1)'",
                        "--out",
                        "artifacts/evals/policy-fallback.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

            report = json.loads(
                (root / "artifacts" / "evals" / "policy-fallback.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(code, 0)
        self.assertIn("unsafe_fallback=true", output)
        # Ran locally (not wrapped): first two args are [uv, "run"].
        invoked_argv = run_command.call_args.args[0]
        self.assertEqual(invoked_argv[:2], ["uv", "run"])
        # Report must mark enforcement off and fallback on.
        self.assertEqual(report["policy"]["enforced"], False)
        self.assertEqual(report["policy"]["unsafe_fallback_applied"], True)

    @patch("vex.cli.sandbox_backend", return_value="docker")
    @patch("vex.cli.shutil.which")
    @patch("vex.cli.subprocess.run")
    def test_eval_policy_wraps_promptfoo_uvx_invocation(
        self,
        subprocess_run: object,
        which_mock: object,
        _backend: object,
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/local/bin/uvx" if name == "uvx" else None

        class _Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        def _fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
            # The sandboxed invocation no longer writes a tmp output file on
            # the host (it would run inside the container). Return empty
            # results so the normalizer produces an empty report.
            output_path_idx = None
            if "--output" in argv:
                output_path_idx = argv.index("--output") + 1
            if output_path_idx is not None and output_path_idx < len(argv):
                candidate = Path(argv[output_path_idx])
                # Only write to host paths; skip container /workspace paths.
                if candidate.is_absolute() and candidate.parent.exists():
                    candidate.write_text(
                        json.dumps({"results": {"results": []}}),
                        encoding="utf-8",
                    )
            return _Completed()

        subprocess_run.side_effect = _fake_run

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex]\nmanaged = true\n\n"
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'network = "deny"\n'
                'sandbox_backend = "docker"\n'
                'sandbox_image = "python:3.12-slim"\n',
                encoding="utf-8",
            )
            (root / "promptfooconfig.yaml").write_text(
                "providers: []\n", encoding="utf-8"
            )
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    [
                        "eval",
                        "--policy",
                        "--adapter",
                        "promptfoo",
                        "--out",
                        "artifacts/evals/policy-promptfoo.json",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        # No adapter content, exit code should be 0 (no failures detected) or
        # 1 if the normalizer treats 0/0 as non-failing; the key assertion
        # is the shape of the subprocess argv.
        self.assertIn(code, (0, 1))
        self.assertEqual(subprocess_run.call_count, 1)
        invoked_argv = subprocess_run.call_args.args[0]
        # Sandbox prefix.
        self.assertEqual(invoked_argv[0], "docker")
        self.assertEqual(invoked_argv[1], "run")
        self.assertEqual(invoked_argv[2], "--rm")
        self.assertIn("python:3.12-slim", invoked_argv)
        # sh -c <shell_cmd> contains the uvx promptfoo invocation.
        self.assertEqual(invoked_argv[-3], "sh")
        self.assertEqual(invoked_argv[-2], "-c")
        self.assertIn("uvx", invoked_argv[-1])
        self.assertIn("promptfoo", invoked_argv[-1])
        # Shim for uv-less default image.
        self.assertIn("pip install", invoked_argv[-1])

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

    @patch("vex.cli.run_command_capture", return_value=(0, "https://svc-abcd-uw.a.run.app\n", ""))
    @patch("vex.cli.run_command", return_value=0)
    @patch("vex.cli.detect_gcloud_project", return_value="demo-project")
    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    @patch("vex.cli.shutil.which", return_value="/usr/bin/gcloud")
    def test_deploy_cloud_run_apply_calls_gcloud_deploy(
        self,
        _which: object,
        _uv_bin: object,
        _docker: object,
        _project: object,
        run_command: object,
        _run_capture: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    [
                        "deploy",
                        "cloud-run",
                        "--apply",
                        "--service",
                        "svc",
                        "--region",
                        "us-west1",
                        "--project",
                        "demo-project",
                        "--image",
                        "gcr.io/demo-project/svc",
                        "--tag",
                        "v1",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        build_argv = run_command.call_args.args[0]
        self.assertEqual(build_argv[0:3], ["gcloud", "builds", "submit"])
        self.assertIn("gcr.io/demo-project/svc:v1", build_argv)

        deploy_argv = _run_capture.call_args.args[0]
        self.assertEqual(deploy_argv[0:4], ["gcloud", "run", "deploy", "svc"])
        self.assertIn("--image", deploy_argv)
        self.assertIn("gcr.io/demo-project/svc:v1", deploy_argv)
        self.assertIn("--region", deploy_argv)
        self.assertIn("us-west1", deploy_argv)
        self.assertIn("--project", deploy_argv)
        self.assertIn("demo-project", deploy_argv)

    @patch("vex.cli.run_command_capture", return_value=(0, "https://svc.a.run.app\n", ""))
    @patch("vex.cli.run_command", return_value=0)
    @patch("vex.cli.detect_gcloud_project", return_value="demo-project")
    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    @patch("vex.cli.shutil.which", return_value="/usr/bin/gcloud")
    def test_deploy_cloud_run_apply_respects_profile_interpolation(
        self,
        _which: object,
        _uv_bin: object,
        _docker: object,
        _project: object,
        run_command: object,
        run_capture: object,
    ) -> None:
        original_cwd = os.getcwd()
        previous_repo = os.environ.get("VEX_IMAGE_REPO")
        os.environ["VEX_IMAGE_REPO"] = "gcr.io/demo"
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                (root / "deploy.targets.toml").write_text(
                    "[profiles.default]\n"
                    'image = "${VEX_IMAGE_REPO}/app"\n'
                    'tag = "v7"\n'
                    'service = "my-svc"\n'
                    'region = "us-west1"\n'
                    'project = "demo-project"\n'
                    'memory = "1Gi"\n'
                    'cpu = "2"\n'
                    'min_instances = 1\n'
                    'max_instances = 4\n'
                    'service_account = "runner@demo-project.iam.gserviceaccount.com"\n',
                    encoding="utf-8",
                )
                os.chdir(temp_dir)
                try:
                    code, _output = self.run_cli(["deploy", "cloud-run", "--apply"])
                finally:
                    os.chdir(original_cwd)
        finally:
            if previous_repo is None:
                os.environ.pop("VEX_IMAGE_REPO", None)
            else:
                os.environ["VEX_IMAGE_REPO"] = previous_repo

        self.assertEqual(code, 0)
        build_argv = run_command.call_args.args[0]
        self.assertIn("gcr.io/demo/app:v7", build_argv)

        deploy_argv = run_capture.call_args.args[0]
        self.assertIn("gcr.io/demo/app:v7", deploy_argv)
        self.assertIn("--memory", deploy_argv)
        self.assertIn("1Gi", deploy_argv)
        self.assertIn("--cpu", deploy_argv)
        self.assertIn("2", deploy_argv)
        self.assertIn("--min-instances", deploy_argv)
        self.assertIn("1", deploy_argv)
        self.assertIn("--max-instances", deploy_argv)
        self.assertIn("4", deploy_argv)
        self.assertIn("--service-account", deploy_argv)
        self.assertIn("runner@demo-project.iam.gserviceaccount.com", deploy_argv)

    @patch("vex.cli.run_command_capture")
    @patch("vex.cli.run_command")
    @patch("vex.cli.deploy_preflight", return_value=(2, ["WARN missing tool"]))
    def test_deploy_cloud_run_apply_runs_preflight_first(
        self,
        _preflight: object,
        run_command: object,
        run_capture: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    ["deploy", "cloud-run", "--apply", "--service", "svc", "--project", "p"]
                )
            finally:
                os.chdir(original_cwd)

        self.assertNotEqual(code, 0)
        self.assertIn("WARN missing tool", output)
        run_command.assert_not_called()
        run_capture.assert_not_called()

    @patch(
        "vex.cli.run_command_capture",
        return_value=(
            0,
            "Building...\n✓ Created web endpoint => https://acme--demo-app.modal.run\n",
            "",
        ),
    )
    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    @patch("vex.cli.shutil.which")
    def test_deploy_modal_run_invokes_modal_cli(
        self,
        which_mock: object,
        _uv_bin: object,
        _docker: object,
        run_capture: object,
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/bin/modal" if name == "modal" else None
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(
                    [
                        "deploy",
                        "modal",
                        "--run",
                        "--app-name",
                        "demo-app",
                        "--skip-preflight",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        called_argv = run_capture.call_args.args[0]
        self.assertEqual(called_argv[0:2], ["modal", "deploy"])
        # Scaffold path should be passed as third arg.
        self.assertTrue(called_argv[2].endswith("modal_app.py"))

    @patch(
        "vex.cli.run_command_capture",
        return_value=(
            0,
            "View app at https://acme--demo-app.modal.run\n",
            "",
        ),
    )
    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.uv_bin", return_value="/usr/local/bin/uv")
    @patch("vex.cli.shutil.which")
    def test_deploy_modal_run_surfaces_deployed_url(
        self,
        which_mock: object,
        _uv_bin: object,
        _docker: object,
        _run_capture: object,
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/bin/modal" if name == "modal" else None
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "deploy",
                        "modal",
                        "--run",
                        "--app-name",
                        "demo-app",
                        "--skip-preflight",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        self.assertIn("Deployed: https://acme--demo-app.modal.run", output)

    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.run_command", return_value=0)
    def test_deploy_docker_run_builds_and_runs_image(
        self, run_command: object, _docker: object
    ) -> None:
        code, _output = self.run_cli(
            [
                "deploy",
                "docker",
                "--image",
                "ghcr.io/acme/app",
                "--tag",
                "v1",
                "--run",
                "--port",
                "8080",
                "--skip-preflight",
            ]
        )
        self.assertEqual(code, 0)
        argvs = [call.args[0] for call in run_command.call_args_list]
        self.assertEqual(argvs[0], ["docker", "build", "-t", "ghcr.io/acme/app:v1", "."])
        self.assertEqual(
            argvs[-1],
            ["docker", "run", "--rm", "-p", "8080:8080", "ghcr.io/acme/app:v1"],
        )

    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.run_command", return_value=0)
    def test_deploy_docker_policy_gate_adds_caps_and_net(
        self, run_command: object, _docker: object
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text(
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'network = "deny"\n'
                "sandbox_memory_mb = 512\n"
                "sandbox_pids_limit = 64\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "deploy",
                        "docker",
                        "--image",
                        "ghcr.io/acme/app",
                        "--tag",
                        "v1",
                        "--run",
                        "--port",
                        "8080",
                        "--policy-gate",
                        "--skip-preflight",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        run_argv = run_command.call_args_list[-1].args[0]
        # docker run argv should contain the hardened flags.
        self.assertEqual(run_argv[0:2], ["docker", "run"])
        self.assertIn("--cap-drop", run_argv)
        self.assertIn("ALL", run_argv)
        self.assertIn("--read-only", run_argv)
        self.assertIn("--network", run_argv)
        self.assertIn("none", run_argv)
        self.assertIn("--memory", run_argv)
        self.assertIn("512m", run_argv)
        self.assertIn("--pids-limit", run_argv)
        self.assertIn("64", run_argv)
        self.assertIn("--security-opt", run_argv)
        self.assertIn("no-new-privileges", run_argv)
        # Port mapping + image must survive.
        self.assertIn("8080:8080", run_argv)
        self.assertEqual(run_argv[-1], "ghcr.io/acme/app:v1")
        # Summary line should print on success.
        self.assertIn("[policy-gate]", output)
        self.assertIn("enforced via docker", output)

    @patch("vex.cli.run_command_capture", return_value=(0, "https://svc.a.run.app\n", ""))
    @patch("vex.cli.run_command", return_value=0)
    @patch("vex.cli.shutil.which", return_value="/usr/bin/gcloud")
    def test_deploy_cloud_run_policy_gate_rejects_allow_unauth(
        self,
        _which: object,
        _run_command: object,
        _run_capture: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'network = "deny"\n',
                encoding="utf-8",
            )
            (root / "deploy.targets.toml").write_text(
                "[profiles.default]\n"
                'image = "gcr.io/demo/app"\n'
                'tag = "v1"\n'
                'service = "svc"\n'
                'region = "us-west1"\n'
                "allow_unauthenticated = true\n",
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                buffer = io.StringIO()
                err_buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(err_buffer):
                    from vex.cli import main as cli_main
                    code = cli_main(
                        [
                            "deploy",
                            "cloud-run",
                            "--apply",
                            "--project",
                            "p",
                            "--policy-gate",
                            "--skip-preflight",
                        ]
                    )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 2)
        self.assertIn("allow_unauthenticated", err_buffer.getvalue())

    @patch("vex.cli.run_command_capture", return_value=(0, "https://svc.a.run.app\n", ""))
    @patch("vex.cli.run_command", return_value=0)
    @patch("vex.cli.shutil.which", return_value="/usr/bin/gcloud")
    def test_deploy_cloud_run_policy_gate_injects_no_unauth_flag(
        self,
        _which: object,
        _run_command: object,
        run_capture: object,
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'network = "deny"\n',
                encoding="utf-8",
            )
            (root / "deploy.targets.toml").write_text(
                "[profiles.default]\n"
                'image = "gcr.io/demo/app"\n'
                'tag = "v1"\n'
                'service = "svc"\n'
                'region = "us-west1"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    [
                        "deploy",
                        "cloud-run",
                        "--apply",
                        "--project",
                        "p",
                        "--policy-gate",
                        "--skip-preflight",
                    ]
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 0)
        deploy_argv = run_capture.call_args.args[0]
        self.assertEqual(deploy_argv[0:4], ["gcloud", "run", "deploy", "svc"])
        self.assertIn("--no-allow-unauthenticated", deploy_argv)
        self.assertIn("--cpu-boost=false", deploy_argv)
        self.assertIn("[policy-gate]", output)
        self.assertIn("allow_unauth=false", output)
        self.assertIn("enforced via cloud-run", output)

    @patch(
        "vex.cli.run_command_capture",
        return_value=(0, "View app at https://acme--demo-app.modal.run\n", ""),
    )
    @patch("vex.cli.shutil.which")
    def test_deploy_modal_policy_gate_prints_warning_not_fail_on_permissive(
        self,
        which_mock: object,
        _run_capture: object,
    ) -> None:
        which_mock.side_effect = lambda name: "/usr/bin/modal" if name == "modal" else None
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "[tool.vex.policy]\n"
                "sandbox = true\n"
                'network = "deny"\n',
                encoding="utf-8",
            )
            # Pre-seed a permissive modal scaffold to override what scaffold_modal
            # would normally write. scaffold_modal overwrites on each run, so
            # instead we monkey-patch the scaffolded file AFTER scaffold runs by
            # using a post-scaffold hook is impractical — instead we rely on
            # scaffold_modal writing first, then we inject permissive markers by
            # patching the file right before deploy. For simplicity in this
            # test, we rewrite the file after scaffold_modal runs by watching
            # the parent's working directory. Easiest approach: run in two
            # steps — scaffold only (no --run), then rewrite, then --run.
            os.chdir(temp_dir)
            try:
                # Step 1: scaffold only.
                scaffold_code, _ = self.run_cli(
                    ["deploy", "modal", "--app-name", "demo-app", "--skip-preflight"]
                )
                self.assertEqual(scaffold_code, 0)

                # Step 2: rewrite scaffold with a permissive shape, then --run.
                (Path(temp_dir) / "deploy" / "modal_app.py").write_text(
                    "import modal\n"
                    "app = modal.App(name=\"demo-app\")\n"
                    "image = modal.Image.debian_slim()\n"
                    "@app.function(image=image, allow_network=True)\n"
                    "def healthz():\n"
                    "    return {\"status\": \"ok\"}\n",
                    encoding="utf-8",
                )

                # We need to NOT re-scaffold. scaffold_modal overwrites, so
                # we patch it out for the second invocation.
                with patch("vex.cli.scaffold_modal") as scaffold_mock:
                    scaffold_mock.return_value = Path(temp_dir) / "deploy" / "modal_app.py"
                    buffer = io.StringIO()
                    err_buffer = io.StringIO()
                    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(err_buffer):
                        from vex.cli import main as cli_main
                        code = cli_main(
                            [
                                "deploy",
                                "modal",
                                "--run",
                                "--app-name",
                                "demo-app",
                                "--policy-gate",
                                "--skip-preflight",
                            ]
                        )
                    combined_output = buffer.getvalue() + err_buffer.getvalue()
            finally:
                os.chdir(original_cwd)

        # Permissive scaffold prints a WARN but does not fail the deploy.
        self.assertEqual(code, 0)
        self.assertIn("WARN", combined_output)
        self.assertIn("allow_network", combined_output)
        self.assertIn("[policy-gate]", combined_output)
        self.assertIn("enforced via modal", combined_output)

    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.run_command", return_value=0)
    def test_deploy_policy_gate_refuses_when_sandbox_disabled(
        self, _run_command: object, _docker: object
    ) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "pyproject.toml").write_text(
                "[tool.vex.policy]\n"
                "sandbox = false\n"
                'network = "deny"\n',
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                buffer = io.StringIO()
                err_buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(err_buffer):
                    from vex.cli import main as cli_main
                    code = cli_main(
                        [
                            "deploy",
                            "docker",
                            "--run",
                            "--policy-gate",
                            "--skip-preflight",
                        ]
                    )
                err_out = err_buffer.getvalue()
            finally:
                os.chdir(original_cwd)

        self.assertEqual(code, 2)
        self.assertIn("sandbox = false", err_out)

    @patch("vex.cli.docker_like_bin", return_value="docker")
    @patch("vex.cli.run_command", return_value=0)
    def test_deploy_no_policy_gate_flag_preserves_old_behavior(
        self, run_command: object, _docker: object
    ) -> None:
        code, _output = self.run_cli(
            [
                "deploy",
                "docker",
                "--image",
                "ghcr.io/acme/app",
                "--tag",
                "v1",
                "--run",
                "--port",
                "9000",
                "--skip-preflight",
            ]
        )
        self.assertEqual(code, 0)
        run_argv = run_command.call_args_list[-1].args[0]
        self.assertEqual(
            run_argv,
            ["docker", "run", "--rm", "-p", "9000:9000", "ghcr.io/acme/app:v1"],
        )


class VexExportImportTests(unittest.TestCase):
    """Tests for `vex export` and `vex import` — portable .vex artifacts (#42)."""

    def run_cli(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(argv)
        return code, buffer.getvalue()

    def _write_project(self, root: Path, name: str = "demo-bot", version: str = "0.1.0") -> None:
        pyproject = (
            "[project]\n"
            f'name = "{name}"\n'
            f'version = "{version}"\n'
            'requires-python = ">=3.11"\n'
            "\n"
            "[tool.vex]\n"
            "managed = true\n"
            "\n"
            "[tool.vex.policy]\n"
            "sandbox = true\n"
            'network = "deny"\n'
            "\n"
            "[tool.vex.ai]\n"
            'template = "agent"\n'
            'runtime = "vex-ai-runtime"\n'
            'framework = "pydantic-ai"\n'
            "\n"
            "[tool.vex.eval]\n"
            'adapter = "inspect"\n'
        )
        (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
        pkg_dir = root / "src" / name.replace("-", "_")
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "__init__.py").write_text("\n", encoding="utf-8")
        (pkg_dir / "main.py").write_text("def main():\n    print('hi')\n", encoding="utf-8")
        (root / ".env.example").write_text("OPENAI_API_KEY=\n", encoding="utf-8")
        (root / ".gitignore").write_text(".venv/\n__pycache__/\n", encoding="utf-8")
        # Add noise that default excludes should strip.
        venv = root / ".venv" / "bin"
        venv.mkdir(parents=True, exist_ok=True)
        (venv / "python").write_text("junk\n", encoding="utf-8")
        cache = pkg_dir / "__pycache__"
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "main.cpython-312.pyc").write_text("pyc\n", encoding="utf-8")
        # Real secret that must never be exported.
        (root / ".env").write_text("SECRET=42\n", encoding="utf-8")

    def _extract_tar_members(self, artifact: Path) -> list[str]:
        import tarfile as _tarfile
        with _tarfile.open(artifact, mode="r:gz") as tf:
            return sorted(m.name for m in tf.getmembers())

    def test_export_writes_deterministic_tarball(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            os.chdir(temp_dir)
            try:
                code1, _ = self.run_cli(["export", "--out", "dist/a.vex"])
                code2, _ = self.run_cli(["export", "--out", "dist/b.vex"])
                a = (root / "dist" / "a.vex").read_bytes()
                b = (root / "dist" / "b.vex").read_bytes()
            finally:
                os.chdir(original_cwd)
        self.assertEqual(code1, 0)
        self.assertEqual(code2, 0)
        self.assertEqual(a, b, "two exports of the same tree must be byte-identical")

    def test_export_manifest_has_required_fields(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, name="support-bot", version="0.3.2")
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["export", "--dry-run"])
            finally:
                os.chdir(original_cwd)
        self.assertEqual(code, 0)
        manifest = json.loads(output)
        for key in (
            "schema",
            "name",
            "version",
            "created_at",
            "python_requires",
            "entry_module",
            "policy",
            "adapters",
            "files",
            "models",
            "locks",
        ):
            self.assertIn(key, manifest)
        self.assertEqual(manifest["schema"], "vex-artifact/v1")
        self.assertEqual(manifest["name"], "support-bot")
        self.assertEqual(manifest["version"], "0.3.2")
        self.assertEqual(manifest["entry_module"], "support_bot.main")
        self.assertEqual(manifest["policy"]["network"], "deny")
        self.assertEqual(manifest["adapters"]["eval"], "inspect")
        self.assertEqual(manifest["adapters"]["framework"], "pydantic-ai")
        self.assertEqual(manifest["adapters"]["runtime"], "vex-ai-runtime")

    def test_export_excludes_venv_and_pycache_by_default(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["export", "--dry-run"])
            finally:
                os.chdir(original_cwd)
        self.assertEqual(code, 0)
        manifest = json.loads(output)
        paths = [entry["path"] for entry in manifest["files"]]
        for path in paths:
            self.assertNotIn(".venv/", path)
            self.assertNotIn("__pycache__", path)
        # .env is excluded, .env.example is not.
        self.assertNotIn(".env", paths)
        self.assertIn(".env.example", paths)

    def test_export_dry_run_writes_nothing_prints_manifest(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["export", "--dry-run", "--out", "dist/never.vex"])
            finally:
                os.chdir(original_cwd)
            self.assertEqual(code, 0)
            manifest = json.loads(output)
            self.assertEqual(manifest["schema"], "vex-artifact/v1")
            self.assertFalse((root / "dist" / "never.vex").exists())
            self.assertFalse((root / "dist").exists())

    def test_export_respects_custom_exclude_pattern(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            secrets = root / "src" / "demo_bot" / "secrets.py"
            secrets.write_text("TOKEN='x'\n", encoding="utf-8")
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(
                    ["export", "--dry-run", "--exclude", "src/demo_bot/secrets.py"]
                )
            finally:
                os.chdir(original_cwd)
        self.assertEqual(code, 0)
        manifest = json.loads(output)
        paths = [entry["path"] for entry in manifest["files"]]
        self.assertNotIn("src/demo_bot/secrets.py", paths)
        self.assertIn("src/demo_bot/main.py", paths)

    def test_export_hashes_match_file_contents(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            os.chdir(temp_dir)
            try:
                code, output = self.run_cli(["export", "--dry-run"])
            finally:
                os.chdir(original_cwd)
            self.assertEqual(code, 0)
            manifest = json.loads(output)
            import hashlib as _hashlib
            for entry in manifest["files"]:
                abs_path = root / entry["path"]
                expected = _hashlib.sha256(abs_path.read_bytes()).hexdigest()
                self.assertEqual(expected, entry["sha256"], f"hash mismatch for {entry['path']}")

    def test_import_round_trip_preserves_tree(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            artifact = root / "dist" / "demo-bot-0.1.0.vex"
            os.chdir(temp_dir)
            try:
                code, _ = self.run_cli(["export"])
                self.assertEqual(code, 0)
                self.assertTrue(artifact.exists())
            finally:
                os.chdir(original_cwd)
            # Unpack to an isolated directory.
            with tempfile.TemporaryDirectory() as dest_dir:
                dest = Path(dest_dir) / "unpacked"
                os.chdir(dest_dir)
                try:
                    code, output = self.run_cli([
                        "import",
                        str(artifact),
                        "--dest",
                        str(dest),
                    ])
                finally:
                    os.chdir(original_cwd)
                self.assertEqual(code, 0)
                self.assertIn("Unpacked demo-bot", output)
                # Every non-excluded file from the source made it across,
                # with identical content.
                for rel in [
                    "pyproject.toml",
                    "src/demo_bot/__init__.py",
                    "src/demo_bot/main.py",
                    ".env.example",
                    ".gitignore",
                ]:
                    self.assertTrue((dest / rel).exists(), f"missing {rel}")
                    self.assertEqual(
                        (root / rel).read_bytes(),
                        (dest / rel).read_bytes(),
                        f"content mismatch for {rel}",
                    )
                # .env was excluded on export and must not be in the unpack.
                self.assertFalse((dest / ".env").exists())

    def _tamper_file_in_artifact(self, artifact: Path, file_path: str, new_bytes: bytes) -> None:
        """Rewrite one file in the .vex tar but leave manifest.json untouched."""
        import tarfile as _tarfile
        with _tarfile.open(artifact, mode="r:gz") as tf:
            members = tf.getmembers()
            blobs: dict[str, bytes] = {}
            for m in members:
                if m.isfile():
                    fp = tf.extractfile(m)
                    blobs[m.name] = fp.read() if fp else b""
        blobs[file_path] = new_bytes
        # Rewrite the tarball preserving deterministic layout.
        import io as _io
        import gzip as _gzip
        raw = _io.BytesIO()
        with _gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            with _tarfile.open(fileobj=gz, mode="w", format=_tarfile.USTAR_FORMAT) as out:
                for name in sorted(blobs):
                    data = blobs[name]
                    info = _tarfile.TarInfo(name=name)
                    info.size = len(data)
                    info.mtime = 0
                    info.mode = 0o644
                    out.addfile(info, _io.BytesIO(data))
        artifact.write_bytes(raw.getvalue())

    def test_import_refuses_on_sha_mismatch(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            artifact = root / "dist" / "demo-bot-0.1.0.vex"
            os.chdir(temp_dir)
            try:
                code, _ = self.run_cli(["export"])
                self.assertEqual(code, 0)
            finally:
                os.chdir(original_cwd)
            self._tamper_file_in_artifact(artifact, "src/demo_bot/main.py", b"# tampered\n")
            with tempfile.TemporaryDirectory() as dest_dir:
                dest = Path(dest_dir) / "unpacked"
                code, output = self.run_cli(["import", str(artifact), "--dest", str(dest)])
            self.assertEqual(code, 2)
            self.assertIn("sha mismatch", output)
            self.assertIn("src/demo_bot/main.py", output)

    def test_import_force_overrides_sha_mismatch_with_warning(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            artifact = root / "dist" / "demo-bot-0.1.0.vex"
            os.chdir(temp_dir)
            try:
                code, _ = self.run_cli(["export"])
                self.assertEqual(code, 0)
            finally:
                os.chdir(original_cwd)
            self._tamper_file_in_artifact(artifact, "src/demo_bot/main.py", b"# tampered\n")
            with tempfile.TemporaryDirectory() as dest_dir:
                dest = Path(dest_dir) / "unpacked"
                code, output = self.run_cli([
                    "import",
                    str(artifact),
                    "--dest",
                    str(dest),
                    "--force",
                ])
                self.assertEqual(code, 0)
                self.assertIn("WARN sha mismatch", output)
                self.assertEqual(
                    (dest / "src/demo_bot/main.py").read_bytes(), b"# tampered\n"
                )

    def test_import_refuses_overwrite_of_non_empty_dest(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            artifact = root / "dist" / "demo-bot-0.1.0.vex"
            os.chdir(temp_dir)
            try:
                code, _ = self.run_cli(["export"])
                self.assertEqual(code, 0)
            finally:
                os.chdir(original_cwd)
            with tempfile.TemporaryDirectory() as dest_dir:
                dest = Path(dest_dir) / "existing"
                dest.mkdir()
                (dest / "preexisting.txt").write_text("keep me\n", encoding="utf-8")
                code, output = self.run_cli(["import", str(artifact), "--dest", str(dest)])
                self.assertEqual(code, 2)
                self.assertIn("refusing to overwrite", output)
                self.assertTrue((dest / "preexisting.txt").exists())
                # --force allows the overwrite.
                code, _ = self.run_cli([
                    "import",
                    str(artifact),
                    "--dest",
                    str(dest),
                    "--force",
                ])
                self.assertEqual(code, 0)
                self.assertTrue((dest / "pyproject.toml").exists())

    def test_export_includes_packaged_models_in_tarball(self) -> None:
        """Model manifests under dist/ must travel with the artifact."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            # Simulate a `vex package-model` output tree.
            (root / "dist" / "classifier" / "models").mkdir(parents=True)
            (root / "dist" / "classifier" / "models" / "classifier.onnx").write_bytes(b"fakemodel")
            import hashlib as _hashlib
            sha = _hashlib.sha256(b"fakemodel").hexdigest()
            (root / "dist" / "classifier" / "vex-model.json").write_text(
                json.dumps(
                    {
                        "schema": "vex-model/v1",
                        "schema_version": "v1",
                        "runtime": "vex-ai-runtime",
                        "engine": "onnxruntime",
                        "name": "classifier",
                        "model_path": "models/classifier.onnx",
                        "sha256": sha,
                    }
                ),
                encoding="utf-8",
            )
            os.chdir(temp_dir)
            try:
                code, _ = self.run_cli(["export", "--out", "/tmp/_model-test.vex"])
            finally:
                os.chdir(original_cwd)
            self.assertEqual(code, 0)
            members = self._extract_tar_members(Path("/tmp/_model-test.vex"))
            self.assertIn("dist/classifier/models/classifier.onnx", members)
            self.assertIn("dist/classifier/vex-model.json", members)
            # --no-include-models strips them back out.
            os.chdir(temp_dir)
            try:
                code, _ = self.run_cli([
                    "export",
                    "--no-include-models",
                    "--out",
                    "/tmp/_nomodel-test.vex",
                ])
            finally:
                os.chdir(original_cwd)
            self.assertEqual(code, 0)
            members = self._extract_tar_members(Path("/tmp/_nomodel-test.vex"))
            self.assertNotIn("dist/classifier/models/classifier.onnx", members)

    def test_build_vex_artifact_manifest_includes_uv_lock(self) -> None:
        """build_vex_artifact_manifest should expose uv.lock hash when present."""
        from vex.cli import build_vex_artifact_manifest, collect_export_files, load_vex_policy

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            (root / "uv.lock").write_text("# lockfile\n", encoding="utf-8")
            files = collect_export_files(root, include_venv=False)
            policy = load_vex_policy(root)
            manifest = build_vex_artifact_manifest(root, policy, files, [])
        self.assertIn("uv.lock", manifest["locks"])
        self.assertTrue(manifest["locks"]["uv.lock"].startswith("sha256:"))


class DevTraceTests(unittest.TestCase):
    """Coverage for vex dev --trace (closes #43)."""

    def run_cli(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(argv)
        return code, buffer.getvalue()

    @patch.dict(os.environ, {}, clear=True)
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_dev_sets_vex_trace_dir_env_by_default(
        self, _run_command: object, _uv_bin: object
    ) -> None:
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
                code, _out = self.run_cli(["dev", "--no-reload"])
            finally:
                os.chdir(original_cwd)

            self.assertEqual(code, 0)
            actual_value = os.environ.get("VEX_TRACE_DIR")
            self.assertIsNotNone(actual_value)
            assert actual_value is not None
            expected = (Path(temp_dir) / "artifacts" / "traces").resolve()
            self.assertEqual(Path(actual_value).resolve(), expected)
            self.assertTrue((Path(temp_dir) / "artifacts" / "traces").is_dir())

    @patch.dict(os.environ, {}, clear=True)
    @patch("vex.cli.uv_bin", return_value="uv")
    @patch("vex.cli.run_command", return_value=0)
    def test_dev_no_trace_flag_disables_env(
        self, _run_command: object, _uv_bin: object
    ) -> None:
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
                code, _out = self.run_cli(["dev", "--no-reload", "--no-trace"])
            finally:
                os.chdir(original_cwd)

            self.assertEqual(code, 0)
            self.assertNotIn("VEX_TRACE_DIR", os.environ)
            self.assertFalse((Path(temp_dir) / "artifacts" / "traces").exists())

    def test_trace_module_writes_jsonl_per_llm_call(self) -> None:
        from vex import trace as trace_mod

        trace_mod._reset_for_tests()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = trace_mod.enable_dev_tracing(temp_dir)
            self.assertIsNotNone(path)
            try:
                logger = logging.getLogger("pydantic_ai")
                record = logger.makeRecord(
                    "pydantic_ai",
                    logging.INFO,
                    "test",
                    0,
                    "llm request complete",
                    (),
                    None,
                    extra={
                        "event": "llm_request",
                        "latency_ms": 42.0,
                        "gen_ai.system": "openai",
                        "gen_ai.request.model": "gpt-4o-mini",
                        "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                        "gen_ai.usage.input_tokens": 7,
                        "gen_ai.usage.output_tokens": 3,
                    },
                )
                # Fire through our handler directly so we don't depend on
                # global logger propagation being enabled.
                handler = trace_mod._PYDANTIC_AI_HANDLER
                self.assertIsNotNone(handler)
                handler.handle(record)  # type: ignore[union-attr]

                assert path is not None
                lines = [
                    line for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                self.assertEqual(len(lines), 1)
                payload = json.loads(lines[0])
                self.assertEqual(payload["kind"], "llm_call")
                self.assertIn("ts", payload)
                self.assertIn("session_id", payload)
                self.assertEqual(payload["latency_ms"], 42.0)
            finally:
                trace_mod._reset_for_tests()

    def test_trace_otel_envelope_fields_present(self) -> None:
        from vex import trace as trace_mod

        trace_mod._reset_for_tests()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = trace_mod.enable_dev_tracing(temp_dir)
            self.assertIsNotNone(path)
            try:
                trace_mod.record_llm_call(
                    latency_ms=128.5,
                    **{
                        "gen_ai.system": "anthropic",
                        "gen_ai.request.model": "claude-3-5-sonnet-latest",
                        "gen_ai.response.model": "claude-3-5-sonnet-20241022",
                        "gen_ai.usage.input_tokens": 12,
                        "gen_ai.usage.output_tokens": 9,
                    },
                )
                assert path is not None
                lines = [
                    line for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                self.assertEqual(len(lines), 1)
                payload = json.loads(lines[0])
                for key in trace_mod.OTEL_GEN_AI_KEYS:
                    self.assertIn(key, payload, msg=f"missing otel key: {key}")
                self.assertEqual(payload["gen_ai.system"], "anthropic")
                self.assertEqual(payload["gen_ai.usage.input_tokens"], 12)
                self.assertEqual(payload["latency_ms"], 128.5)
                self.assertEqual(payload["kind"], "llm_call")
            finally:
                trace_mod._reset_for_tests()

    def test_trace_module_updates_latest_symlink(self) -> None:
        from vex import trace as trace_mod

        trace_mod._reset_for_tests()
        with tempfile.TemporaryDirectory() as temp_dir:
            first = trace_mod.enable_dev_tracing(temp_dir)
            trace_mod._reset_for_tests()
            # Second session: must rotate `latest.jsonl` to the new file.
            # Sleep briefly so the timestamp in the filename differs.
            import time as _time
            _time.sleep(1.1)
            second = trace_mod.enable_dev_tracing(temp_dir)
            try:
                self.assertIsNotNone(first)
                self.assertIsNotNone(second)
                assert first is not None and second is not None
                self.assertNotEqual(first, second)
                latest = Path(temp_dir) / "latest.jsonl"
                self.assertTrue(latest.exists() or latest.is_symlink())
                # Resolve (follow symlink if any) and compare to second file.
                resolved = latest.resolve()
                self.assertEqual(resolved, second.resolve())
            finally:
                trace_mod._reset_for_tests()

    def test_scaffold_main_py_includes_trace_hook(self) -> None:
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                code, _output = self.run_cli(["init", "agent", "support-agent"])
            finally:
                os.chdir(original_cwd)

            self.assertEqual(code, 0)
            root = Path(temp_dir) / "support-agent"
            main_src = (root / "src" / "support_agent" / "main.py").read_text(
                encoding="utf-8"
            )

            self.assertIn('if os.environ.get("VEX_TRACE_DIR"):', main_src)
            self.assertIn("from vex.trace import enable_dev_tracing", main_src)
            self.assertIn("enable_dev_tracing(os.environ[\"VEX_TRACE_DIR\"])", main_src)
            self.assertIn("except ImportError:", main_src)

            gitignore = root / ".gitignore"
            self.assertTrue(gitignore.exists())
            self.assertIn("artifacts/traces/", gitignore.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
