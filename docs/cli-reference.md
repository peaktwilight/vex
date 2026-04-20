# CLI reference

Every `vex` verb is a thin wrapper around `uv` or a target-specific CLI.
This page is a per-verb flag and exit-code reference; see [`eval.md`](eval.md),
[`policy.md`](policy.md), and [`deploy.md`](deploy.md) for the deeper behavior
of the AI workflow verbs.

Global flags:

- `--version` — print the installed `vex` version and exit 0.

When `vex` is invoked with no subcommand it prints help and exits 0.

## AI workflow verbs

### `vex init`

Scaffold a new vex-managed project by delegating to `uv init` and then
appending `[tool.vex]` configuration, optional AI template files, and a
`deploy.targets.toml` profile.

Positional arguments (both optional):

- `template_or_path` — either one of the AI templates (`agent`,
  `inference-api`) or a destination path.
- `path` — the destination path when the first argument was a template.

Flags:

- `--name <str>` — project name forwarded to `uv init --name`; also the seed
  for the derived package name written into `[tool.vex]`.
- `--python <str>` — Python version forwarded to `uv init --python`. When
  omitted, the scaffold pins to `3.12` and normalizes `requires-python` to
  `>=3.11` so projects stay portable across developer machines.
- `--framework {pydantic-ai,langgraph,claude-agent-sdk}` — only valid with
  `vex init agent`. Selects the agent framework baked into the scaffolded
  files and `[project.optional-dependencies].agent`. Default: `pydantic-ai`.
  The chosen framework is recorded as `[tool.vex.ai].framework` and surfaced
  by `vex doctor ai`.
- `--app` — passthrough to `uv init --app --no-package` (non-packaged app).
- `--lib` — passthrough to `uv init --lib --package --build-backend hatch`.
  Mutually exclusive with `--app`.

Exit codes:

- `0` — scaffold succeeded.
- `2` — invalid template / path combination (e.g. `vex init agent foo bar`).
- non-zero — whatever `uv init` returned; `127` if `uv` is not on PATH.

Config written after init:

- `[tool.vex]` block inside `pyproject.toml` (package name, template marker).
- `[tool.vex.scripts]` with the template's `dev` / `benchmark` / `eval`
  entrypoints.
- `[tool.vex.policy]` block with sandbox defaults (see [`policy.md`](policy.md)).
- `deploy.targets.toml` with `profiles.default` and `profiles.prod`.

Example:

```bash
vex init agent support-bot --name support-bot
vex init agent graph-bot --framework langgraph
vex init agent claude-bot --framework claude-agent-sdk
```

### `vex dev`

Run the project's `[tool.vex.scripts].dev` command under `uv run` with
file-watching reload and an LLM provider banner.

Flags:

- `--no-reload` — disable watchfiles reload; run the dev command once under
  `uv run` and forward its exit code.
- `--watch <path>` — extra path to watch; repeatable. Added on top of
  `src/` (when present) and `[tool.vex.dev].watch`.
- `--provider-check` / `--no-provider-check` — toggle the
  `[vex dev] provider=...` banner. Default: on. The banner warns when
  `provider=ollama` but `ollama` is not on PATH.
- trailing args — forwarded verbatim to the dev command.

Exit codes:

- `0` — dev command exited cleanly.
- `2` — no `[tool.vex.scripts].dev` configured.
- `127` — `uv` not on PATH.
- `130` — SIGINT during watch loop.

Config sources:

- `[tool.vex.scripts].dev` (required).
- `[tool.vex.dev].watch` — list of extra paths to watch.
- Environment: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (used by the provider
  banner heuristic; see `resolve_dev_provider`).

Example:

```bash
vex dev --watch config/
```

### `vex eval`

Run dataset-driven evaluations and emit a normalized `vex-eval/v1` report.
See [`eval.md`](eval.md) for adapter precedence and the report schema.

Flags:

- `--command <str>` — shell command to run; forces the built-in harness.
- `--dataset <path>` — dataset path (default: `evals/datasets/cases.jsonl`).
- `--out <path>` — report output path (default: `artifacts/evals/latest.json`).
- `--per-case` — with the harness, run the command once per case and gate on
  per-case expectations.
- `--json` — print the normalized report JSON to stdout and suppress the
  human summary.
- `--min-pass-rate <float>` — fraction in `[0.0, 1.0]`; fail when
  `pass_rate / 100` falls below this. Falls back to
  `[tool.vex.eval].min_pass_rate`.
