# FAQ

Short answers to positioning, mechanics, and compatibility questions. See
[`product-boundary.md`](product-boundary.md) for the long form on what vex
owns vs delegates.

## Positioning

### Does vex replace uv?

No. `uv` is a hard dependency. Every install, sync, lock, build, and publish
verb shells out to `uv`; `vex` itself owns no resolver, lockfile, or build
backend. See [`architecture.md`](architecture.md#non-goals).

### Why not just a Makefile plus promptfoo?

A Makefile encodes commands, not policy. `vex` composes command aliases
(`[tool.vex.scripts]`) with sandbox semantics (`[tool.vex.policy]`), eval
adapter resolution (`[tool.vex.eval]`), deploy profiles
(`deploy.targets.toml`), and a shared model-artifact schema. The binding
across those surfaces is the product — see
[`policy.md`](policy.md) for the `[tool.vex.policy]` shape
`vex run --sandbox` actually enforces.

### Why PydanticAI as the default agent framework?

Typed tool boundaries, `pydantic-settings`-shaped config, and first-class
Logfire instrumentation line up with the rest of the vex surface. The
`agent` scaffold wires `logfire.instrument_pydantic_ai()` when
`LOGFIRE_TOKEN` is set; see
[`templates.md`](templates.md#vex-init-agent-path).

### Can I use LangGraph or Claude Agent SDK?

Not yet via `vex init`. The `--framework` flag that adds `langgraph` and
`claude-agent-sdk` scaffold variants is tracked in
[issue #45](https://github.com/peaktwilight/vex/issues/45). Until it ships,
either fork the PydanticAI scaffold or drop your framework of choice into a
plain `uv init` project and add a `[tool.vex]` block by hand.

### Why not the LangGraph CLI?

LangGraph CLI is LangSmith-coupled and opinionated about graph authoring.
`vex` is backend-neutral: no LangSmith lock-in, policy and sandbox are
first-class, and the deploy targets (Docker, Cloud Run, Modal) are vendor-CLI
wrappers — see [`deploy.md`](deploy.md).

## Mechanics

### How does `vex run --sandbox` differ from `docker run`?

`vex run --sandbox` is a pre-configured `docker run` (or `podman run`) with
`--cap-drop ALL`, `--read-only`, `--network <none|bridge>`,
`--security-opt no-new-privileges`, memory and pids caps, and the project
mounted read-only at `/workspace`. Every flag is driven by
`[tool.vex.policy]` — see
[`policy.md`](policy.md#what-vex-run---sandbox-actually-enforces) for the
full argv shape.

### What is `vex-ai-runtime` for?

A Rust + PyO3 crate that owns native model artifact loading and
`vex-model/v1` schema validation. `vex package-model` produces the
manifest; `vex schema validate-model` and the runtime both consume it. See
[`runtime.md`](runtime.md).

### Is there a local-only mode?

Yes. With no hosted provider key set, the agent scaffold's
`resolve_provider()` returns `"ollama"` and `vex dev` prints
`[vex dev] provider=ollama`. No network calls leave the box as long as
`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` are unset and the agent only touches
local tools. `vex doctor ai` confirms the state (`OK  no hosted provider
keys; ollama available on PATH (local fallback)`).

## Compatibility

### Which Python versions are supported?

3.11 or newer. `vex init` normalizes the scaffolded `requires-python` to
`>=3.11` and pins `.python-version` to `3.12` when `--python` is not
passed. Both `vex` itself and `vex-ai-runtime` declare
`requires-python = ">=3.11"`.

### Which platforms are supported?

macOS and Linux. The sandbox path assumes POSIX semantics (`sh -c`,
container-native `--cap-drop`, `--read-only`, `--pids-limit`), so Windows
is not tested and `vex run --sandbox` is unlikely to behave correctly
there. Use WSL2 on Windows.

### How is uv's version pinned?

CI pins `astral-sh/setup-uv@v5` to a specific uv release
(`version: "0.5.14"` at time of writing, in
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)). Local
installations follow whatever the user installed via
https://docs.astral.sh/uv/getting-started/installation/; `vex doctor`
reports the resolved `uv` path.

See also: [`architecture.md`](architecture.md),
[`product-boundary.md`](product-boundary.md), [`roadmap.md`](roadmap.md),
[`templates.md`](templates.md), [`runtime.md`](runtime.md),
[`troubleshooting.md`](troubleshooting.md).
