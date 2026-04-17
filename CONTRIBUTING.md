# Contributing

Thanks for contributing to `vex`.

This repository is a monorepo with two main components:

- `vex/` (this root): AI workflow/control-plane CLI
- `engine/vex-ai-runtime/`: native runtime and artifact validation engine

## Local Setup

Prerequisites:

- Python 3.11+
- `uv` on `PATH`
- Rust toolchain for runtime development

## Common Commands

Run all local tests:

```bash
make test
```

Run only CLI tests:

```bash
make test-vex
```

Run only runtime tests:

```bash
make test-runtime
```

## Running tests

The vex CLI test suite is written as `unittest.TestCase` classes so it can be
driven by either runner. Pick whichever is convenient:

```bash
# Stdlib unittest (no extra deps required)
python -m unittest discover -s tests

# Pytest (runs the same unittest classes plus anything marker-selected)
pytest tests/

# Integration tests: opt-in, shell out to real `uv`, ~1-2 minutes locally
pytest tests/integration -m integration
# or
VEX_RUN_INTEGRATION=1 pytest tests/integration -m integration
```

Integration tests are excluded from the default `pytest tests/` run via the
`addopts` config in `pyproject.toml` — they require `uv` on `PATH` and are
gated behind the `integration` marker plus the `VEX_RUN_INTEGRATION=1`
environment variable to avoid surprising contributors with a multi-minute
scaffold+sync during a quick unit loop.

## Architecture Boundary

Keep this separation clear:

- `vex` owns workflow UX (`init`, `eval`, `policy`, `deploy`, etc.)
- `vex-ai-runtime` owns model artifact/runtime validation and native execution logic

If you change the model schema contract, update both sides:

- `engine/vex-ai-runtime/schemas/vex-model-schema.json`
- `src/vex/cli.py` integration behavior and tests

## CI

GitHub Actions runs:

- `vex` unit tests
- runtime Python tests
- runtime Rust tests

Please keep all three green before merging.
