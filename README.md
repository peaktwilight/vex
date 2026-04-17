# vex

**The missing AI workflow layer for Python.** Four commands take you from an empty directory to a deployed, evaluated agent.

```bash
vex init agent support-bot   # real PydanticAI agent, settings, eval, deploy profiles
vex dev                      # hot reload + local model fallback + trace tail
vex eval                     # pass/fail over your dataset, CI-ready exit codes
vex deploy modal             # ships it
```

One CLI. One `pyproject.toml`. No yaml sprawl, no duct-taped stack. `vex` rides on top of `uv` and composes the tools you were going to reach for anyway.

---

## Why vex

Python AI apps are a duct-taped stack. You install PydanticAI by hand, bolt on promptfoo, hand-roll a Dockerfile, wire up ollama somewhere, and your eval harness is three scripts glued together. `uv` already owns packaging. Nothing owns the workflow.

`vex` is the workflow. It is explicitly **not** a new resolver, lockfile, or runtime (see [`docs/architecture.md`](docs/architecture.md#non-goals)). It composes:

- [`uv`](https://docs.astral.sh/uv/) — envs, deps, lockfile, Python versions
- [PydanticAI](https://ai.pydantic.dev) + [`pydantic-settings`](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — typed agents and config
- [`ollama`](https://ollama.com) — local-first model fallback when no API key is set
- [`promptfoo`](https://www.promptfoo.dev) / [`deepeval`](https://www.deepeval.com) — evals you can gate CI on
- [`vex-ai-runtime`](engine/vex-ai-runtime/) — native execution and signed model artifacts
- Docker / Cloud Run / Modal — deploy targets that already work

## Install

```bash
uv tool install vex          # recommended
# or run straight from the repo:
PYTHONPATH=src python3 -m vex --help
```

`vex` requires [`uv`](https://docs.astral.sh/uv/) on `PATH`.

## How it composes

```
  pyproject.toml            (single source of truth)
        │
        ├── [tool.vex.scripts]      dev / benchmark / eval / test / lint / format / typecheck
        ├── [tool.vex.policy]       sandbox / network / filesystem / memory / pids
        ├── [tool.vex.ai]           template / runtime selection
        └── [project.optional-dependencies]   agent / api / eval extras
        │
  vex ──┼── uv ──────────── install, lock, sync, python versions, build, publish
        ├── vex-ai-runtime ─ native model load, schema validation, policy enforcement
        ├── ollama ───────── local fallback when no API key
        ├── promptfoo ────── eval adapter (when promptfooconfig.yaml exists)
        └── deploy ───────── docker | cloud-run | modal
```

Every verb is a thin wrapper. Escape hatches everywhere — if you want `uv run foo` directly, go do it.

## What works today

- `vex init agent <path>` — scaffolds a real PydanticAI agent: `agent.py` with a tool, `settings.py` with provider auto-resolution (openai / anthropic / ollama), `main.py` async entrypoint, `eval.py` with PASS/FAIL reporting, five seed eval cases, `prompts/system.md`, `.env.example`, `deploy.targets.toml` with `default` and `prod` profiles
- `vex init inference-api <path>` — FastAPI + uvicorn + typed schemas
- `vex benchmark --command ... --runs ... --warmup ...` — harness with warmup control and JSON output
- `vex eval --command ...` and `vex eval --per-case --command "... {input} ..."` — dataset-driven checks
- `vex eval` auto-delegates to [`promptfoo`](https://www.promptfoo.dev) via `uvx` when `promptfooconfig.yaml` is present. Use `--no-promptfoo` to force the built-in harness, `--json` for machine-readable output, and `--min-pass-rate 0.9` to gate CI on a fraction of passing cases. Override defaults in `[tool.vex.eval]` (`adapter = "auto"|"promptfoo"|"harness"`, `min_pass_rate = 0.9`).
- `vex policy list|get|set|unset` — inspect and override `[tool.vex.policy]`
- `vex run --sandbox ...` — Docker/Podman-backed execution with `--cap-drop ALL`, `--network none`, read-only rootfs, memory + pids caps
- `vex package-model <model.onnx>` — versioned manifest with compatibility metadata:
  ```json
  { "schema_version": "v1", "runtime": "vex-ai-runtime",
    "engine": "onnxruntime", "model_path": "models/model.onnx" }
  ```
- `vex deploy docker|cloud-run|modal [--apply|--run]` — scaffold + execute; profile inheritance (`inherit = "default"`) and env interpolation (`${VEX_IMAGE_REPO}`)
- `vex deploy check [--for all|docker|cloud-run|modal]` — preflight
- `vex schema validate-model [artifact_dir]` — verify a packaged artifact
- `vex doctor ai` — 13-check readiness report

Every generic `uv` verb (`add`, `remove`, `sync`, `lock`, `build`, `publish`, `python`, `tool`, `run`, `test`, `lint`, `format`, `typecheck`) is also exposed as a thin passthrough so a vex project stays a normal Python project.

## Try it

```bash
vex init agent demo
cd demo
uv sync --extra agent
vex doctor ai                 # expect mostly green
vex dev                       # talks to your configured model (or ollama fallback)
vex eval                      # runs the seed dataset, prints PASS/FAIL
vex deploy check --for all
```

No API key? `vex` falls back to a local [`ollama`](https://ollama.com) model — no code changes.

## Repository layout

- `src/vex/` — CLI and workflow control plane
- `engine/vex-ai-runtime/` — Rust + PyO3 runtime for native execution and model artifact validation
- `tests/` — CLI test suite
- `docs/` — architecture, product boundary, roadmap
- `.github/workflows/` — CI for CLI + runtime

## Where this is going

The roadmap ([`docs/roadmap.md`](docs/roadmap.md)) and product boundary ([`docs/product-boundary.md`](docs/product-boundary.md)) spell it out:

- `vex dev` upgraded to a real dev loop: [`watchfiles`](https://watchfiles.helpmanual.io) hot reload + local ollama fallback + inline trace tail
- `vex eval` adapters for promptfoo and deepeval, with `--json` CI output and pass-rate gates
- `vex deploy modal|cloud-run` as full end-to-end deployments, not just scaffolding
- `vex doctor ai` extended to verify ollama availability, model reachability, eval dataset shape, deploy profile env vars
- More opinionated `examples/` tree with runnable agents, inference APIs, and local RAG

## Design principles

Lifted verbatim from [`docs/architecture.md`](docs/architecture.md):

1. `pyproject.toml` is the source of truth.
2. Default to a local `.venv` per project.
3. Prefer delegation to mature tools over reimplementation.
4. Keep the command surface small.
5. Optimize for AI app developers first.
6. Treat runtime choice, policy, and model packaging as first-class workflow concerns.

## Running the test suite

```bash
make test
```

Runs the Python CLI tests and the `vex-ai-runtime` Rust + Python tests.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full dev loop.

---

vex is early. Expect sharp edges, missing polish, and a few commands that still read as bootstrap plumbing. The direction is firm: make the AI app path obvious, one composed workflow at a time.
