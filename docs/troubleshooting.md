# Troubleshooting

Failure modes grouped by surface. Not exhaustive — this page lists the
failure shapes most likely to hit a new user. See
[`cli-reference.md`](cli-reference.md) for flag semantics and
[`doctor.md`](doctor.md) for a per-check readiness guide.

## vex init

### "The requested interpreter resolved to Python X, which is incompatible..."

Fix: pass `--python 3.12` or patch `requires-python` in the scaffolded
`pyproject.toml`. Since #21, the scaffold normalizes `requires-python` to
`>=3.11` and pins `.python-version` to `3.12` automatically unless you
override with `--python`.

### "uv: command not found"

Fix: install `uv` via https://docs.astral.sh/uv/getting-started/installation/.
`vex` shells out to `uv` for every verb — there is no fallback.

### "vex init accepts only one path unless using a template..."

Fix: `vex init <path>` for a plain project, or `vex init agent <path>` /
`vex init inference-api <path>` for an AI template. A bare
`vex init agent foo bar` is rejected with exit `2`.

## vex dev

### "watchfiles not installed" and dev runs without hot reload

Fix: `uv sync --extra agent` — `watchfiles` ships as part of the PydanticAI
install tree. `vex dev` detects the missing import, prints a notice, and
falls back to running the dev command once.

### Banner says "provider=ollama" but ollama is not on PATH

Fix: install ollama from https://ollama.com, or export `OPENAI_API_KEY` /
`ANTHROPIC_API_KEY`. The banner is produced by `resolve_dev_provider`: any
hosted key flips the resolved provider; otherwise it defaults to `ollama`.

### "vex dev requires [tool.vex.scripts].dev in pyproject.toml"

Fix: add a `dev` alias under `[tool.vex.scripts]`, for example:

```toml
[tool.vex.scripts]
dev = "python -m myapp.main"
```

Exit code: `2`.

## vex eval

### "The executable 'inspect-ai' was not found."

Fix: the CLI entrypoint is `inspect`, not `inspect-ai`. `vex` already uses
`uvx --from inspect-ai inspect` internally; this error means your shell PATH
found stale `inspect-ai` machinery. Either remove the stale binary or rely
on `uvx` (install `uv`).

### "promptfooconfig.yaml present but I want the harness"

Fix: `--adapter harness` (or `[tool.vex.eval].adapter = "harness"`). The
deprecated `--no-promptfoo` flag still works but prints a deprecation
warning.

### Dataset parsing: "0 rows, N invalid JSON"

Fix: validate with
`python -c "import json; [json.loads(l) for l in open('evals/datasets/cases.jsonl')]"`.
Each line must be a standalone JSON object with at least an `input` field.
Empty lines are ignored.

### `--min-pass-rate` always fails

Fix: the value is a fraction in `[0.0, 1.0]`, not a percent. `0.9` means
90 %. Values outside that range exit with code `2`.

### "inspect adapter timed out after 300s"

Fix: raise `--timeout` (seconds). Default is `300.0`; exceeding it returns
exit code `124`.

## vex deploy

### "Preflight reported N issue(s); aborting."

Fix: run `vex deploy check --for <target>` to see which checks failed —
missing env vars, missing vendor CLI, or a missing project profile. Address
each WARN, then re-run. `--skip-preflight` is available but bypasses safety.

### "${VEX_IMAGE_REPO} not bound" (via preflight)

Fix: export the env var or add it to a `.env` file sourced before
`vex deploy`. `vex doctor ai` also catches this via the deploy env var
interpolation check.

### gcloud / modal / docker not on PATH

Fix: install the target's CLI. `vex doctor ai` surfaces this too.

- Cloud Run requires `gcloud`; deploy aborts with exit `127` when it is
  missing.
- Modal requires `modal` plus `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`.
- Docker requires `docker` or `podman` on PATH.

### Cloud Run URL not captured

Fix: the URL is parsed from `gcloud run deploy`'s stdout/stderr using the
`*.run.app` pattern. When the match fails you still see
`Deployed service <name> (no URL detected in gcloud output)` and exit `0`.
Re-run with `--quiet` already set; confirm the service in the Cloud Console.

## vex run --sandbox

### "No sandbox backend available"

Fix: install `docker` or `podman`. Alternatively, opt in to unsandboxed
execution with `vex policy set unsafe_fallback true --type bool` — this
is a warning-only fallback and is not recommended for production.

### "echo hi: not found" inside the sandbox

Fix: known bug pre-#4. Upgrade to `main`. Single-token quoted commands are
now passed verbatim to `sh -c` inside the container, so
`vex run --sandbox "echo hi"` works as expected.

### Image pull taking forever

Fix: `<backend> pull <image>` outside of `vex` to warm the cache — for
example `docker pull python:3.12-slim`. `vex doctor ai` reports when the
configured `sandbox_image` is not cached locally.

### "Sandbox execution is disabled by policy (sandbox=false)"

Fix: set `[tool.vex.policy].sandbox = true` in `pyproject.toml`, or
`vex policy set sandbox true --type bool`. The CLI refuses to shell out to
a sandbox backend when policy says sandboxing is off.

See also: [`doctor.md`](doctor.md), [`policy.md`](policy.md),
[`eval.md`](eval.md), [`deploy.md`](deploy.md),
[`cli-reference.md`](cli-reference.md).
