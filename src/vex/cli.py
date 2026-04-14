from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Sequence

from vex import __version__


COMMAND_HELP = {
    "init": "Scaffold a new vex-managed project",
    "add": "Add dependencies and sync the environment",
    "remove": "Remove dependencies and sync the environment",
    "sync": "Make the environment match the lockfile",
    "lock": "Resolve and write the lockfile",
    "run": "Run a command or named script in the managed environment",
    "test": "Run the project test command",
    "lint": "Run the project lint command",
    "format": "Run the project format command",
    "typecheck": "Run the project typecheck command",
    "doctor": "Check the local vex project setup",
    "python": "Manage Python installations and project pinning",
    "build": "Build project artifacts",
    "publish": "Publish artifacts to a package index",
    "tool": "Run or manage isolated Python CLI tools",
}

DEFAULT_SCRIPT_COMMANDS = {
    "test": ["--with", "pytest", "pytest"],
    "lint": ["--with", "ruff", "ruff", "check", "."],
    "format": ["--with", "ruff", "ruff", "format", "."],
    "typecheck": ["--with", "mypy", "mypy", "."],
}

PASSTHROUGH_COMMANDS = {"run", "test", "lint", "format", "typecheck"}


def project_root() -> Path:
    return Path.cwd()


def uv_bin() -> str | None:
    return shutil.which("uv")


def run_command(argv: Sequence[str], cwd: Path | None = None) -> int:
    completed = subprocess.run(list(argv), cwd=cwd, check=False)
    return completed.returncode


def run_uv(args: Sequence[str], cwd: Path | None = None) -> int:
    uv = uv_bin()
    if uv is None:
        print("vex requires 'uv' on PATH", file=sys.stderr)
        return 127
    return run_command([uv, *args], cwd=cwd)


def load_pyproject(root: Path) -> dict:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return {}
    try:
        return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def load_vex_scripts(root: Path) -> dict[str, str]:
    data = load_pyproject(root)
    scripts = data.get("tool", {}).get("vex", {}).get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in scripts.items()}


def vex_env_path(root: Path) -> Path:
    data = load_pyproject(root)
    env_path = data.get("tool", {}).get("vex", {}).get("env", {}).get("path")
    if isinstance(env_path, str) and env_path:
        return root / env_path
    return root / ".venv"


def doctor_checks(root: Path) -> tuple[int, list[str]]:
    lines: list[str] = []
    issues = 0

    uv = uv_bin()
    if uv:
        lines.append(f"OK  uv found at {uv}")
    else:
        issues += 1
        lines.append("ERR uv not found on PATH")

    pyproject_path = root / "pyproject.toml"
    if pyproject_path.exists():
        lines.append(f"OK  found {pyproject_path.name}")
    else:
        issues += 1
        lines.append("ERR missing pyproject.toml")
        return issues, lines

    data = load_pyproject(root)
    if data:
        lines.append("OK  pyproject.toml parsed successfully")
    else:
        issues += 1
        lines.append("ERR could not parse pyproject.toml")
        return issues, lines

    vex_config = data.get("tool", {}).get("vex")
    if isinstance(vex_config, dict):
        lines.append("OK  found [tool.vex] configuration")
    else:
        issues += 1
        lines.append("WARN missing [tool.vex] configuration")

    lockfile = root / "uv.lock"
    if lockfile.exists():
        lines.append("OK  found uv.lock")
    else:
        issues += 1
        lines.append("WARN missing uv.lock; run 'vex sync' or 'vex lock'")

    env_path = vex_env_path(root)
    if env_path.exists():
        lines.append(f"OK  environment directory exists at {env_path.relative_to(root)}")
    else:
        issues += 1
        lines.append(f"WARN environment directory missing at {env_path.relative_to(root)}")

    scripts = load_vex_scripts(root)
    if scripts:
        lines.append(f"OK  found vex scripts: {', '.join(sorted(scripts))}")
    else:
        lines.append("WARN no [tool.vex.scripts] aliases configured")

    return issues, lines


