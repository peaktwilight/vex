# Portable `.vex` artifacts

`vex export` and `vex import` turn a vex-managed project into a single
self-describing file. The README's headline — "portable execution
contract" — is literal here: the policy, the scaffold source, the resolved
deps (`uv.lock` hash), and any model manifests are all bundled together so
the exact same bytes can be imported on another machine, reviewed, and then
run, evaluated, or deployed under the same `[tool.vex.policy]`.

## File layout

A `.vex` file is a gzipped POSIX tarball. The first member is always
`manifest.json`, followed by every tracked project file in sorted path
order.

```
artifact.vex (gzip)
├── manifest.json
├── .env.example
├── .gitignore
├── pyproject.toml
├── src/<pkg>/__init__.py
├── src/<pkg>/main.py
├── uv.lock
└── dist/<model>/vex-model.json   # if --include-models
```

## Manifest schema — `vex-artifact/v1`

```json
{
  "schema": "vex-artifact/v1",
  "name": "support-bot",
  "version": "0.3.2",
  "created_at": "2026-04-17T00:00:00Z",
  "python_requires": ">=3.11",
  "entry_module": "support_bot.main",
  "policy": {
    "sandbox": true,
    "network": "deny",
    "filesystem": "project",
    "sandbox_backend": "auto",
    "sandbox_image": "python:3.12-slim",
    "sandbox_memory_mb": 1024,
    "sandbox_pids_limit": 128,
    "unsafe_fallback": false
  },
  "adapters": {
    "eval": "inspect",
    "runtime": "vex-ai-runtime",
    "framework": "pydantic-ai",
    "template": "agent"
  },
  "files": [
    { "path": "pyproject.toml", "sha256": "..." },
    { "path": "src/support_bot/main.py", "sha256": "..." }
  ],
  "models": [
    {
      "path": "dist/classifier/models/classifier.onnx",
      "sha256": "...",
      "engine": "onnxruntime",
      "name": "classifier"
    }
  ],
  "locks": { "uv.lock": "sha256:..." }
}
```

Field meanings:

- `schema` — exact string `vex-artifact/v1`. Anything else is rejected by
  `vex import`.
- `name` / `version` / `python_requires` — copied verbatim from `[project]`
  in `pyproject.toml`.
- `entry_module` — best-effort `<snake(name)>.main` so `vex deploy` and
  `vex run` can resolve a default entrypoint without user input.
- `policy` — snapshot of the effective `load_vex_policy(root)` value
  (merged from `[tool.vex.policy]` + `.vex/policy.json`).
- `adapters` — copied from `[tool.vex.ai]` (`template`, `runtime`,
  `framework`) and `[tool.vex.eval]` (`adapter`). Keys are omitted when
  unset.
- `files` — sorted, path-relative-to-root with a SHA-256 over the file
  contents.
- `models` — one entry per `dist/<name>/vex-model.json` referenced model
  file. Omitted with `--no-include-models`.
- `locks` — currently `uv.lock` with a `sha256:<hex>` string, empty when
  no lockfile is present.

## `vex export`

Flags:

- `--out <path>` — artifact destination. Default:
  `dist/<name>-<version>.vex` under the project root.
- `--include-models` / `--no-include-models` — walk `dist/*/vex-model.json`
  and inline the referenced model files. Default: include.
- `--include-venv` / `--no-include-venv` — override the `.venv/` default
  exclude. Default: exclude.
- `--dry-run` — print the manifest to stdout, do not write the tarball.
  Exit 0.
- `--exclude <glob>` — repeatable glob (matched against the relative path)
  for project-specific skips.

Default excludes (applied on top of `.gitignore`):

```
.venv/  __pycache__/  .pytest_cache/  .mypy_cache/
.ruff_cache/  .git/  dist/  artifacts/
node_modules/  *.pyc  .DS_Store  .env
```

`.env.example` is explicitly allowed so the scaffold's documented env keys
stay with the artifact.

## Determinism guarantee

Two exports of the same tree (no file contents changed) produce **byte-
identical** `.vex` output. The writer:

- Walks the tree with sorted directory entries.
- Uses `USTAR_FORMAT` and sets `tarinfo.mtime = 0`, `uid = gid = 0`,
  `uname = gname = ""`, file mode `0644`, directory mode `0755`.
- Streams through `gzip.GzipFile(fileobj=..., mtime=0)` so the gzip header
  carries no timestamp.
- Seeds `manifest.created_at` from the newest `mtime` in the included set
  rather than wall-clock `now()`.

This makes `.vex` files reviewable and diff-able: a reviewer can re-export
a committed branch locally and compare SHA-256 digests against the shipped
artifact.

## `vex import`

```
vex import <artifact.vex> [--dest <path>] [--force]
```

1. Opens the tarball and reads `manifest.json` first.
2. Refuses to write when the destination directory is non-empty (override
   with `--force`).
3. Extracts every file listed under `manifest.files`, recomputing the
   SHA-256 on the fly.
4. Any file whose SHA-256 does not match the manifest fails the import
   with exit code 2. `--force` downgrades this to `WARN` and continues.
5. On success, prints a summary:

```
Unpacked support-bot v0.3.2 to <dest>. policy.sandbox=true network=deny entry=support_bot.main. Next: cd <dest> && vex doctor ai
```

Paths that try to escape the destination (`../`, absolute paths) are
rejected unconditionally.

## How model files are collected

`vex export` does not re-discover model files from scratch. It looks for
`dist/<name>/vex-model.json` manifests (produced by `vex package-model`)
and copies the `model_path` entries into the artifact. This keeps the
runtime's model-compatibility contract — `vex-model/v1`, enforced by
`vex-ai-runtime` — intact end-to-end.

To include a model, run `vex package-model <model>` first, then
`vex export`.

## Follow-ups (out of scope for this release)

- `vex deploy <target> --from artifact.vex` — deploy straight from a `.vex`
  without unpacking into a working tree.
- `vex run --from artifact.vex --sandbox` — execute an artifact directly
  under the declared policy.
- Signing with a cosign key and a server-side verifier.
- Remote artifact registry / pull from URL.

See also: [`cli-reference.md`](cli-reference.md),
[`policy.md`](policy.md), [`deploy.md`](deploy.md).
