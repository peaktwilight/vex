# vex-ai-runtime

`vex-ai-runtime` is an ONNX-first, Rust-backed runtime exploration for fast and secure Python inference workloads.

The near-term goal is not to replace CPython. The goal is to prove a narrower wedge:

- faster cold starts for inference-heavy Python apps
- predictable model packaging
- secure defaults for agent and model execution
- a Python API that feels natural while delegating hot paths to native code

## MVP Direction

The current working direction is:

- Rust core
- ONNX Runtime as the first inference engine
- Python bindings via `pyo3` and `maturin`
- prevalidated, packageable model artifacts rather than arbitrary user-supplied runtime models

That choice optimizes for compatibility and operational simplicity first, with room to add narrower/faster engines later.

## Why This Exists

Python owns the ML ecosystem, but AI deployment is still fragmented:

- slow and inconsistent cold starts
- ad hoc packaging of models and native dependencies
- poor defaults for sandboxing and policy enforcement
- too many hand-rolled local/serverless/agent execution paths

`vex-ai-runtime` explores a product that makes those workflows boring and fast.

## Repository Layout

- `Cargo.toml`: Rust crate for the native runtime core
- `src/lib.rs`: initial PyO3 module surface
- `python/vex_ai_runtime/`: Python-facing package API
- `docs/architecture.md`: MVP architecture and design constraints
- `docs/benchmark-plan.md`: benchmark methodology and target metrics
- `docs/roadmap.md`: phased implementation plan
- `tests/`: lightweight Python tests for the early package surface

## Current Status

This repo is intentionally early. The initial scaffold focuses on:

- product direction
- engine choice
- Rust/Python boundary
- benchmark plan
- minimal package structure

It also includes a first artifact-manifest validator for packaged models. The current manifest contract is intentionally strict and local-only:

```json
{
  "schema": "vex-model/v1",
  "schema_version": "v1",
  "runtime": "vex-ai-runtime",
  "name": "encoder",
  "engine": "onnxruntime",
  "model_path": "models/encoder.onnx",
  "sha256": "...optional..."
}
```

Current validation rules:

- `engine` must be `onnxruntime`
- `schema`, `schema_version`, and `runtime` must match `schemas/vex-model-schema.json`
- `model_path` must be relative
- `model_path` cannot escape the artifact directory
- referenced model file must exist

## Local Development

```bash
cargo test
python3 -m unittest discover -s tests
```

If `maturin` is installed later, the intended dev loop will be:

```bash
maturin develop
python3 -m unittest discover -s tests
```
