# inference-api

A FastAPI-based inference service with a fake `/predict` endpoint and a
packaged-model workflow wired through `vex package-model`.

## What this shows

- `vex init inference-api` output customised with a real-ish `/predict` route
- A fake inference function that returns a prediction, score, and latency
  metadata (so you can see the response shape without pulling a real model)
- `/healthz` and `/models` read-only routes for deploy preflight and discovery
- How to package a binary placeholder artifact with `vex package-model` so the
  artifact schema is produced end-to-end (swap the placeholder for an `.onnx`
  when you are ready)
- `deploy.targets.toml` with `default` and `prod` profiles wired for Cloud Run
  style `service` + `region` plus an inherited `prod` that pushes the image

## How to run

```bash
cd examples/inference-api
uv sync --extra api

vex dev                              # uvicorn on :8000
# in another shell
curl -s localhost:8000/healthz
curl -s -X POST localhost:8000/predict \
  -H 'content-type: application/json' \
  -d '{"text": "hello world"}' | jq

vex eval                             # runs the JSONL cases against /predict
vex package-model models/stub.bin --name stub-classifier
vex deploy check --for all
vex deploy docker
```

`vex package-model` prints the path to `build/model-artifact/vex-model.json`.

## Files

```
inference-api/
  pyproject.toml                package deps and vex scripts
  deploy.targets.toml           default + prod profiles
  models/stub.bin               32-byte placeholder artifact (see notes)
  src/inference_api/
    __init__.py
    api.py                      FastAPI app with /predict, /healthz, /models
    predictor.py                fake inference with deterministic latency
    schemas.py                  typed request / response models
    benchmark.py                10-run /predict throughput probe
    eval.py                     JSONL-driven /predict correctness check
  evals/
    run_eval.py
    datasets/cases.jsonl        5 cases covering classes + error shapes
```

## Notes on the stub model

`models/stub.bin` is deliberately a tiny binary file with no real meaning.
`vex package-model` hashes it, copies it under `models/`, and writes a
`vex-model.json` manifest shaped like:

```json
{
  "schema": "vex.model",
  "schema_version": "v1",
  "runtime": "vex-ai-runtime",
  "engine": "onnxruntime",
  "name": "stub-classifier",
  "model_path": "models/stub.bin",
  "sha256": "..."
}
```

When you have a real ONNX or TorchScript model, drop it next to `stub.bin` and
re-run `vex package-model`. The manifest stays the same shape and the service
code in `predictor.py` is the single place that needs to load the real artifact.
