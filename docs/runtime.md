# Runtime

`vex-ai-runtime` is the native-execution half of the vex product boundary.
Where `vex` owns the AI workflow surface in Python, `vex-ai-runtime` owns
secure model artifact loading and runtime policy. The two sides communicate
through the shared `vex-model/v1` manifest contract.

Repo layout under [`engine/vex-ai-runtime/`](../engine/vex-ai-runtime/):

- `Cargo.toml` — Rust crate (`vex-ai-runtime`, `cdylib` + `rlib`).
- `src/lib.rs` — PyO3 module `_core` with `runtime_info` and `healthcheck`
  entry points.
- `python/vex_ai_runtime/` — Python facade: `__init__.py` re-exports the
  native functions (or Python fallbacks when the extension is not built),
  and `artifacts.py` implements `ArtifactManifest` + `load_artifact_manifest`.
- `schemas/vex-model-schema.json` — shared schema file consumed by both
  `vex` and the runtime's validator.
- `pyproject.toml` — `maturin` build backend, `module-name =
  "vex_ai_runtime._core"`.

## What it does today

- Native model artifact loading. `load_artifact_manifest(root)` reads
  `vex-model.json` from an artifact directory, validates every field, and
  resolves the referenced model file relative to the artifact root.
- `vex-model/v1` schema validation. The runtime rejects manifests whose
  `schema`, `schema_version`, `runtime`, or `engine` values do not match
  `schemas/vex-model-schema.json`.
- Runtime policy enforcement on the load path. `model_path` must be
  relative and must not escape the artifact directory; the referenced file
  must exist; `sha256` (when present) must be a string. `engine` is pinned
  to `onnxruntime` for the MVP.
- A stable Python surface that keeps working without the native extension.
  `healthcheck()` returns `"ok"` when built with `maturin`,
  `"native-extension-unavailable"` otherwise; `NATIVE_AVAILABLE` is the
  boolean flag to branch on.

## The `vex-model/v1` schema

Manifest shape (`vex-model.json` at the artifact root):

```json
{
  "schema": "vex-model/v1",
  "schema_version": "v1",
  "runtime": "vex-ai-runtime",
  "name": "encoder",
  "engine": "onnxruntime",
  "model_path": "models/encoder.onnx",
  "sha256": "..."
}
```

Field semantics:

- `schema` — always `"vex-model/v1"`. Stamped from
  `engine/vex-ai-runtime/schemas/vex-model-schema.json` when the runtime is
  resolvable, else from the constant `VEX_MODEL_SCHEMA_ID` in `vex`. Drift
  between the two sides is surfaced by `vex doctor ai` — see
  [`doctor.md`](doctor.md#schema-drift).
- `schema_version` — currently `"v1"`; reserved for breaking schema
  evolution.
- `runtime` — always `"vex-ai-runtime"` for this contract.
- `name` — non-empty human-readable name. Defaults to the source file's
  stem when `vex package-model` is called without `--name`.
- `engine` — pinned to `"onnxruntime"` for v1. Additional engines are
  deferred.
- `model_path` — path to the model binary, relative to the artifact root.
  Absolute paths and `..` segments are rejected.
- `sha256` — optional hex digest of the source model. `vex package-model`
  computes it with `hashlib.sha256` when `--sha256` is not passed.

Producer: `vex package-model <model> [--out-dir build/model-artifact]
[--name <n>] [--sha256 <hex>] [--skip-compat-check]` copies the model into
`<out-dir>/models/` and writes `<out-dir>/vex-model.json`. Every stamped
field comes from `load_shared_model_schema`, which prefers the runtime's
schema file over the `vex` constants. See
[`cli-reference.md`](cli-reference.md#vex-package-model).

Consumer: `vex schema validate-model <artifact_dir> [--strict-runtime]`
runs the same load path the runtime uses — it will refuse to approve an
artifact the runtime would refuse to load. See
[`cli-reference.md`](cli-reference.md#vex-schema-validate-model).

## When you need the runtime

- Serving a packaged model artifact at native speed from an
  `inference-api` scaffold.
- Validating an artifact's manifest against the same rules the runtime
  will apply (`vex schema validate-model`).
- Producing a manifest whose schema fields match a specific
  `vex-ai-runtime` checkout — useful in CI when vex and the runtime are
  versioned together.

## When you don't

- The `vex dev` loop on a scaffolded agent. PydanticAI calls out to a
  hosted provider or ollama; the runtime is not on this path.
- `vex eval` against any of the three adapters (`harness`, `promptfoo`,
  `inspect`). Evals run the project's command under `uv run`, not through
  the runtime.
- Any of the deploy targets' scaffolds (`docker`, `cloud-run`, `modal`).
  Deploy surface is the user's own `Dockerfile` / Modal app / Cloud Run
  service; wiring in the runtime is optional.

## Vendoring the runtime

`vex` looks up the runtime in this order (see `resolve_runtime_root` in
[`src/vex/cli.py`](../src/vex/cli.py)):

1. `$VEX_AI_RUNTIME_PATH` when exported and pointing at an existing path.
2. `<project>/engine/vex-ai-runtime/`
3. `<project parent>/vex-ai-runtime/`
4. `<project>/vex-ai-runtime/`
5. `<project parent parent>/vex-ai-runtime/`
6. `<project>/packages/vex-ai-runtime/`

Example layouts:

```
# Sibling checkout
workspace/
├── my-agent/
│   └── pyproject.toml
└── vex-ai-runtime/
    ├── schemas/vex-model-schema.json
    └── ...

# Vendored into the project
my-agent/
├── pyproject.toml
└── packages/vex-ai-runtime/
    └── schemas/vex-model-schema.json

# Explicit override
export VEX_AI_RUNTIME_PATH=/opt/vex-ai-runtime
```

`vex doctor ai` echoes the resolved path as
`OK  runtime path resolved to <path>`, or warns when nothing is found. When
the runtime is missing, `vex package-model` still works (it falls back to
the `VEX_MODEL_SCHEMA_ID` / `VEX_MODEL_SCHEMA_VERSION` constants baked into
`vex`), but schema drift cannot be detected.

## Building from source

Inside the monorepo:

```bash
# Rust core
cargo test --manifest-path engine/vex-ai-runtime/Cargo.toml
cargo build -p vex-ai-runtime --release

# Python surface (pure Python, runs without the native extension)
python3 -m unittest discover -s engine/vex-ai-runtime/tests

# Native extension via maturin (PyO3 cdylib -> vex_ai_runtime._core)
pip install maturin
maturin develop --manifest-path engine/vex-ai-runtime/Cargo.toml
```

The `Makefile` targets `test-runtime-python` and `test-runtime-rust` wrap
the first two invocations; `make test` runs the full `vex` + runtime
matrix. Release builds (`maturin build`) are driven by
[`.github/workflows/release.yml`](../.github/workflows/release.yml) on
version tags.

See also: [`architecture.md`](architecture.md),
[`product-boundary.md`](product-boundary.md),
[`cli-reference.md`](cli-reference.md), [`policy.md`](policy.md),
[`doctor.md`](doctor.md).
