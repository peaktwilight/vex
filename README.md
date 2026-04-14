# vex

`vex` is a Bun-inspired workflow tool for Python apps.

The goal is not to replace the Python ecosystem. The goal is to make the common path obvious:

- install Python
- create a project
- add dependencies
- sync a locked environment
- run scripts
- test, build, and publish

`vex` should orchestrate mature tools rather than reimplement Python packaging from scratch.

## Product Thesis

Python already has strong building blocks like `uv`, `pytest`, `ruff`, and `hatchling`, but the day-to-day workflow is still fragmented. `vex` aims to provide:

- one entry point
- one project model
- one default environment model
- one lockfile-driven workflow
- clear escape hatches to the underlying ecosystem

## Initial Direction

The current scaffold is a small `uv`-backed Python prototype that captures the command surface and architecture.

Recommended MVP integrations:

- `uv` for Python installs, envs, resolution, locking, sync, build, publish, and tool execution
- `pytest` for tests
- `ruff` for linting and formatting
- `mypy` as the default type checker
- `watchfiles` for generic file watching
- `hatchling` as the default build backend for new projects

## Planned Commands

- `vex init`
- `vex add`
- `vex remove`
- `vex sync`
- `vex lock`
- `vex run`
- `vex test`
- `vex lint`
- `vex format`
- `vex typecheck`
- `vex doctor`
- `vex python`
- `vex build`
- `vex publish`
- `vex tool`

## Repository Layout

- `src/vex/`: prototype CLI
- `tests/`: lightweight CLI tests
- `docs/architecture.md`: integration choices and non-goals
- `docs/roadmap.md`: command surface and phased plan

## Running The Prototype

```bash
PYTHONPATH=src python3 -m vex --help
PYTHONPATH=src python3 -m vex doctor
PYTHONPATH=src python3 -m vex python list
PYTHONPATH=src python3 -m vex test
PYTHONPATH=src python3 -m unittest discover -s tests
```

`vex` currently requires `uv` to be installed and available on `PATH`.
