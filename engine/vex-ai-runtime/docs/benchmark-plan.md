# Benchmark Plan

## Goal

Measure whether a native-core inference runtime can deliver a meaningful product win over baseline Python inference setups.

## Primary Metrics

- cold start time
- first inference latency
- steady-state p50 and p95 latency
- throughput under fixed concurrency
- resident memory after startup
- artifact size and deploy complexity

## Baselines

### Baseline A

Python + ONNX Runtime directly.

### Baseline B

Python web wrapper around model execution, for example a minimal FastAPI inference server.

### Candidate Runtime

Rust-backed Python package with packaged model loading and native session management.

## Initial Workloads

Start narrow:

- small embedding model
- small classifier
- reranker-sized model

Avoid large LLM workloads first. They hide startup and packaging wins under raw compute time.

## Environment Controls

- fixed machine type
- fixed Python version
- CPU-only first
- warm-cache and cold-cache runs separated
- repeated process launches for cold-start measurement

## Success Thresholds

Strong early signal:

- clear cold-start improvement on packaged model execution
- simpler deployment artifact story than baseline Python stack
- no major compatibility regressions on chosen fixture models

Weak signal:

- marginal latency improvement only after warmup
- startup wins erased by model loading complexity
- packaging complexity equal to or worse than baseline
