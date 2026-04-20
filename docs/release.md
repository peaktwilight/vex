# Release

How `vex` and `vex-ai-runtime` are versioned, gated, and changelogged. This
is a policy doc, not a runbook — the mechanics live in
[`.github/workflows/release.yml`](../.github/workflows/release.yml).

## Versioning

SemVer, with a pre-1.0 relaxation:

- While the project is on `0.x`, breaking changes are allowed on minor
  version bumps. Every breaking change ships with release notes and, where
  relevant, a migration entry in the upgrade guide.
- After `1.0`, breaking changes only ship on major version bumps.
- Patch versions are always non-breaking (bugfix / docs / dependency floor
  adjustments).

The `vex` CLI surface (flags, config keys, exit codes) and the
`vex-model/v1` manifest contract are the two surfaces SemVer applies to.
Internal function signatures in `src/vex/cli.py` are not stable.

## CI release gate

A release tag (`v*`) is only cut when every gate below is green on the
commit being tagged:

- **Unit** — `vex-tests` and `runtime-python-tests` jobs in
  [`ci.yml`](../.github/workflows/ci.yml). Run on every push / PR.
- **Integration** — `integration` job in the same workflow
  (`VEX_RUN_INTEGRATION=1 uv run pytest tests/integration -m integration`).
- **Runtime Rust** — `runtime-rust-tests` job
  (`cargo test` inside `engine/vex-ai-runtime`).
- **Contract CI** — tracked in
  [issue #44](https://github.com/peaktwilight/vex/issues/44). Verifies that
  `vex package-model` output still loads cleanly through the runtime's
  `load_artifact_manifest`, and that `VEX_MODEL_SCHEMA_ID` /
  `VEX_MODEL_SCHEMA_VERSION` in `src/vex/cli.py` match
  `engine/vex-ai-runtime/schemas/vex-model-schema.json`. This gate becomes
  exhaustive once #44 merges.
- **Release-E2E** — a manual end-to-end run against a representative scaffold
  (`vex init agent`, `vex eval`, `vex deploy check --for all`) on the tagged
  commit. Triggered by hand on the tag before publishing the GitHub Release.

[`release.yml`](../.github/workflows/release.yml) handles the build step on
tag push: `python -m build` for `vex`, `maturin build --release` and
`python -m build engine/vex-ai-runtime` for the runtime, then
`softprops/action-gh-release` attaches the artifacts.

## Changelog convention

`CHANGELOG.md` at the repo root, in
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format:
`Unreleased` at the top, then a section per released version with date,
grouped under `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and
`Security`. Each entry links to the merged PR or closing issue.

`CHANGELOG.md` is not yet present in the repo — adding it is a follow-up
(see PR body).

## Upgrade guide convention

Breaking changes get a per-minor section in `docs/upgrading.md` with:

- What changed on the CLI surface, config keys, or scaffold layout.
- The deprecation warning shown on the previous minor (if any).
- The migration command or edit needed to move a project forward.

`docs/upgrading.md` is not yet present — adding it is a follow-up (see PR
body).

## Deprecation policy

When a flag, config key, or manifest field is removed:

1. The previous minor release ships a deprecation warning on every use of
   the surface, plus a changelog entry under `Deprecated`.
2. The next minor release removes the surface and logs the removal under
   `Removed` with a pointer at the upgrade guide section.

Removing a surface in the same release cycle it was deprecated in is not
allowed. Existing deprecation warnings in `src/vex/cli.py` (for instance
`--no-promptfoo`, see
[`cli-reference.md`](cli-reference.md#vex-eval)) follow this pattern.

See also: [`architecture.md`](architecture.md),
[`cli-reference.md`](cli-reference.md), [`roadmap.md`](roadmap.md),
[`runtime.md`](runtime.md).
