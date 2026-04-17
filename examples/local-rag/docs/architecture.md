# Architecture

vex is an AI-native workflow layer for Python apps. It is explicitly not a new
dependency resolver, lockfile format, build backend, or general-purpose Python
runtime.

## Principles

1. `pyproject.toml` is the single source of truth.
2. Default to a local `.venv` per project.
3. Prefer delegation to mature tools over reimplementation.
4. Keep the command surface small.
5. Optimize for AI app developers first.
6. Treat runtime choice, policy, and model packaging as first-class workflow
   concerns.

## Substrate

vex composes four categories of tooling:

- `uv` for Python installation, virtualenvs, dependency add/remove/lock/sync,
  and build and publish delegation.
- `vex-ai-runtime` for native model artifact loading and runtime policy
  enforcement.
- local model runtimes like `ollama` for development and fallback.
- eval and benchmark adapters for local-first quality and performance loops.