- `--adapter {auto,inspect,promptfoo,harness}` — override adapter selection.
  `auto` prefers Inspect AI, then promptfoo, then harness.
- `--no-promptfoo` — deprecated alias for `--adapter harness`; emits a
  warning.
- `--timeout <float>` — adapter subprocess timeout in seconds (default
  `300.0`).
- trailing args — appended to the resolved command (harness only).

Exit codes:

- `0` — all cases passed (and the min-pass-rate gate was met).
- `1` — at least one case failed, or `--min-pass-rate` gate missed.
- `2` — invalid arguments (out-of-range `--min-pass-rate`, missing command or
  adapter config).
- `124` — adapter subprocess exceeded `--timeout`.
- `127` — required adapter binary (`uvx` / `inspect` / `promptfoo`) not
  available.

Config sources:

- `[tool.vex.scripts].eval` — default command when `--command` is omitted.
- `[tool.vex.eval].adapter` — default adapter.
- `[tool.vex.eval].min_pass_rate` — default gate threshold.
- Adapter configs at project root: `inspect.yaml` / `inspect.toml` /
  `evals/*.inspect.py` for Inspect AI; `promptfooconfig.yaml` for promptfoo.

Example:

```bash
vex eval --adapter promptfoo --json --min-pass-rate 0.9 > results.json
```

### `vex deploy`

Build or ship the project to docker, Cloud Run, or Modal. Preflight runs
automatically before `--apply` / `--run`. See [`deploy.md`](deploy.md) for
target-specific behavior.

Positional argument:

- `target` — one of `docker`, `cloud-run`, `modal`, or `check`.

Flags:

- `--image <str>` — OCI image name (default `vex-app`). Profile override key
  `image`.
- `--tag <str>` — image tag (default `latest`). Profile override key `tag`.
- `--push` — docker only; push after build. Profile override key `push`.
- `--service <str>` — Cloud Run service name (default `vex-ai-service`).
- `--region <str>` — Cloud Run region (default `us-central1`).
- `--project <str>` — GCP project (falls back to `GOOGLE_CLOUD_PROJECT` or
  `gcloud config` default).
- `--app-name <str>` — Modal app name (default `vex-ai-app`). Profile
  override keys `app_name` / `app-name`.
- `--apply` — after scaffolding, apply via the vendor CLI (runs preflight
  first unless `--skip-preflight`).
- `--run` — docker: build + run locally; modal: `modal deploy` the
  scaffold. Runs preflight first unless `--skip-preflight`. (Cloud Run
  deploys are triggered by `--apply`, not `--run`.)
- `--port <int>` — port mapping for `docker --run` (default `8000`).
- `--profile <str>` — `deploy.targets.toml` profile to apply (default
  `default`).
- `--skip-preflight` — bypass the automatic preflight for `--apply`/`--run`.
- `--for {all,docker,cloud-run,modal}` — with `target=check`, restrict the
  preflight scope (default `all`).

Exit codes:

- `0` — scaffold / apply / run succeeded; for `target=check` also returned
  when no preflight issues are reported.
- `1` — preflight reported one or more issues (either for `check` or before
  `--apply`/`--run`).
- `2` — unsupported target.
- `127` — required vendor CLI (`docker`/`podman`/`gcloud`/`modal`) missing.
- non-zero — whatever the vendor CLI returned.

Config sources:

- `deploy.targets.toml` — profiles, env interpolation, inheritance.
- Environment: `GOOGLE_CLOUD_PROJECT`, `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`,
  and anything referenced as `${VAR}` in profile values.

Examples:

```bash
vex deploy cloud-run --apply --profile prod
vex deploy docker --run --port 8080
```

### `vex deploy check`

Run preflight against the local environment without building or deploying.

Flags:

- `--for {all,docker,cloud-run,modal}` — scope (default `all`).
- All `vex deploy` profile flags are accepted and applied to the resolved
  profile (for instance `--image` / `--tag` for the reported `image:tag`).

Exit codes:

- `0` — no issues reported.
- `1` — one or more WARN lines.

See [`deploy.md`](deploy.md) for the full check list.

Example:

```bash
vex deploy check --for cloud-run
```

### `vex policy`

Inspect and override the effective `[tool.vex.policy]` configuration. See
[`policy.md`](policy.md) for the schema and sandbox enforcement.

