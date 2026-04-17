# Roadmap

## Phase 0

- settle engine choice
- define product boundary vs `vex`
- establish benchmark plan
- scaffold Rust/Python project

## Phase 1

- wrap ONNX Runtime from Rust
- expose a tiny Python API
- load a packaged model artifact
- run one benchmarkable inference path
- measure cold start and first inference latency

## Phase 2

- define packaging format for trusted model artifacts
- add runtime configuration validation
- add artifact hashing and metadata
- compare packaged runtime against direct Python baselines

## Phase 3

- introduce secure execution policies
- add more realistic agent and API integration patterns
- investigate reduced-op/minimal runtime builds
- decide whether to keep ONNX Runtime-only or add a second backend

## Deferred Bets

- edge/WASM runtime target
- general Python transpilation
- multi-provider GPU support
- general agent sandbox orchestration