def append_vex_config(root: Path, package_mode: bool) -> None:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return

    content = pyproject_path.read_text(encoding="utf-8")
    if "[tool.vex]" in content:
        return

    snippet = (
        "\n[tool.vex]\n"
        "managed = true\n"
        f"package-mode = {str(package_mode).lower()}\n\n"
        "[tool.vex.python]\n"
        'prefer-managed = true\n\n'
        "[tool.vex.env]\n"
        'path = ".venv"\n\n'
        "[tool.vex.scripts]\n"
        'test = "pytest"\n'
        'lint = "ruff check ."\n'
        'format = "ruff format ."\n'
        'typecheck = "mypy ."\n'
    )
    pyproject_path.write_text(content.rstrip() + "\n" + snippet, encoding="utf-8")


def init_project_dir(path_arg: str | None) -> Path:
    if path_arg:
        return (project_root() / path_arg).resolve()
    return project_root()


def build_init_args(args: argparse.Namespace) -> tuple[list[str], Path, bool]:
    package_mode = bool(args.lib)
    uv_args = ["init"]

    if args.path:
        uv_args.append(args.path)
    if args.name:
        uv_args.extend(["--name", args.name])
    if args.python:
        uv_args.extend(["--python", args.python])

    uv_args.extend(["--vcs", "none", "--no-workspace"])

    if args.lib:
        uv_args.extend(["--lib", "--package", "--build-backend", "hatch"])
    else:
        uv_args.extend(["--app", "--no-package"])

    return uv_args, init_project_dir(args.path), package_mode


def build_add_args(args: argparse.Namespace) -> list[str]:
    uv_args = ["add"]
    if args.dev:
        uv_args.append("--dev")
    elif args.group:
        uv_args.extend(["--group", args.group])
    uv_args.extend(args.packages)
    return uv_args


def build_remove_args(args: argparse.Namespace) -> list[str]:
    uv_args = ["remove"]
    if args.dev:
        uv_args.append("--dev")
    elif args.group:
        uv_args.extend(["--group", args.group])
    uv_args.extend(args.packages)
    return uv_args


def build_sync_args(args: argparse.Namespace) -> list[str]:
    uv_args = ["sync"]
    if args.frozen:
        uv_args.append("--frozen")
    for group in args.group:
        uv_args.extend(["--group", group])
    return uv_args


def build_lock_args(args: argparse.Namespace) -> list[str]:
    uv_args = ["lock"]
    if args.upgrade and not args.packages:
        uv_args.append("--upgrade")
    for package in args.packages:
        uv_args.extend(["--upgrade-package", package])
    return uv_args


def resolve_run_args(args: argparse.Namespace, root: Path) -> list[str] | None:
    if not args.args:
        return None

    scripts = load_vex_scripts(root)
    script_name = args.args[0]
    script = scripts.get(script_name)
    if script is None:
        return ["run", *args.args]

    extra = " ".join(shlex.quote(value) for value in args.args[1:])
    command = script if not extra else f"{script} {extra}"
    return ["run", "sh", "-c", command]


