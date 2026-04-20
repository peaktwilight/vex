# Templates

A `vex` template is the scaffold that `vex init <template> <path>` lays down
on top of `uv init`. Each template is a fixed tree of files plus a
`[tool.vex]` block appended to `pyproject.toml` — the conventions are the
product, not the individual files. Ground truth for every file emitted is
`scaffold_agent_template` and `scaffold_inference_template` in
[`src/vex/cli.py`](../src/vex/cli.py).

Two templates ship today:

- `agent` — PydanticAI-based chat / tool-use agent with typed settings and a
  dataset-driven eval harness.
- `inference-api` — FastAPI + uvicorn service with a `/healthz` endpoint
  ready for `vex package-model` wiring.

Both scaffolds install in package mode (`package-mode = true`, `uv init
--package --build-backend hatch`) so `python -m <pkg>.main` resolves without
`PYTHONPATH` tricks, normalize `requires-python` to `>=3.11`, and write
`deploy.targets.toml` with `default` and `prod` profiles. Policy defaults
(`[tool.vex.policy]`) are the same for both — see [`policy.md`](policy.md).

## `vex init agent <path>`

Tree:

```
<path>/
├── .env.example
├── .python-version
├── deploy.targets.toml
├── pyproject.toml
├── prompts/
│   └── system.md
├── src/<pkg>/
│   ├── __init__.py
│   ├── agent.py
│   ├── benchmark.py
│   ├── eval.py
│   ├── main.py
│   └── settings.py
├── evals/
│   ├── run_eval.py
│   └── datasets/
│       ├── .gitkeep
│       └── cases.jsonl
└── tests/
    └── test_smoke.py
```

Per file:

- `src/<pkg>/settings.py` — `pydantic_settings.BaseSettings` subclass with a
  `VEX_` env prefix, `.env` loader, and `resolve_provider()` /
  `model_spec()` helpers. Picks `openai` when `OPENAI_API_KEY` is set,
  `anthropic` when `ANTHROPIC_API_KEY` is set, falls back to `ollama`. This
  file is the first thing to edit when adding a new provider knob.
- `src/<pkg>/agent.py` — `build_agent(settings)` that constructs a
  `pydantic_ai.Agent` from the resolved model spec, loads the system prompt
  from `prompts/system.md`, and registers a single `lookup_faq` tool as a
  placeholder. Add your tools here.
- `src/<pkg>/main.py` — CLI entry point. Runs the agent with a prompt from
  argv, prints the resolved provider / model banner, and wires
  `logfire.instrument_pydantic_ai()` when `LOGFIRE_TOKEN` is exported.
  `vex dev` invokes this module via `[tool.vex.scripts].dev`.
- `src/<pkg>/benchmark.py` — minimal warmup-free latency sampler. Targeted
  by `[tool.vex.scripts].benchmark` and re-run via `vex benchmark`.
- `src/<pkg>/eval.py` — the package-local eval harness. Reads
  `evals/datasets/cases.jsonl`, runs each case through `build_agent()`, and
  prints pass/fail. Swap this out for an Inspect AI task or a promptfoo
  config once you outgrow substring matching.
- `prompts/system.md` — system prompt text. Plain markdown; not templated.
- `evals/run_eval.py` — thin wrapper that `[tool.vex.scripts].eval` invokes
  (`python evals/run_eval.py --input {input}`). Forwards to the package's
  `eval.py`.
