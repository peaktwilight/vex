# vex doctor — readiness checks

`vex doctor` reports one `OK`, `WARN`, or `ERR` line per check and exits `0`
when no issues were reported, `1` otherwise. Two scopes exist:

- `vex doctor` — base scope, always runs.
- `vex doctor ai` — additive scope for AI projects (policy, deploy profile,
  runtime, sandbox, providers, observability, eval datasets, deploy env).

Ground truth: `doctor_checks` in `src/vex/cli.py`.

## vex doctor (base scope)

### uv availability

- `OK  uv found at <path>` — `uv` resolved via `shutil.which`.
- `ERR uv not found on PATH`

Fix: install `uv` per https://docs.astral.sh/uv/getting-started/installation/.

### pyproject.toml present

- `OK  found pyproject.toml`
- `ERR missing pyproject.toml` — subsequent checks are skipped.

Fix: run `vex init` (or `uv init`) in the project root.

### pyproject.toml parses

- `OK  pyproject.toml parsed successfully`
- `ERR could not parse pyproject.toml` — subsequent checks are skipped.

Fix: repair the TOML syntax; `python -c "import tomllib; tomllib.loads(open('pyproject.toml').read())"`
prints the exact parse error.

### `[tool.vex]` section

- `OK  found [tool.vex] configuration`
- `WARN missing [tool.vex] configuration`

Fix: add a `[tool.vex]` block, or re-run `vex init` to generate one.

### uv.lock present

- `OK  found uv.lock`
- `WARN missing uv.lock; run 'vex sync' or 'vex lock'`

Fix: `vex sync` or `vex lock`.

### Environment directory

- `OK  environment directory exists at <path>`
- `WARN environment directory missing at <path>`

`<path>` is `[tool.vex.env].path` if set, else `.venv`.

Fix: `vex sync`.

### `[tool.vex.scripts]` aliases

- `OK  found vex scripts: <names>`
- `WARN no [tool.vex.scripts] aliases configured`

Fix: add a `[tool.vex.scripts]` table to `pyproject.toml`, for example:

```toml
[tool.vex.scripts]
dev = "python -m myapp.main"
eval = "python -m myapp.eval"
```

## vex doctor ai (AI scope — additive)

All base-scope checks run first. The AI scope adds the following.

### AI workflow scripts

For each of `dev`, `benchmark`, and `eval`:

- `OK  found AI workflow script '<name>'`
- `WARN missing AI workflow script '<name>'`

Fix: add the missing alias under `[tool.vex.scripts]` in `pyproject.toml`.

### `[tool.vex.policy]` section

- `OK  found [tool.vex.policy] with keys: <keys>` — either an inline policy
  block or an override in `.vex/policy.json` was detected.
- `WARN missing [tool.vex.policy] configuration`

Fix: add a `[tool.vex.policy]` block (see [`policy.md`](policy.md) for the
schema), or run `vex policy set <key> <value>` to seed
`.vex/policy.json`.

### `deploy.targets.toml` with default profile

- `OK  found deploy.targets.toml with default profile`
- `WARN missing deploy.targets.toml default profile`

Fix: create `deploy.targets.toml` with a `[profiles.default]` table (see
[`deploy.md`](deploy.md)), or re-run `vex init` with an AI template so the
scaffold writes one.

### Runtime path

- `OK  runtime path resolved to <path>`
- `WARN runtime path not resolved (set VEX_AI_RUNTIME_PATH if needed)`

The CLI searches, in order, `engine/vex-ai-runtime/`, `../vex-ai-runtime/`,
`./vex-ai-runtime/`, `../../vex-ai-runtime/`, and
`packages/vex-ai-runtime/`.

Fix: export `VEX_AI_RUNTIME_PATH=<abs path>` to point at your runtime
checkout, or place it in one of the searched locations.

### Shared model schema

- `OK  found shared model schema in runtime`
- `WARN runtime schema file missing`

Runs only when the runtime path was resolved. Checks for
`<runtime>/schemas/vex-model-schema.json`.

Fix: update your `vex-ai-runtime` checkout so the schema file is present.

### Sandbox backend

Only runs when `policy.sandbox` is `true`.

