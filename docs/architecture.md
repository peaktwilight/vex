# Architecture

## Goal

`vex` should unify the Python AI app workflow without inventing a parallel
packaging ecosystem.

It should explicitly build on top of `uv`, not compete with `uv`.

## MVP Principles

1. Use `pyproject.toml` as the source of truth.
2. Default to a local `.venv` per project.
3. Prefer delegation to mature tools over reimplementation.
4. Keep the command surface small.
5. Optimize for AI app developers first.
6. Treat runtime choice, policy, and model packaging as first-class workflow concerns.

## Layered Architecture

`vex` is a thin control plane that composes existing tools. Every verb is a
wrapper; the real work happens in the adapter layer below.

```
  pyproject.toml  +  deploy.targets.toml       (single source of truth)
        │
        ▼
  src/vex/cli.py                               (control plane)
  argparse surface, config loading, provider resolution,
  [tool.vex.scripts] + [tool.vex.policy] + [tool.vex.eval] + [tool.vex.ai]
        │
        ▼
  ┌──────────────┬──────────────┬──────────────┬──────────────────┐
  │  eval layer  │ deploy layer │ sandbox layer│   runtime layer  │
  │              │              │              │                  │
  │  harness     │  docker      │  docker /    │ vex-ai-runtime   │
  │  promptfoo   │  cloud-run   │  podman      │ (native model    │
  │  Inspect AI  │  modal       │  execution   │  load + policy)  │
  │  (intended)  │              │              │                  │
  └──────────────┴──────────────┴──────────────┴──────────────────┘
        │
        ▼
  composed tools (subprocess calls, no reimplementation)
  uv · PydanticAI · ollama · promptfoo · Inspect AI (intended)
  Modal · gcloud / Cloud Run · Docker/Podman · watchfiles
  Logfire / OTel GenAI (intended) · vex-ai-runtime
```

Read top-to-bottom: config declares intent, the CLI resolves it, adapters pick
the right backend, and the actual work is delegated to a mature tool. `vex`
itself owns no resolver, lockfile, runtime, or eval executor.

Detailed reading per layer:

- Eval layer — see [`eval.md`](eval.md) for adapter precedence, the
  `vex-eval/v1` schema, and `--min-pass-rate` semantics.
- Deploy layer — see [`deploy.md`](deploy.md) for `deploy.targets.toml`
  schema, profile inheritance, env interpolation, and preflight.
- Sandbox layer — see [`policy.md`](policy.md) for the `[tool.vex.policy]`
  schema and what `vex run --sandbox` actually enforces.
- Runtime layer — see [`engine/vex-ai-runtime/`](../engine/vex-ai-runtime/)
  for the native execution path and packaged artifact validation.

## Recommended Integration Stack

### Core Substrate

- `uv`
  - Python installation and pinning
  - virtual environment creation
  - dependency add/remove/lock/sync
  - command execution
  - build and publish delegation
  - isolated tool execution

### AI Workflow Layer

- `vex-ai-runtime`
  - secure packaged model artifacts (`vex-model/v1` schema)
  - native inference execution
  - runtime policy enforcement
- local model runtimes like `ollama`
  - local development and fallback execution paths when no hosted API key is set
- eval adapters
  - Python harness (built-in, always available)
  - promptfoo (opt-in, auto-delegates when `promptfooconfig.yaml` exists)
  - Inspect AI (intended default, tracked in issue #23)
- deployment adapters
  - Docker/OCI, Google Cloud Run, and Modal — all shipped end-to-end with
    `--apply`/`--run`
- observability adapters
  - Logfire / OTel GenAI (intended, tracked in issue #24)
- `watchfiles`
  - generic dev reload support for `vex dev`

## Non-Goals

- custom dependency resolver
- custom lockfile format in v0
- custom build backend
- a generic replacement for `uv`
- a new general-purpose Python runtime in the initial `vex` product

## Why AI Workflow Is The Better Wedge

`uv` already solved a large part of generic Python workflow. The remaining open
space is higher-level and AI-specific:

- local-first AI app workflow is still fragmented
- model packaging and execution policy are not first-class in generic Python tools
- deployment and runtime choices are still split across many products
- AI app packaging is not the same thing as Python dependency management

The better wedge for `vex` is an AI-native workflow layer that can later
orchestrate `vex-ai-runtime` and other execution backends.