- `evals/datasets/cases.jsonl` — seed dataset, one JSON object per line
  (`input`, `expect_contains`). Schema documented in
  [`eval.md`](eval.md#authoring-evalsdatasetscasesjsonl).
- `.env.example` — commented-out provider keys and overrides (`VEX_PROVIDER`,
  `VEX_OPENAI_MODEL`, `LOGFIRE_TOKEN`, `OTEL_EXPORTER_OTLP_ENDPOINT`). Copy
  to `.env` and fill in.
- `deploy.targets.toml` — see [`deploy.md`](deploy.md) for the schema.
  `[profiles.default]` points at `ghcr.io/example/<pkg>` with a `<pkg>-agent`
  service / app name; `[profiles.prod]` overrides the tag to `prod` and
  enables `push`.
- `pyproject.toml` — `[project.optional-dependencies].agent` pins
  `pydantic-ai`, `pydantic-settings`, `httpx`, `tenacity`. `eval` extra adds
  `deepeval` and `ragas`; `observability` adds `logfire`. Install with
  `uv sync --extra agent`.
- `tests/test_smoke.py` — placeholder `assert True` so `vex test` passes on
  a fresh scaffold.

User-customizable: every file under `src/<pkg>/`, `prompts/`, `evals/`, plus
`.env.example`. `deploy.targets.toml` and the `[tool.vex.*]` blocks are
intended to be edited in place.

## `vex init inference-api <path>`

Tree:

```
<path>/
├── .python-version
├── deploy.targets.toml
├── pyproject.toml
├── src/<pkg>/
│   ├── __init__.py
│   ├── api.py
│   ├── benchmark.py
│   └── eval.py
├── evals/
│   ├── run_eval.py
│   └── datasets/
│       ├── .gitkeep
│       └── cases.jsonl
└── tests/
    └── test_smoke.py
```

Per file:

- `src/<pkg>/api.py` — FastAPI `app` with a `/healthz` endpoint and a
  `uvicorn.run` block guarded by `__name__ == "__main__"`. `vex dev`
  invokes this module via `[tool.vex.scripts].dev`
  (`python -m <pkg>.api`). Add your `/predict` handler here.
- `src/<pkg>/benchmark.py` — stub benchmark for `vex benchmark` to reach
  before you wire real latency measurement.
- `src/<pkg>/eval.py` — argparse-driven stub that reads
  `evals/datasets/cases.jsonl` and prints the case count. Replace with a
  real HTTP-driven eval once the `/predict` handler exists.
- `evals/run_eval.py` — standalone (not a package wrapper this time);
  targeted by `[tool.vex.scripts].eval`.
- `evals/datasets/cases.jsonl` — single-case seed dataset.
- `deploy.targets.toml` — `<pkg>-api` service and app names, otherwise the
  same shape as the agent scaffold.
- `pyproject.toml` — `[project.optional-dependencies].api` pins `fastapi`,
  `uvicorn[standard]`, `pydantic-settings`, `httpx`, `tenacity`. `eval`
  extra same as the agent template. Install with `uv sync --extra api`.
- `tests/test_smoke.py` — placeholder smoke test.

User-customizable: `api.py` (the whole point of the template), `eval.py`,
the dataset, and the deploy profile. The other files are scaffold scaffolding.

Pair with [`vex package-model`](cli-reference.md#vex-package-model) and
[`vex schema validate-model`](cli-reference.md#vex-schema-validate-model)
when the API is serving a packaged `vex-model/v1` artifact — see
[`runtime.md`](runtime.md).

## Framework variants

The current `agent` template hardcodes PydanticAI. The `--framework` flag is
not yet on `main`; adding LangGraph and Claude Agent SDK variants is tracked
in [issue #45](https://github.com/peaktwilight/vex/issues/45). Once it lands,
this section will cover all three side by side. For now:

- PydanticAI is the default because its typed tool boundary, `RunContext`
  usage pattern, and native Logfire hook match the rest of the vex surface.
- LangGraph and Claude Agent SDK will be opt-in via `--framework langgraph`
  and `--framework claude-agent-sdk` once #45 ships. Pick your framework at
  `vex init` time; the rest of the scaffold (`settings.py`, `eval.py`,
  `deploy.targets.toml`, policy defaults) will stay the same shape.

## Customizing the scaffold

The templates are emitted by a handful of helper functions, not loaded from
template files on disk. To change what `vex init` lays down:

- `scaffold_agent_template(root, package_name)` —
  [`src/vex/cli.py`](../src/vex/cli.py) — controls every file under the
  agent tree.
- `scaffold_inference_template(root, package_name)` —
  same file — controls the inference-api tree.
- `append_vex_config(root, package_mode, template, package_name)` —
  controls the `[tool.vex.*]` blocks and the optional-dependency table.
- `scaffold_deploy_targets(root, package_name, template)` —
  controls `deploy.targets.toml`.

For one-off edits, scaffold a project with `vex init` and edit the output.
To fork the scaffold as a starting point, copy the generated tree into
your own template repo and add the files you need — vex does not re-read
its templates after init, so a forked tree stays a plain uv project the
rest of the way.

See also: [`policy.md`](policy.md), [`eval.md`](eval.md),
[`deploy.md`](deploy.md), [`cli-reference.md`](cli-reference.md),
[`runtime.md`](runtime.md).
