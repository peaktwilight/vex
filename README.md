# vex

**vex is the only Python agent CLI with a portable execution contract.**

Declare what your agent is allowed to do in `pyproject.toml`, then run, evaluate, and ship it under that same contract.

```toml
# pyproject.toml
[tool.vex.policy]
sandbox           = true
network           = "deny"
filesystem        = "project"
sandbox_backend   = "auto"       # podman | docker | auto
sandbox_memory_mb = 1024
sandbox_pids_limit = 128
unsafe_fallback   = false
```

```bash
vex run --sandbox python -m support_bot     # runs under cap-drop ALL, network none, read-only rootfs
vex policy list                             # prints the effective contract
```

`vex deploy` is the same contract, pointed at Modal / Cloud Run / Docker. `vex eval` is the same contract, pointed at a dataset. The policy that makes the agent safe in production is the policy your evals already ran under — one artifact, three execution surfaces.

All three shipped today. `vex run --sandbox` enforces the contract locally. `vex eval --policy` runs every adapter (harness / promptfoo / Inspect AI) inside the sandbox defined by `[tool.vex.policy]`, so an eval case that needs forbidden network egress fails the same way the deployed agent would. `vex deploy --policy-gate` hard-fails on permissive policy and re-expresses `[tool.vex.policy]` as the target's native primitive (docker cap-drop, Cloud Run `--no-allow-unauthenticated`, Modal scaffold audit). One artifact, three execution surfaces, one pass/fail boundary.

## Not another `langgraph new`

LangGraph CLI ships `langgraph new → langgraph dev → langgraph deploy`. Modal CLI ships `modal serve → modal deploy`. Both are good. Neither treats the agent's execution policy as a portable first-class artifact.

`vex` does. `[tool.vex.policy]` is declared once and re-expressed as the deploy target's native primitive: Modal sandbox config on Modal, IAM + VPC egress on Cloud Run, `--cap-drop` + `--network none` on a local container. Same contract, different substrate. You get the LangGraph-style workflow on top, but the policy is the headline — not the four commands.

---

## The workflow that makes the contract observable

```bash
vex init agent support-bot   # scaffolds a PydanticAI agent under a default policy
vex dev                      # watchfiles reload + provider banner + ollama fallback
vex eval                     # PASS/FAIL over your dataset, CI-ready exit codes
vex deploy modal             # ships it (preflight runs automatically)
```

One CLI. One `pyproject.toml`. No yaml sprawl. `vex` rides on top of `uv` and composes the tools you were going to reach for anyway.

## How it composes

