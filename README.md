# vex

`vex` is an AI-native workflow tool for Python apps.

The goal is not to replace `uv` or rebuild Python packaging. The goal is to make the AI app path obvious:

- create an agent or inference project
- run it locally with good defaults
- benchmark it
- package models and runtime assets
- enforce execution policy and sandboxing
- promote the app to real deployment targets

`vex` should orchestrate mature tools rather than reimplement Python packaging from scratch.

## Product Thesis

Python already has strong building blocks like `uv`, `pytest`, `ruff`, and `hatchling`, and `uv` already owns the generic packaging substrate. `vex` should sit one layer higher and provide:

- one local-first workflow for Python AI apps
- one project model that treats prompts, models, evals, and policies as first-class
- one place to switch between local runtimes and deployment targets
- one place to define execution safety and runtime defaults
- clear escape hatches to the underlying ecosystem, including `uv`

## Initial Direction

The current scaffold is a small `uv`-backed Python prototype. That remains useful as plumbing, but it is no longer the product thesis.

Recommended product direction:

- `uv` for Python installs, envs, resolution, locking, sync, build, publish, and tool execution
- `vex-ai-runtime` for secure packaged inference execution
- local runtimes like `ollama` where appropriate
- eval and benchmark adapters rather than bespoke cloud infrastructure

Recommended target commands:

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

Current prototype commands still expose `uv`-adjacent wrappers. They should be treated as bootstrap functionality, not the long-term differentiator.

## Dream Workflow

The intended shape is closer to this:

```bash
vex init agent customer-support-agent
vex dev
vex benchmark
vex eval --command "python -m app.eval"
vex package-model models/encoder.onnx --out-dir dist/encoder
vex deploy cloud-run --service customer-support-agent
vex policy
vex run --sandbox
```

Under the hood:

- `uv` handles package and environment plumbing
- `vex` handles AI app workflow and policy
- `vex-ai-runtime` handles packaged inference execution

## Planned Commands

- `vex init agent`
- `vex init inference-api`
- `vex dev`
- `vex benchmark`
- `vex eval`
- `vex policy`
- `vex package-model`
- `vex deploy`
- `vex run --sandbox`
- `vex doctor ai`

## Current Implemented AI Commands

- `vex init agent <path>` and `vex init inference-api <path>`
- `vex benchmark --command ... --runs ... --warmup ... --out ...`
- `vex eval --command ... --dataset ... --out ...`
- `vex eval --per-case --command "... {input} ..."` for dataset-driven checks
- `vex policy list|get|set|unset`
- `vex run --sandbox ...`
- `vex package-model <model.onnx> [--skip-compat-check]`
- `vex deploy docker|cloud-run|modal` (with `--apply` / `--run` on supported targets)
- `vex deploy --profile <name>` to load defaults from `deploy.targets.toml`
- deploy profiles support inheritance (`inherit = "default"`) and env interpolation (for example `${VEX_IMAGE_REPO}`)
- `vex schema validate-model [artifact_dir]`

`vex init agent` and `vex init inference-api` now also scaffold `deploy.targets.toml` with `default` and `prod` profiles.

`vex package-model` now emits a versioned manifest with compatibility fields:

```json
{
  "schema_version": "v1",
  "runtime": "vex-ai-runtime",
  "engine": "onnxruntime",
  "model_path": "models/model.onnx"
}
```

## Repository Layout

- `src/vex/`: prototype CLI
- `tests/`: lightweight CLI tests
- `docs/architecture.md`: integration choices and non-goals
- `docs/roadmap.md`: command surface and phased plan
- `../vex-ai-runtime/`: separate runtime repo for native execution and secure model packaging

## Running The Prototype

```bash
PYTHONPATH=src python3 -m vex --help
PYTHONPATH=src python3 -m vex init agent demo-agent
PYTHONPATH=src python3 -m vex init inference-api demo-api
PYTHONPATH=src python3 -m vex benchmark --command "python -c 'print(1)'" --runs 3 --warmup 1
PYTHONPATH=src python3 -m vex eval --command "python -c 'print(1)'" --dataset evals/datasets/cases.jsonl
PYTHONPATH=src python3 -m vex policy list
PYTHONPATH=src python3 -m vex policy set network allow --type str
PYTHONPATH=src python3 -m vex policy get network
PYTHONPATH=src python3 -m vex package-model path/to/model.onnx --out-dir dist/model
PYTHONPATH=src python3 -m vex schema validate-model dist/model
PYTHONPATH=src python3 -m vex deploy cloud-run --service demo-service --apply
PYTHONPATH=src python3 -m vex deploy modal --app-name demo-app --run
PYTHONPATH=src python3 -m vex doctor
PYTHONPATH=src python3 -m vex doctor ai
PYTHONPATH=src python3 -m vex run --sandbox "echo hello"
PYTHONPATH=src python3 -m vex python list
PYTHONPATH=src python3 -m vex test
PYTHONPATH=src python3 -m unittest discover -s tests
```

`vex` currently requires `uv` to be installed and available on `PATH`.

The current codebase is still in transition from generic workflow bootstrap toward the AI-native direction above.

## Repo Strategy

Short answer: keeping `vex` and `vex-ai-runtime` as separate packages is still useful, but a monorepo is likely better during this phase.

- `vex`: workflow/control plane (init/dev/eval/policy/deploy)
- `vex-ai-runtime`: native execution + model artifact validation

Why separate packages still matter:

- cleaner boundaries and dependency surfaces
- runtime can evolve independently
- easier to consume runtime without the full CLI stack

Why a monorepo is likely better right now:

- faster coordinated changes across CLI + runtime schema
- easier refactors during heavy iteration
- less cross-repo sync overhead

The current implementation supports both styles by resolving `vex-ai-runtime` from common locations, and it also supports an explicit override via `VEX_AI_RUNTIME_PATH`.

Current local layout in this workspace:

- `vex/` (main CLI/workflow repo)
- `vex/engine/vex-ai-runtime/` (embedded runtime engine)
