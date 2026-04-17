# Product Boundary

## Short Version

- `uv` owns Python packaging substrate
- `vex` owns AI application workflow
- `vex-ai-runtime` owns native inference execution and secure model artifacts

## What Vex Should Not Compete On

`vex` should not try to beat `uv` at:

- dependency installation speed
- virtualenv management
- Python version installation
- universal lockfiles
- generic Python workspace management

Those are already strong enough that competing there weakens the product story.

## What Vex Should Own

`vex` should own the developer workflow for Python AI applications:

- AI project scaffolding
- local development loops for agents and inference APIs
- runtime selection and switching
- benchmarking and evaluation entry points
- policy and sandbox defaults
- model packaging orchestration
- promotion to deployment targets

## What vex-ai-runtime Should Own

`vex-ai-runtime` should own the lower-level execution path:

- native model artifact loading
- runtime session creation
- secure packaged artifact validation
- native execution policies
- cold-start and packaged-runtime optimization

## Relationship To Existing Ecosystem Tools

`vex` should integrate rather than replace:

- `uv` for package/env management
- `ollama` for local model runtime where useful
- agent frameworks like `PydanticAI` or `LangGraph`
- eval tools like `Inspect AI` (intended default), `promptfoo`, or hosted
  observability platforms
- observability adapters like `Logfire` / OTel GenAI
- deployment targets like Modal, BentoML, Baseten, or custom containers

## Recommended Domain Defaults (MVP)

- **Scaffolding: agent**
  - `PydanticAI`, `pydantic-settings`, typed tool boundaries
- **Scaffolding: inference-api**
  - `FastAPI` + `uvicorn` with typed schemas
- **Benchmark and eval**
  - Inspect AI by default, promptfoo as opt-in adapter, Python harness as
    fallback (see [`eval.md`](eval.md) for adapter precedence)
- **Sandboxing**
  - container sandbox backend for local development, network denied by default
    (see [`policy.md`](policy.md) for the full `[tool.vex.policy]` schema)
- **Deployment adapters**
  - Docker/OCI, Cloud Run, and Modal are all shipped with
    `vex deploy <target> --apply|--run` (see [`deploy.md`](deploy.md) for
    target-specific behavior and `deploy.targets.toml`)
- **Observability**
  - Logfire / OTel GenAI are the intended adapters so traces from
    `vex dev` and production inference stay on a shared schema

These defaults are intentionally pragmatic and local-first.

## Repo Topology

During rapid iteration, a monorepo is recommended:

- `vex/` (CLI and workflow control plane)
- `engine/vex-ai-runtime/` (native runtime and schema validation)

This keeps schema, packaging, and compatibility changes synchronized.

Long term, the components can still be versioned and released independently.
The product boundary stays the same even if source control topology changes.

## Command Surface

AI-native workflow commands that give `vex` a story distinct from generic
Python tooling:

- `vex init agent`
- `vex init inference-api`
- `vex dev`
- `vex benchmark`
- `vex eval` (see [`eval.md`](eval.md))
- `vex policy` (see [`policy.md`](policy.md))
- `vex package-model`
- `vex deploy` (see [`deploy.md`](deploy.md))
- `vex deploy check`
- `vex schema validate-model`
- `vex run --sandbox`
- `vex doctor ai`