- `OK  sandbox backend detected: <docker|podman>` — from
  `sandbox_backend(policy)`.
- `WARN no sandbox backend detected (install docker or podman)`

Fix: install `docker` or `podman` on PATH, or set
`[tool.vex.policy].sandbox = false` if you don't need sandboxed runs.

### Sandbox image cache

Only runs when a sandbox backend was detected. Relies on
`sandbox_image_cached`, which shells out to `<backend> image inspect <image>`.

- `OK  sandbox image cached locally: <image>`
- `WARN sandbox image not cached locally: <image> (run: <backend> pull <image>)`

Fix: run the printed `<backend> pull <image>` command once to warm the cache.

### Hosted provider credentials

Checks each of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, and
`GROQ_API_KEY`.

- `OK  hosted provider credential detected: <name> (<ENV>)`
- `WARN OPENAI_API_KEY set but does not start with 'sk-' (looks malformed)` —
  accepts the `ollama` prefix as well.
- `WARN ANTHROPIC_API_KEY set but does not start with 'sk-ant-' (looks malformed)`

Fix: export a real credential (`export OPENAI_API_KEY=sk-...`), or unset the
malformed value and rely on the ollama fallback.

### Ollama fallback

- `OK  no hosted provider keys; ollama available on PATH (local fallback)` —
  no hosted keys set but `ollama` binary found.
- `OK  ollama available on PATH (local fallback)` — hosted keys present and
  `ollama` also available.
- `WARN no hosted provider keys set and 'ollama' not on PATH (install ollama or set OPENAI_API_KEY / ANTHROPIC_API_KEY)`

Fix: install ollama from https://ollama.com or set one of the hosted keys.

### `.env.example` declared keys

- `OK  .env.example declares <N> provider key(s); none set — will use ollama fallback`
- `WARN .env.example declares <N> provider key(s) but none are set in the environment` —
  only emitted when ollama is also unavailable.

Fix: export the declared keys (or a subset) in your shell or `.env`, or
install ollama.

### Observability

One of:

- `OK  observability: logfire` — `LOGFIRE_TOKEN` is set.
- `OK  observability: otel endpoint=<host>` — `OTEL_EXPORTER_OTLP_ENDPOINT`
  is set; the host (with port if present) is echoed back.
- `WARN no observability configured (set LOGFIRE_TOKEN or OTEL_EXPORTER_OTLP_ENDPOINT)`

Fix: export `LOGFIRE_TOKEN=...` or `OTEL_EXPORTER_OTLP_ENDPOINT=https://collector:4318`.

### Eval dataset shape

Runs only when `evals/datasets/` exists. For each `.jsonl` file:

- `OK  eval dataset <path>: <N> cases valid`
- `WARN evals/datasets/ present but no .jsonl datasets found`
- `WARN <path> has no cases`
- `WARN <path>: <N> rows, <B> invalid JSON, <M> missing 'input' field`
- `WARN could not read <path>: <OS error>`

Fix: make each dataset line a standalone JSON object with at least an
`input` field. Validate quickly with
`python -c "import json; [json.loads(l) for l in open('evals/datasets/cases.jsonl')]"`.

### Deploy env var interpolation

Runs only when `deploy.targets.toml` exists. Extracts every `${VAR}` token
from the file and checks each against the process environment.

- `OK  deploy.targets.toml env vars bound (<N> referenced)`
- `WARN deploy.targets.toml references unbound env vars: <names>`

Fix: export the missing variables, or add them to a `.env` file sourced
before `vex deploy`.

### Schema drift

- `WARN schema drift detected between vex and vex-ai-runtime for keys: <keys>` —
  emitted when the local `VEX_MODEL_SCHEMA_ID`, schema version, runtime, or
  engine constants differ from the runtime's shared
  `schemas/vex-model-schema.json`.

Fix: align your `vex` and `vex-ai-runtime` versions; if you are developing
locally, update whichever side is stale.

See also: [`cli-reference.md`](cli-reference.md),
[`troubleshooting.md`](troubleshooting.md), [`policy.md`](policy.md),
[`deploy.md`](deploy.md), [`eval.md`](eval.md).