Subcommands:

- `list` — print every resolved policy key on stdout (default when no
  subcommand).
- `get <key>` — print a single value; exit `1` when the key is missing.
- `set <key> <value> [--type {auto,str,bool,int,float,json}]` — write an
  override to `.vex/policy.json`. `auto` tries bool, then int, then float,
  then falls back to string.
- `unset <key>` — remove an override from `.vex/policy.json`.

Exit codes:

- `0` — success.
- `1` — `get` called with a missing key.
- `2` — `set` value could not be parsed, or unknown subcommand.

Config sources:

- `[tool.vex.policy]` in `pyproject.toml` (base).
- `.vex/policy.json` (per-developer override, layered on top).

Example:

```bash
vex policy set unsafe_fallback true --type bool
```

### `vex run`

Run a script alias or arbitrary command under `uv run`, optionally inside a
sandbox container.

Flags:

- `--sandbox` — run the resolved command inside the sandbox backend
  (`docker` or `podman`) configured by `[tool.vex.policy]`. See
  [`policy.md`](policy.md) for the exact container flags.
- trailing args — script alias or shell command.

Exit codes:

- `0` / propagated — whatever the command returned.
- `2` — no command supplied, or sandbox disabled by policy
  (`sandbox=false`).
- `127` — `uv` not on PATH.

Config sources:

- `[tool.vex.scripts].<name>` — script alias lookup.
- `[tool.vex.policy]` — sandbox backend, image, network, memory, pids
  limits.
- `.vex/policy.json` — per-developer overrides.

Examples:

```bash
vex run smoke                   # resolves [tool.vex.scripts].smoke
vex run --sandbox "pytest -q"
```

### `vex package-model`

Create a packaged model artifact manifest (`vex-model.json`) suitable for
`vex-ai-runtime`.

Positional:

- `model` — path to the source model file.

Flags:

- `--out-dir <path>` — output directory (default `build/model-artifact`).
- `--name <str>` — artifact name (default: the source filename stem).
- `--sha256 <str>` — pre-computed digest; when omitted, the CLI computes the
  hash itself.
- `--skip-compat-check` — skip the runtime compatibility validation step.

Exit codes:

- `0` — manifest written (and compat check passed, if run).
- `2` — invalid input (missing source file, incompatible artifact).

Config sources:

- `VEX_AI_RUNTIME_PATH` — override for the shared schema location.
- `engine/vex-ai-runtime/schemas/vex-model-schema.json` — shared schema used
  to stamp the manifest's `schema` / `schema_version` / `runtime` / `engine`
  fields.

Example:

```bash
vex package-model models/classifier.onnx --name classifier
```

### `vex schema validate-model`

Validate a packaged model artifact against the runtime's load path.

Positional:

- `artifact_dir` — directory to validate (default `build/model-artifact`).

Flags:

- `--strict-runtime` — treat a missing runtime as an error; default is to
  skip the check with a notice.

Exit codes:

- `0` — compatibility check passed (or was skipped without `--strict-runtime`).
- `2` — validation failed, or subcommand was omitted.

Config sources: same as `vex package-model`.

Example:

```bash
vex schema validate-model build/model-artifact --strict-runtime
```

### `vex doctor`

Run readiness checks against the project. Optional positional `scope`
(`ai`) runs the extended AI scope. See [`doctor.md`](doctor.md) for the full
list of checks.

Exit codes:

- `0` — no issues reported.
- `1` — one or more WARN / ERR lines.

Example:

```bash
vex doctor ai
```

### `vex benchmark`

Time a shell command across warmup and measured runs, emitting a
`vex-benchmark/v1` report.

Flags:

- `--command <str>` — command to benchmark. When omitted, falls back to
  `[tool.vex.scripts].benchmark`, then `python -m timeit -n 1000 -r 5 '1+1'`.
- `--runs <int>` — measured iterations (default `5`).
- `--warmup <int>` — warmup iterations (default `1`).
- `--out <path>` — report path (default `artifacts/benchmarks/latest.json`).
- trailing args — appended to the resolved command.

Exit codes:

- `0` — every measured run exited `0`.
- non-zero — propagated from the first failing run.
- `127` — `uv` not on PATH.

Config sources:

- `[tool.vex.scripts].benchmark` — default command.

Example:

```bash
vex benchmark --runs 20 --warmup 3 --command "python -m app.bench"
```

### `vex export`

