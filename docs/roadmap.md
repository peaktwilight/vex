# Roadmap

`vex` is an AI workflow layer that rides on top of `uv`. The roadmap is split
into three buckets: what's **Shipped** and verified by the test suite, what's
**Next** on the path to v1, and what's **Later** (still in scope, but not the
current focus).

Paired reading: [`architecture.md`](architecture.md),
[`product-boundary.md`](product-boundary.md),
[`policy.md`](policy.md), [`deploy.md`](deploy.md), [`eval.md`](eval.md).

## Shipped

Generic `uv` passthroughs — these are bootstrap plumbing so a vex project stays
a normal Python project, not the long-term moat:

- `vex init`, `vex add`, `vex remove`, `vex sync`, `vex lock`
- `vex run`, `vex test`, `vex lint`, `vex format`, `vex typecheck`
- `vex doctor`, `vex build`, `vex publish`
- `vex python install|pin|list|path|uninstall`
- `vex tool run|install|list|upgrade|uninstall`

AI-native workflow (the actual product):

- `vex init agent` — PydanticAI agent scaffold with `agent.py`, `settings.py`
  (openai / anthropic / ollama auto-resolution), `eval.py`, seed dataset,
  `.env.example`, `deploy.targets.toml` with `default` and `prod` profiles
- `vex init inference-api` — FastAPI + uvicorn scaffold with typed schemas
- `vex dev` — watchfiles-based hot reload plus a provider banner that reports
  which model backend (hosted or ollama fallback) will be used
- `vex benchmark` — warmup-aware harness with JSON output
- `vex eval` — dataset-driven checks with `--json`, `--min-pass-rate`, and a
  promptfoo adapter that auto-delegates when `promptfooconfig.yaml` is present
- `vex policy list|get|set|unset` — read and override `[tool.vex.policy]`
- `vex package-model` — versioned manifest with compatibility metadata for
  `vex-ai-runtime`
- `vex deploy docker|cloud-run|modal` — scaffold and end-to-end ship. `--apply`
  and `--run` drive real subprocess calls (`docker build`, `gcloud builds
  submit` + `gcloud run deploy`, `modal deploy`) and surface the deployed URL.
  Supports profile inheritance (`inherit = "default"`) and env interpolation
  (`${VEX_IMAGE_REPO}`)
- `vex deploy check [--for all|docker|cloud-run|modal]` — preflight readiness
  for each target, also runs automatically before `--apply`/`--run`
- `vex schema validate-model` — verify a packaged artifact against the shared
  `vex-model/v1` schema
- `vex run --sandbox` — Docker/Podman-backed execution with `--cap-drop ALL`,
  `--network none`, read-only rootfs, memory and pids caps,
  `no-new-privileges`
- `vex doctor ai` — 13-check AI readiness report (sandbox backend, schema,
  provider creds, eval dataset shape, deploy env vars, runtime path, etc.)

## Next

On the path to v1:

- `vex eval --policy` — treat `[tool.vex.policy]` (or a named policy block) as
  a CI gate so evals fail closed on policy violations, not just quality regressions
- `vex deploy --policy-gate` — block `--apply`/`--run` when policy preconditions
  (sandbox, secrets, model signature) are not met
- Trace tail in `vex dev` — inline spans from the agent / HTTP loop during
  hot-reload so developers see what the model actually did
- Inspect AI adapter for `vex eval` — in flight in
  [issue #23](https://github.com/peaktwilight/vex/issues/23); becomes the new
  default once it lands
- Logfire observability hook — in flight in
  [issue #24](https://github.com/peaktwilight/vex/issues/24); OTel GenAI
  compatible
- Contract CI between `vex` and `vex-ai-runtime` so schema and manifest changes
  stay wired across the two repos

## Later

Still in scope but not the current focus:

- `vex export` — render a vex project to a plain uv / Docker project so teams
  can hand it off without vex
- `vex shell` — ergonomic drop-in into the managed `.venv` with policy
  defaults applied
- `vex cache` — share warmed-up model / tool caches across runs
- Workspace support — multiple vex-managed projects in one monorepo

## v1 Direction

- polished AI project templates
- container-oriented and runtime-aware deployment helpers
- deep integration with `vex-ai-runtime` (native execution + packaged artifacts)
- local benchmark and evaluation workflows with CI-gradable output
- opt-in secure packaging and policy enforcement
- deployment adapters for Docker/OCI, Cloud Run, and Modal (shipped); Inspect
  AI and Logfire adapters wired in (next)

## Product Guardrails

- one project config: `pyproject.toml`
- one default environment: `.venv`
- one substrate for package/env management: `uv`
- one clear local-first AI workflow
- runtime and policy should be first-class, not bolted on later
- escape hatches are allowed, but secondary
