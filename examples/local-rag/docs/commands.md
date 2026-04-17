# Commands

vex exposes a small verb set. The verbs most relevant to an AI app are:

- `vex init agent <path>` scaffolds a real PydanticAI agent with
  `agent.py`, `settings.py`, `main.py`, `eval.py`, a `prompts/system.md`,
  five seed eval cases, and a `deploy.targets.toml` with `default` and `prod`
  profiles.
- `vex init inference-api <path>` scaffolds a FastAPI + uvicorn service with
  typed schemas.
- `vex dev` runs the project dev command.
- `vex benchmark` runs the benchmark command with configurable warmup.
- `vex eval` runs dataset-driven PASS/FAIL checks with CI-ready exit codes.
- `vex deploy docker|cloud-run|modal` builds or scaffolds a deployment.
- `vex deploy check --for all` runs a deploy preflight.
- `vex package-model <artifact>` writes a versioned model manifest under
  `build/model-artifact/vex-model.json`.
- `vex doctor ai` runs a 13-check readiness report.

Every generic `uv` verb (`add`, `remove`, `sync`, `lock`, `build`, `publish`,
`python`, `tool`, `run`, `test`, `lint`, `format`, `typecheck`) is exposed as
a thin passthrough.
