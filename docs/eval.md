# Eval

`vex eval` runs dataset-driven checks over the project, emits a normalized
`vex-eval/v1` JSON report, and can gate CI on a minimum pass rate. There are
three adapters today and one in flight.

## Adapters

- **harness** — built-in, always available. Executes the configured command
  under `uv run` for each case in `evals/datasets/cases.jsonl` (with
  `--per-case`) or once for the whole dataset (default).
- **promptfoo** — opt-in adapter that shells out to `uvx promptfoo` (or a
  system `promptfoo` on `PATH`) when a `promptfooconfig.yaml` file is present.
  Normalizes promptfoo's output into the same `vex-eval/v1` schema. promptfoo
  is owned by OpenAI as of 2026-03-09; the adapter is stable, but is no longer
  the intended default.
- **Inspect AI** — becomes the default once
  [issue #23](https://github.com/peaktwilight/vex/issues/23) lands. It replaces
  promptfoo as the recommended adapter for new projects; promptfoo will remain
  as a supported adapter for existing pipelines.

## Adapter precedence

Resolved in `handle_eval`:

1. **Explicit `--command`** — always uses the built-in harness.
2. **`--no-promptfoo`** — force the built-in harness even if
   `promptfooconfig.yaml` exists.
3. **`[tool.vex.eval].adapter`** — `"harness"`, `"promptfoo"`, or `"auto"`
   (default). Unknown values fall back to `"auto"`.
4. **`"auto"` resolution** — delegate to promptfoo when
   `promptfooconfig.yaml` (or `.yml`) exists at the project root, otherwise
   use the harness.

Once the Inspect AI adapter lands, the default for freshly scaffolded projects
becomes `adapter = "inspect"`; existing projects keep whatever is in
`pyproject.toml` and can migrate on their own schedule.

## `--json` schema

The normalized report is `vex-eval/v1`. Relevant top-level keys:

- `schema` — always `"vex-eval/v1"`
- `adapter` — `"harness"` or `"promptfoo"` (future: `"inspect"`)
- `mode` — `"per-case"` or `"promptfoo"` when applicable
- `command` / `dataset` — what was executed and against what
- `dataset_case_count`, `passed`, `failed`
- `pass_rate` — percentage of cases that passed (0.0–100.0)
- `duration_ms` — wall-clock time (harness, single-shot mode)
- `results` — per-case array with `input`, `exit_code`, `passed`,
  `expect_contains`, `expect_exact`, `expect_json_path`, `expect_json_equals`,
  plus the `contains_ok` / `exact_ok` / `json_path_ok` gate flags and truncated
  `stdout` / `stderr` snippets

Use `--json` to print the report to stdout (the human summary is suppressed).
The report is also written to `--out` (default `artifacts/evals/latest.json`).

## `--min-pass-rate` semantics

`--min-pass-rate <fraction>` accepts a value in `[0.0, 1.0]`. Compares against
`pass_rate / 100` and sets the exit code to non-zero when the threshold is
missed, even if every case exited cleanly. The default threshold comes from
`[tool.vex.eval].min_pass_rate` in `pyproject.toml`:

```toml
[tool.vex.eval]
adapter = "auto"
min_pass_rate = 0.9
```

The CLI flag overrides the config value. Absent both, no minimum is enforced.

## Authoring `evals/datasets/cases.jsonl`

One JSON object per line. Fields supported by `run_eval_per_case_harness`:

- `input` (string) — substituted into the command. When the command contains
  `{input}`, it replaces the literal token; otherwise the input is appended as
  a shell-quoted argument.
- `expect_contains` (string) — passes when the substring appears in stdout.
- `expect_exact` (string) — passes when `stdout.strip()` equals the value.
- `expect_json_path` (dot path string, e.g. `"result.status"`) — parses stdout
  as JSON and walks the path.
- `expect_json_equals` (any JSON value) — combined with `expect_json_path`,
  asserts that the value at the path equals this value.

A case passes when the command exits 0 *and* every specified expectation
holds. Omit a field to skip its check.

Minimal dataset:

```jsonl
{"input": "how long do refunds take?", "expect_contains": "5 business days"}
{"input": "ping", "expect_contains": "ping"}
{"input": "status", "expect_json_path": "result.status", "expect_json_equals": "ok"}
```

## CI snippet

Gate CI on the promptfoo adapter emitting 90 %+ pass rate and capture the
normalized report:

```bash
vex eval --adapter promptfoo --json --min-pass-rate 0.9 > results.json
```

`--adapter` is the forthcoming surface for adapter selection; today the same
effect is achieved via `[tool.vex.eval].adapter = "promptfoo"` plus the
existing `--json` and `--min-pass-rate` flags:

```bash
vex eval --json --min-pass-rate 0.9 > results.json
```

## `--policy` — run evals under the declared sandbox

`vex eval --policy` wraps every adapter (`harness`, `per-case`, `promptfoo`,
`inspect`) inside the sandbox declared in [`[tool.vex.policy]`](policy.md).
Uses the same argv shape as `vex run --sandbox`: `--cap-drop ALL`,
`--read-only`, `--network <none|bridge>`, memory + pids caps, project mounted
read-only at `/workspace`. Adds a `policy` block to the normalized report
(schema stays `vex-eval/v1`, additive only):

```json
{
  "policy": {
    "enforced": true,
    "network": "deny",
    "filesystem": "project",
    "sandbox_backend": "docker",
    "sandbox_image": "python:3.12-slim",
    "sandbox_memory_mb": 1024,
    "sandbox_pids_limit": 128,
    "unsafe_fallback_applied": false
  }
}
```

Hard-fail conditions:

- `[tool.vex.policy].sandbox = false` combined with `--policy` exits `2` with
  a message pointing at `vex policy set sandbox true --type bool`.
- No sandbox backend available (no `podman` or `docker` on `PATH`) and
  `unsafe_fallback = false` exits `2` with a pointer at `vex doctor ai`.
- `unsafe_fallback = true` + no backend runs the adapter locally, prints a
  `WARN sandbox backend unavailable; running eval without sandbox enforcement
  (unsafe_fallback=true)` banner, and stamps `enforced: false,
  unsafe_fallback_applied: true` in the report.

`promptfoo` and `inspect` adapters shell out via `uvx`; when `--policy` is
active, the entire `uvx promptfoo ...` / `uvx --from inspect-ai inspect ...`
invocation runs inside the container. The default `python:3.12-slim` image
does not bundle `uv`, so the adapter prepends a one-shot
`command -v uvx >/dev/null 2>&1 || pip install --quiet uv` shim before the
`uvx` call. A follow-up `vex/sandbox-eval:latest` image will pre-bake `uv`
and drop the shim (see issue #33 discussion).

See also: [`architecture.md`](architecture.md),
[`product-boundary.md`](product-boundary.md), [`deploy.md`](deploy.md),
[`policy.md`](policy.md).