def resolve_named_workflow_args(command_name: str, extra_args: Sequence[str], root: Path) -> list[str]:
    scripts = load_vex_scripts(root)
    script = scripts.get(command_name)
    if script is not None:
        extra = " ".join(shlex.quote(value) for value in extra_args)
        command = script if not extra else f"{script} {extra}"
        return ["run", "sh", "-c", command]

    default = list(DEFAULT_SCRIPT_COMMANDS[command_name])
    return ["run", *default, *extra_args]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vex",
        description="Bun-inspired workflow tool for Python apps.",
    )
    parser.add_argument("--version", action="version", version=f"vex {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help=COMMAND_HELP["init"])
    init_parser.add_argument("path", nargs="?")
    init_parser.add_argument("--name")
    init_parser.add_argument("--python")
    init_mode = init_parser.add_mutually_exclusive_group()
    init_mode.add_argument("--app", action="store_true")
    init_mode.add_argument("--lib", action="store_true")
    init_parser.set_defaults(handler=handle_init)

    add_parser = subparsers.add_parser("add", help=COMMAND_HELP["add"])
    add_parser.add_argument("packages", nargs="+")
    add_group = add_parser.add_mutually_exclusive_group()
    add_group.add_argument("--dev", action="store_true")
    add_group.add_argument("--group")
    add_parser.set_defaults(handler=handle_add)

    remove_parser = subparsers.add_parser("remove", help=COMMAND_HELP["remove"])
    remove_parser.add_argument("packages", nargs="+")
    remove_group = remove_parser.add_mutually_exclusive_group()
    remove_group.add_argument("--dev", action="store_true")
    remove_group.add_argument("--group")
    remove_parser.set_defaults(handler=handle_remove)

    sync_parser = subparsers.add_parser("sync", help=COMMAND_HELP["sync"])
    sync_parser.add_argument("--frozen", action="store_true")
    sync_parser.add_argument("--group", action="append", default=[])
    sync_parser.set_defaults(handler=handle_sync)

    lock_parser = subparsers.add_parser("lock", help=COMMAND_HELP["lock"])
    lock_parser.add_argument("--upgrade", action="store_true")
    lock_parser.add_argument("packages", nargs="*")
    lock_parser.set_defaults(handler=handle_lock)

    run_parser = subparsers.add_parser("run", help=COMMAND_HELP["run"])
    run_parser.add_argument("args", nargs=argparse.REMAINDER)
    run_parser.set_defaults(handler=handle_run)

    test_parser = subparsers.add_parser("test", help=COMMAND_HELP["test"])
    test_parser.add_argument("args", nargs=argparse.REMAINDER)
    test_parser.set_defaults(handler=handle_test)

    lint_parser = subparsers.add_parser("lint", help=COMMAND_HELP["lint"])
    lint_parser.add_argument("args", nargs=argparse.REMAINDER)
    lint_parser.set_defaults(handler=handle_lint)

    format_parser = subparsers.add_parser("format", help=COMMAND_HELP["format"])
    format_parser.add_argument("args", nargs=argparse.REMAINDER)
    format_parser.set_defaults(handler=handle_format)

    typecheck_parser = subparsers.add_parser("typecheck", help=COMMAND_HELP["typecheck"])
    typecheck_parser.add_argument("args", nargs=argparse.REMAINDER)
    typecheck_parser.set_defaults(handler=handle_typecheck)

    doctor_parser = subparsers.add_parser("doctor", help=COMMAND_HELP["doctor"])
    doctor_parser.set_defaults(handler=handle_doctor)

    python_parser = subparsers.add_parser("python", help=COMMAND_HELP["python"])
    python_subparsers = python_parser.add_subparsers(dest="python_command")

    python_install = python_subparsers.add_parser("install", help="Install a Python version")
    python_install.add_argument("version")
    python_install.set_defaults(handler=handle_python_install)

    python_pin = python_subparsers.add_parser("pin", help="Pin the project Python version")
    python_pin.add_argument("version")
    python_pin.set_defaults(handler=handle_python_pin)

    python_list = python_subparsers.add_parser("list", help="List managed Python versions")
    python_list.set_defaults(handler=handle_python_list)

    python_path = python_subparsers.add_parser("path", help="Show the active Python path")
    python_path.set_defaults(handler=handle_python_path)

    python_uninstall = python_subparsers.add_parser("uninstall", help="Uninstall a Python version")
    python_uninstall.add_argument("version")
    python_uninstall.set_defaults(handler=handle_python_uninstall)

    build_parser_cmd = subparsers.add_parser("build", help=COMMAND_HELP["build"])
    build_parser_cmd.add_argument("--wheel", action="store_true")
    build_parser_cmd.add_argument("--sdist", action="store_true")
    build_parser_cmd.set_defaults(handler=handle_build)

    publish_parser = subparsers.add_parser("publish", help=COMMAND_HELP["publish"])
    publish_parser.add_argument("--repository")
    publish_parser.set_defaults(handler=handle_publish)

    tool_parser = subparsers.add_parser("tool", help=COMMAND_HELP["tool"])
    tool_subparsers = tool_parser.add_subparsers(dest="tool_command")

    tool_run = tool_subparsers.add_parser("run", help="Run a tool in an isolated environment")
    tool_run.add_argument("tool_name")
    tool_run.add_argument("args", nargs=argparse.REMAINDER)
    tool_run.set_defaults(handler=handle_tool_run)

    tool_install = tool_subparsers.add_parser("install", help="Install a tool")
    tool_install.add_argument("tool_name")
    tool_install.set_defaults(handler=handle_tool_install)

    tool_list = tool_subparsers.add_parser("list", help="List installed tools")
    tool_list.set_defaults(handler=handle_tool_list)

    tool_upgrade = tool_subparsers.add_parser("upgrade", help="Upgrade installed tools")
    tool_upgrade.set_defaults(handler=handle_tool_upgrade)

    tool_uninstall = tool_subparsers.add_parser("uninstall", help="Uninstall a tool")
    tool_uninstall.add_argument("tool_name")
    tool_uninstall.set_defaults(handler=handle_tool_uninstall)

    return parser


def handle_init(args: argparse.Namespace) -> int:
    uv_args, root, package_mode = build_init_args(args)
    code = run_uv(uv_args)
    if code == 0:
        append_vex_config(root, package_mode=package_mode)
    return code


def handle_add(args: argparse.Namespace) -> int:
    return run_uv(build_add_args(args))


def handle_remove(args: argparse.Namespace) -> int:
    return run_uv(build_remove_args(args))


def handle_sync(args: argparse.Namespace) -> int:
    return run_uv(build_sync_args(args))


def handle_lock(args: argparse.Namespace) -> int:
    return run_uv(build_lock_args(args))


def handle_run(args: argparse.Namespace) -> int:
    uv_args = resolve_run_args(args, project_root())
    if uv_args is None:
        print("vex run requires a command or script name")
        return 2
    return run_uv(uv_args)


def handle_test(args: argparse.Namespace) -> int:
    return run_uv(resolve_named_workflow_args("test", args.args, project_root()))


def handle_lint(args: argparse.Namespace) -> int:
    return run_uv(resolve_named_workflow_args("lint", args.args, project_root()))


def handle_format(args: argparse.Namespace) -> int:
    return run_uv(resolve_named_workflow_args("format", args.args, project_root()))


def handle_typecheck(args: argparse.Namespace) -> int:
    return run_uv(resolve_named_workflow_args("typecheck", args.args, project_root()))


def handle_doctor(_args: argparse.Namespace) -> int:
    issues, lines = doctor_checks(project_root())
    for line in lines:
        print(line)
    return 0 if issues == 0 else 1


def handle_python_install(args: argparse.Namespace) -> int:
    return run_uv(["python", "install", args.version])


def handle_python_pin(args: argparse.Namespace) -> int:
    return run_uv(["python", "pin", args.version])


def handle_python_list(_args: argparse.Namespace) -> int:
    return run_uv(["python", "list"])


def handle_python_path(_args: argparse.Namespace) -> int:
    return run_uv(["python", "find"])


def handle_python_uninstall(args: argparse.Namespace) -> int:
    return run_uv(["python", "uninstall", args.version])


def handle_build(args: argparse.Namespace) -> int:
    uv_args = ["build"]
    if args.wheel:
        uv_args.append("--wheel")
    if args.sdist:
        uv_args.append("--sdist")
    return run_uv(uv_args)


def handle_publish(args: argparse.Namespace) -> int:
    uv_args = ["publish"]
    if args.repository:
        uv_args.extend(["--index", args.repository])
    return run_uv(uv_args)


def handle_tool_run(args: argparse.Namespace) -> int:
    return run_uv(["tool", "run", args.tool_name, *args.args])


def handle_tool_install(args: argparse.Namespace) -> int:
    return run_uv(["tool", "install", args.tool_name])


def handle_tool_list(_args: argparse.Namespace) -> int:
    return run_uv(["tool", "list"])


def handle_tool_upgrade(_args: argparse.Namespace) -> int:
    return run_uv(["tool", "upgrade"])


def handle_tool_uninstall(args: argparse.Namespace) -> int:
    return run_uv(["tool", "uninstall", args.tool_name])


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    raw_argv = list(argv) if argv is not None else None
    args, unknown = parser.parse_known_args(raw_argv)
    if unknown:
        if hasattr(args, "args"):
            args.args.extend(unknown)
        else:
            parser.error(f"unrecognized arguments: {' '.join(unknown)}")
    if raw_argv and getattr(args, "command", None) in PASSTHROUGH_COMMANDS:
        args.args = raw_argv[1:]
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)
