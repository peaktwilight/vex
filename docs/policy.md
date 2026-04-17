# Policy and Sandbox

`vex` treats execution policy as a first-class workflow concern. Policy lives
in `pyproject.toml` under `[tool.vex.policy]`, is enforced by
`vex run --sandbox`, and shows up in `vex doctor ai` and deploy preflight.

## `[tool.vex.policy]` schema

Scaffolded defaults from `vex init`:

```toml
[tool.vex.policy]
sandbox = true
network = "deny"
filesystem = "project"
sandbox_backend = "auto"
sandbox_image = "python:3.12-slim"
sandbox_memory_mb = 1024
sandbox_pids_limit = 128
unsafe_fallback = false
```

Keys:

- `sandbox` (`bool`) — whether sandboxing is expected. `vex doctor ai` checks
  backend availability only when this is `true`.
- `network` (`"deny"` | `"allow"`) — translates into the container `--network`
  flag. `deny` maps to `--network none`, anything else maps to `--network bridge`.
- `filesystem` (`"project"`) — intent marker for the project-scoped bind mount
  (currently `{root}:/workspace:ro`).
- `sandbox_backend` (`"auto"` | `"docker"` | `"podman"`) — `auto` prefers
  `podman` if present, falls back to `docker`, otherwise reports `none`.
- `sandbox_image` (`str`) — container image for `vex run --sandbox`. Must be
  pre-pulled; `vex doctor ai` warns when the image is not cached locally and
  prints the exact `<backend> pull <image>` command to fix it.
- `sandbox_memory_mb` (`int`) — hard memory cap, passed as `--memory <N>m`.
- `sandbox_pids_limit` (`int`) — max PIDs inside the sandbox, passed as
  `--pids-limit <N>`.
- `unsafe_fallback` (`bool`) — when no sandbox backend is available and this is
  `true`, `vex run --sandbox` prints a warning and runs the command unsandboxed
  instead of exiting with code 2.

## What `vex run --sandbox` actually enforces

Ground truth is `run_sandboxed` in `src/vex/cli.py`. Every invocation runs:

```
<backend> run --rm
  --network <none|bridge>       # from policy.network
  --memory <N>m                 # from policy.sandbox_memory_mb
  --pids-limit <N>              # from policy.sandbox_pids_limit
  --read-only
  --cap-drop ALL
  --security-opt no-new-privileges
  -v <project_root>:/workspace:ro
  -w /workspace
  <sandbox_image>
  sh -c <command>
```

Read-only rootfs, all Linux capabilities dropped, no-new-privileges, project
directory mounted read-only. Network is denied by default and must be
explicitly opted into via `network = "allow"`.

## Docker vs Podman detection

`sandbox_backend = "auto"` (the default) resolves via `shutil.which`:

1. Prefer `podman` if it's on `PATH`.
2. Fall back to `docker`.
3. Otherwise return `none`.

Pin explicitly with `sandbox_backend = "docker"` or `sandbox_backend = "podman"`
to override the preference, for example in CI environments where both are
installed.

## Escape hatches

- `unsafe_fallback = true` — run unsandboxed when no backend is available
  (a warning is printed, but the command still runs).
- `vex policy set <key> <value>` — write an override to `.vex/policy.json` that
  layers on top of the `[tool.vex.policy]` block without editing
  `pyproject.toml`. Useful for per-developer local tweaks and CI toggles. Pair
  with `vex policy unset <key>` to remove the override.
- Drop `--sandbox` from `vex run` to use the plain managed environment.

## Example policies

Agent with a hosted LLM call (needs network):

```toml
[tool.vex.policy]
sandbox = true
network = "allow"
filesystem = "project"
sandbox_backend = "docker"
sandbox_image = "python:3.12-slim"
sandbox_memory_mb = 2048
sandbox_pids_limit = 256
```

Eval harness over a local dataset (fully offline):

```toml
[tool.vex.policy]
sandbox = true
network = "deny"
filesystem = "project"
sandbox_memory_mb = 1024
sandbox_pids_limit = 128
```

Inference API packaged against `vex-ai-runtime` (tight caps, no network):

```toml
[tool.vex.policy]
sandbox = true
network = "deny"
filesystem = "project"
sandbox_backend = "podman"
sandbox_image = "python:3.12-slim"
sandbox_memory_mb = 512
sandbox_pids_limit = 64
unsafe_fallback = false
```

## Relationship to `vex-ai-runtime`

`vex run --sandbox` is container-level isolation. For the *native* execution
angle — signed model artifacts, schema validation, and runtime-enforced
policies on the inference path — see
[`engine/vex-ai-runtime/`](../engine/vex-ai-runtime/). The two layers compose:
`vex` keeps development-time policy honest via containers, and
`vex-ai-runtime` keeps the production inference path honest via the
`vex-model/v1` manifest contract.

See also: [`architecture.md`](architecture.md),
[`product-boundary.md`](product-boundary.md), [`deploy.md`](deploy.md).
