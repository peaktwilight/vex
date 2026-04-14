# Architecture

## Goal

`vex` should unify the Python app workflow without inventing a parallel packaging ecosystem.

## MVP Principles

1. Use `pyproject.toml` as the source of truth.
2. Default to a local `.venv` per project.
3. Prefer delegation to mature tools over reimplementation.
4. Keep the command surface small.
5. Optimize for app developers first, while remaining library-capable.

## Recommended Integration Stack

### Core

- `uv`
  - Python installation and pinning
  - virtual environment creation
  - dependency add/remove/lock/sync
  - command execution
  - build and publish delegation
  - isolated tool execution
- `pytest`
  - default test runner
- `ruff`
  - lint and format
- `mypy`
  - default type checking
- `watchfiles`
  - generic dev reload support
- `hatchling`
  - default build backend in generated projects

### Later Phase

- `cibuildwheel` for wheel CI
- `PyInstaller` for user-facing standalone executables
- `PEX` for hermetic internal app packaging
- `maturin` for Rust acceleration paths
- `mypyc` for typed Python hotspots

## Non-Goals

- custom dependency resolver
- custom lockfile format in v0
- custom build backend
- cloud-agnostic deployment abstraction from day one
- a new Python runtime in the initial product

## Why A New Runtime Is Not The MVP

Python can be made faster, but a Bun-style universal runtime replacement is much harder because:

- CPython compatibility matters deeply
- many important packages depend on native extensions
- a lot of real Python performance already lives outside the interpreter
- startup and packaging constraints matter as much as runtime speed

The better initial wedge is a unified workflow that can later add selective acceleration.
