# Deploy

`vex deploy` ships a vex-managed project to one of three targets — `docker`,
`cloud-run`, or `modal` — using `deploy.targets.toml` profiles and, where
needed, a scaffolded config file. Every target supports the same three modes:

- no flag — scaffold only (write the target's config file, print its path)
- `--apply` — scaffold then apply via the vendor CLI, captures URL output
- `--run` — scaffold then run locally (docker) or deploy (cloud-run / modal),
  surfaces the resulting URL

`--apply` and `--run` run `vex deploy check --for <target>` automatically as a
preflight. Pass `--skip-preflight` to override.

## Targets

### `docker`

- **Scaffold**: none — `docker build` is invoked directly against the project's
  existing `Dockerfile`.
- **`--apply`**: no-op; use `--run` for local execution, or add `--push` to
  push the built image.
- **`--run`**: `docker build -t <image>:<tag> .` followed by
  `docker run --rm -p <port>:<port> <image>:<tag>`. Port defaults to `8000`,
  override via `--port`.
- **Backends**: `docker` or `podman` (first one found on `PATH`).
- **Flags**: `--image`, `--tag`, `--push`, `--port`.

### `cloud-run`

- **Scaffold**: `deploy/cloud-run.yaml` (Knative `Service` with the resolved
  `<image>:<tag>` and a comment recording the target region).
- **`--apply` / `--run`**: `gcloud builds submit --tag <image>:<tag>` then
  `gcloud run deploy <service> --image <image>:<tag> --region <region>
  --format value(status.url) --quiet`. Extra flags are set from the profile
  when present: `--memory`, `--cpu`, `--min-instances`, `--max-instances`,
  `--service-account`, and `--allow-unauthenticated` /
  `--no-allow-unauthenticated`.
- **URL capture**: the service URL (`*.run.app`) is extracted from stdout /
  stderr and echoed as `Deployed: <url>`.
- **Requires**: `gcloud` on `PATH` plus an active project (either
  `--project` or `GOOGLE_CLOUD_PROJECT` or a `gcloud config` default).

### `modal`

- **Scaffold**: `deploy/modal_app.py` with a minimal `modal.App` and a
  `fastapi_endpoint`-backed `/healthz` handler so `modal deploy` has something
  to register.
- **`--run`**: `modal deploy deploy/modal_app.py` (captured output, prints
  `Deployed: <url>` once a `*.modal.run` URL appears in the output).
- **Requires**: `modal` on `PATH`; `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`
  environment variables (preflight warns when they are missing).

## `deploy.targets.toml` schema

Live under the project root. Profiles are TOML tables; a profile can inherit
from another using `inherit = "<name>"`. String values are passed through env
interpolation (`${VAR}` or `${VAR:-fallback}`).

Example — [`examples/support-bot/deploy.targets.toml`](../examples/support-bot/deploy.targets.toml):

```toml
[profiles.default]
image = "ghcr.io/example/support-bot"
tag = "latest"
service = "support-bot-agent"
region = "us-central1"
app_name = "support-bot-agent"
push = false

[profiles.prod]
inherit = "default"
tag = "prod"
image = "${VEX_IMAGE_REPO:-ghcr.io/example/support-bot}"
push = true
```

Common keys:

- `image`, `tag` — used by all three targets
- `push` — boolean, only honored by docker
- `service`, `region` — Cloud Run service name and region
- `project` — optional GCP project override
- `app_name` — Modal app name
- `memory`, `cpu`, `min_instances`, `max_instances`, `service_account`,
  `allow_unauthenticated` — extra Cloud Run `gcloud run deploy` flags

## Preflight semantics

`vex deploy check [--for all|docker|cloud-run|modal]` inspects the local
environment and reports `OK` / `WARN` per check:

- `uv` on `PATH`
- profile `image:tag` resolution
- docker-compatible CLI (for `docker`)
- `gcloud` CLI and configured project (for `cloud-run`)
- `modal` CLI and `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` (for `modal`)
- runtime root detection (`engine/vex-ai-runtime/` or `VEX_AI_RUNTIME_PATH`)
- presence of `deploy.targets.toml`

Exit code is the number of issues. `--apply` and `--run` call the same
preflight and abort when issues are found unless `--skip-preflight` is set.

## Override precedence

Order of resolution for every knob (highest wins):

1. **CLI flag** — e.g. `--image`, `--tag`, `--project`, `--port`
2. **Profile** — the selected `[profiles.<name>]` table, with inheritance
   resolved and env interpolation applied
3. **Environment** — only via `${VAR}` interpolation inside profile values,
   plus `GOOGLE_CLOUD_PROJECT` / `MODAL_TOKEN_*` for preflight

Select a non-default profile with `--profile <name>`.

See also: [`architecture.md`](architecture.md),
[`product-boundary.md`](product-boundary.md), [`policy.md`](policy.md),
[`eval.md`](eval.md).
