from __future__ import annotations

import contextlib
import io
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
        self.assertIn("Bun-inspired workflow tool for Python apps.", output)

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


if __name__ == "__main__":
    unittest.main()
