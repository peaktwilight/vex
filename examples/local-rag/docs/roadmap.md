# Roadmap

Near-term directions for vex:

- `vex dev` upgraded to a real dev loop with `watchfiles` hot reload, local
  ollama fallback, and inline trace tail.
- `vex eval` adapters for `promptfoo` and `deepeval`, with `--json` CI output
  and pass-rate gates.
- `vex deploy modal` and `vex deploy cloud-run` as full end-to-end
  deployments, not just scaffolding.
- `vex doctor ai` extended to verify ollama availability, model reachability,
  eval dataset shape, and deploy profile env var binding.
- A richer `examples/` tree with runnable agents, inference APIs, and local
  RAG (you are reading one).

## Non-goals

- shipping a new Python resolver, lockfile, or build backend.
- competing with `uv` on dependency installation speed.
- replacing hosted observability platforms.
