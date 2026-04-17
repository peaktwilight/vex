# support-bot

A PydanticAI customer-support agent with FAQ lookup and order tracking.

## What this shows

- `vex init agent` output customised with a support persona
- Two typed tools: `lookup_faq` (canned topics) and `track_order` (JSON response)
- A wider `evals/datasets/cases.jsonl` covering FAQ hits, tool calls, and refusals
- `deploy.targets.toml` with `default` (local dry-run) and `prod` (pushed image) profiles
- Zero-code provider fallback: set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or nothing
  (then `vex` talks to a local [`ollama`](https://ollama.com) model)

## How to run

```bash
cd examples/support-bot
uv sync --extra agent
cp .env.example .env           # edit if you want to pin a provider

vex dev "where is my order ORD-1234?"
vex eval                       # runs the 8 cases and prints PASS/FAIL
vex deploy check --for all     # preflight for docker / cloud-run / modal
vex deploy docker              # build the image (add --push to push)
```

## Files

```
support-bot/
  pyproject.toml                package deps and vex scripts
  deploy.targets.toml           default + prod profiles
  .env.example                  provider env hints
  prompts/system.md             support persona
  src/support_bot/
    __init__.py
    settings.py                 provider auto-resolution
    agent.py                    FAQ + order tools
    main.py                     async entrypoint
    benchmark.py                3-sample latency probe
    eval.py                     JSONL-driven PASS/FAIL harness
  evals/
    run_eval.py                 thin wrapper used by `vex eval`
    datasets/cases.jsonl        8 cases: FAQ hits, tool calls, refusals
```

## Notes

- The `track_order` tool returns a canned dict keyed off a tiny lookup table.
  Swap it for a real HTTP call when you wire this to production.
- `cases.jsonl` uses substring matching on the agent's final text. For richer
  checks, replace the harness in `eval.py` with a `deepeval` or `promptfoo`
  adapter (both already listed under `[project.optional-dependencies].eval`).
