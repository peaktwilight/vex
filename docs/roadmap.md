# Roadmap

## Current Prototype

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
- `vex python install|pin|list|path|uninstall`
- `vex build`
- `vex publish`
- `vex tool run|install|list|upgrade|uninstall`

These commands are useful bootstrap plumbing because they let `vex` ride on top of `uv`, but they are not the long-term moat.

## Product Direction

- `vex init agent`
- `vex init inference-api`
- `vex dev`
- `vex benchmark`
- `vex eval`
- `vex policy`
- `vex package-model`
- `vex deploy`
- `vex schema validate-model`
- `vex run --sandbox`
- `vex doctor ai`

## Later

- `vex export`
- `vex shell`
- `vex cache`
- basic workspace investigation

## v1 Direction

- polished AI project templates
- container-oriented and runtime-aware deployment helpers
- integration with `vex-ai-runtime`
- local benchmark and evaluation workflows
- opt-in secure packaging and policy enforcement
- deployment adapters for Docker/OCI, Cloud Run, and Modal

## Product Guardrails

- one project config: `pyproject.toml`
- one default environment: `.venv`
- one substrate for package/env management: `uv`
- one clear local-first AI workflow
- runtime and policy should be first-class, not bolted on later
- escape hatches are allowed, but secondary
