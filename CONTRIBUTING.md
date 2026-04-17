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
