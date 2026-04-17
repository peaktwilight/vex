# Runtime

vex-ai-runtime is the native execution layer. It is implemented in Rust with
PyO3 bindings and is versioned alongside vex in the `engine/vex-ai-runtime/`
directory of the monorepo.

## Responsibilities

- load packaged model artifacts produced by `vex package-model`
- validate artifact manifests against the shared `vex-model-schema.json`
- create runtime sessions for native inference execution
- enforce runtime policies declared under `[tool.vex.policy]`

## Artifact shape

`vex package-model model.onnx` writes a manifest like:

```json
{
  "schema": "vex.model",
  "schema_version": "v1",
  "runtime": "vex-ai-runtime",
  "engine": "onnxruntime",
  "name": "model",
  "model_path": "models/model.onnx",
  "sha256": "..."
}
```

The default engine is `onnxruntime`. The runtime name is always
`vex-ai-runtime`.