Bundle a vex-managed project into a portable `.vex` artifact (gzipped
tarball). See [`artifacts.md`](artifacts.md) for the manifest schema and
the determinism guarantee.

Flags:

- `--out <path>` — artifact destination (default
  `dist/<name>-<version>.vex`).
- `--include-models` / `--no-include-models` — walk `dist/*/vex-model.json`
  and inline the referenced model files (default: include).
- `--include-venv` / `--no-include-venv` — override the default `.venv/`
  exclude (default: exclude).
- `--dry-run` — print the manifest to stdout without writing a tarball.
- `--exclude <glob>` — repeatable glob against the relative path.

Exit codes:

- `0` — artifact written (or dry-run printed).
- `2` — invalid arguments.

Example:

```bash
vex export --out dist/support-bot-0.3.2.vex
```

### `vex import`

Unpack a `.vex` artifact into a fresh project directory, verifying every
file's SHA-256 against the manifest.

Positional:

- `artifact` — path to the `.vex` file.

Flags:

- `--dest <path>` — destination directory (default: current dir + the
  artifact stem).
- `--force` — downgrade SHA mismatches to a `WARN` and allow overwriting a
  non-empty destination.

Exit codes:

- `0` — artifact unpacked cleanly.
- `2` — SHA mismatch, missing manifest, refused overwrite, or invalid
  archive.

Example:

```bash
vex import dist/support-bot-0.3.2.vex --dest /tmp/support-bot
```

## uv passthroughs

These verbs delegate directly to `uv`. They exist so the workflow stays
`vex`-native even when the real work is pure `uv`.

### `vex add` / `vex remove` / `vex sync` / `vex lock`

- `vex add <packages...> [--dev | --group <name>]` — `uv add`.
- `vex remove <packages...> [--dev | --group <name>]` — `uv remove`.
- `vex sync [--frozen] [--group <name> ...]` — `uv sync`.
- `vex lock [--upgrade] [packages...]` — `uv lock`; extra packages map to
  repeated `--upgrade-package <name>` flags.

Exit codes: propagated from `uv`; `127` when `uv` is not on PATH.

Example:

```bash
vex add pydantic-ai --group agent
```

### `vex test` / `vex lint` / `vex format` / `vex typecheck`

Run the project's `[tool.vex.scripts].<name>` command under `uv run sh -c`
when configured; otherwise fall back to the DEFAULT_SCRIPT_COMMANDS:

- `test` → `uv run --with pytest pytest`
- `lint` → `uv run --with ruff ruff check .`
- `format` → `uv run --with ruff ruff format .`
- `typecheck` → `uv run --with mypy mypy .`

Trailing args are appended to the resolved command.

Exit codes: propagated from the underlying tool; `127` when `uv` is not on
PATH.

Example:

```bash
vex test -k agent
```

### `vex python`

Manage Python interpreters via `uv python`.

Subcommands:

- `install <version>` — `uv python install <version>`.
- `pin <version>` — `uv python pin <version>`.
- `list` — `uv python list`.
- `path` — `uv python find`.
- `uninstall <version>` — `uv python uninstall <version>`.

Exit codes: propagated from `uv`.

Example:

```bash
vex python install 3.12
```

### `vex build` / `vex publish`

- `vex build [--wheel] [--sdist]` — `uv build`.
- `vex publish [--repository <url>]` — `uv publish`; `--repository` is
  forwarded as `uv publish --index <url>`.

Exit codes: propagated from `uv`.

Example:

```bash
vex build --wheel --sdist
```

### `vex tool`

Manage isolated Python CLI tools via `uv tool`.

Subcommands:

- `run <tool_name> [args...]` — `uv tool run <tool_name> ...`.
- `install <tool_name>` — `uv tool install <tool_name>`.
- `list` — `uv tool list`.
- `upgrade` — `uv tool upgrade` (all tools).
- `uninstall <tool_name>` — `uv tool uninstall <tool_name>`.

Exit codes: propagated from `uv`.

Example:

```bash
vex tool run ruff check .
```

## CI coverage

The repo runs tests in three layers: unit (every push/PR), integration
(every push/PR, scaffolds a real project under `uv`), and contract (labelled
PRs / nightly, invokes real `docker` / `gcloud` / `modal` / `uvx` against
vex-produced argv). Full end-to-end release gating lives in a separate
sprint. See `CONTRIBUTING.md` for how to opt into each layer locally.