```
  pyproject.toml            (single source of truth)
        │
        ├── [tool.vex.policy]       sandbox / network / filesystem / memory / pids
        ├── [tool.vex.scripts]      dev / benchmark / eval / test / lint / format / typecheck
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

## Works on a plane

`vex dev` does not require an API key, a LangSmith account, or a Modal account to get running:

- `uv` handles Python install, venv, and deps — nothing Python-specific to set up
- No `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` set? The scaffolded agent falls back to a local [`ollama`](https://ollama.com) model with no code changes
- The sandbox runs against a local `podman` or `docker` daemon — no cloud round-trip

Compared side by side: LangGraph Platform wants LangSmith auth to get the full dev loop; Modal needs a `modal.com` account before `modal serve` does anything. `vex dev` wants `uv` on your `$PATH`.

## Install

```bash
uv tool install vex          # recommended
# or run straight from the repo:
PYTHONPATH=src python3 -m vex --help
```

`vex` requires [`uv`](https://docs.astral.sh/uv/) on `PATH`.

## What works today

Policy and sandbox (the contract):

- `vex policy list|get|set|unset` — inspect and override `[tool.vex.policy]`
- `vex run --sandbox ...` — Docker/Podman-backed execution with `--cap-drop ALL`, `--network none`, read-only rootfs, memory + pids caps

Eval / deploy / doctor / init:

- `vex eval --command ...` and `vex eval --per-case --command "... {input} ..."` — dataset-driven checks
- `vex eval` auto-delegates to [Inspect AI](https://inspect.aisi.org.uk/) (default) via `uvx --from inspect-ai inspect` when `inspect.yaml` / `inspect.toml` or `evals/*.inspect.py` is present, with [`promptfoo`](https://www.promptfoo.dev) (opt-in) as a fallback when `promptfooconfig.yaml` is present. Use `--adapter inspect|promptfoo|harness|auto` to override, `--json` for machine-readable output, `--min-pass-rate 0.9` to gate CI on a fraction of passing cases, and `--policy` to run every adapter inside the `[tool.vex.policy]` sandbox (stamps a `policy` block into the report). Override defaults in `[tool.vex.eval]` (`adapter = "auto"|"inspect"|"promptfoo"|"harness"`, `min_pass_rate = 0.9`). `--no-promptfoo` is kept as a deprecated alias for `--adapter harness`.
- `vex deploy docker|cloud-run|modal [--apply|--run] [--policy-gate]` — scaffold + ship end-to-end; `docker --run` builds and runs locally, `cloud-run --apply` runs `gcloud builds submit` then `gcloud run deploy` and echoes the service URL, `modal --run` invokes `modal deploy` and surfaces the `*.modal.run` URL. Profile inheritance (`inherit = "default"`), env interpolation (`${VEX_IMAGE_REPO}`), and Cloud Run profile fields (`project`, `memory`, `cpu`, `min_instances`, `max_instances`, `service_account`, `allow_unauthenticated`). `--policy-gate` (opt-in) hard-fails on permissive policy and translates `[tool.vex.policy]` into target-native primitives — see [`docs/deploy.md`](docs/deploy.md). Preflight runs automatically on `--apply`/`--run` (override with `--skip-preflight`)
- `vex deploy check [--for all|docker|cloud-run|modal]` — preflight
- `vex doctor ai` — readiness report (uv, pyproject, policy, provider env, ollama reachability, eval dataset shape, deploy profile env vars)
- `vex init agent <path>` — scaffolds a real PydanticAI agent: `agent.py` with a tool, `settings.py` with provider auto-resolution (openai / anthropic / ollama), `main.py` async entrypoint, `eval.py` with PASS/FAIL reporting, five seed eval cases, `prompts/system.md`, `.env.example`, `deploy.targets.toml` with `default` and `prod` profiles
- `vex init inference-api <path>` — FastAPI + uvicorn + typed schemas
- `vex dev` — watchfiles reload + provider banner, with `--no-reload` / `--watch` / `--provider-check` flags
- `vex benchmark --command ... --runs ... --warmup ...` — harness with warmup control and JSON output
- `vex package-model <model.onnx>` — versioned manifest with compatibility metadata:
  ```json
  { "schema_version": "v1", "runtime": "vex-ai-runtime",
    "engine": "onnxruntime", "model_path": "models/model.onnx" }
  ```
- `vex schema validate-model [artifact_dir]` — verify a packaged artifact

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

## Where this is going

The policy contract keeps getting sharper:

- Trace tail in `vex dev` — inline LLM / tool-call trace view during the reload loop
- Inspect AI adapter as the default eval backend (see [issue #23](https://github.com/peaktwilight/vex/issues/23))
- Logfire + OTel GenAI observability hook on scaffolded agents (see [issue #24](https://github.com/peaktwilight/vex/issues/24))

See [`docs/roadmap.md`](docs/roadmap.md) and [`docs/product-boundary.md`](docs/product-boundary.md) for the longer view.

## Repository layout

- `src/vex/` — CLI and workflow control plane
- `engine/vex-ai-runtime/` — Rust + PyO3 runtime for native execution and model artifact validation
- `tests/` — CLI test suite
- `docs/` — architecture, product boundary, roadmap
- `.github/workflows/` — CI for CLI + runtime

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

vex is early. Expect sharp edges, missing polish, and a few commands that still read as bootstrap plumbing. The direction is firm: give Python agents a portable execution contract, and make the four-command workflow a consequence of that contract, not a substitute for it.
