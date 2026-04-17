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
- eval tools like `promptfoo` or hosted observability platforms
- deployment targets like Modal, BentoML, Baseten, or custom containers

## Recommended Domain Defaults (MVP)

- **Scaffolding: agent**
  - `PydanticAI`, `pydantic-settings`, typed tool boundaries
- **Scaffolding: inference-api**
  - `FastAPI` + `uvicorn` with typed schemas
- **Benchmark and eval**
  - Python-native harness first, then adapters for `deepeval` and `ragas`
- **Sandboxing**
  - container sandbox backend for local development, network denied by default
- **Deployment adapters**
  - Docker/OCI first, then Cloud Run and Modal as early managed targets

These defaults are intentionally pragmatic and local-first.

## Repo Topology

During rapid iteration, a monorepo is recommended:

- `vex/` (CLI and workflow control plane)
- `vex-ai-runtime/` (native runtime and schema validation)

This keeps schema, packaging, and compatibility changes synchronized.

Long term, the components can still be versioned and released independently. The product boundary stays the same even if source control topology changes.

## Recommended Command Direction

- `vex init agent`
- `vex init inference-api`
- `vex dev`
- `vex benchmark`
- `vex policy`
- `vex package-model`
- `vex run --sandbox`
- `vex doctor ai`

These commands give `vex` a story that is distinct from generic Python tooling.
