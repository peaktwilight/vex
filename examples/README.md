# examples

Runnable end-to-end projects that exercise the four-command `vex` loop
(`init`, `dev`, `eval`, `deploy`) on real code shapes.

Each example is a standalone `vex`-managed project with its own
`pyproject.toml`, `deploy.targets.toml`, `evals/datasets/cases.jsonl`, and
`README.md`. They do not share code or dependencies with each other or with
the main `vex` package.

## Projects

- [`support-bot/`](./support-bot) — a PydanticAI customer-support agent with
  FAQ lookup and an order-tracking tool. The widest eval dataset (FAQ hits,
  tool calls, refusals).
- [`inference-api/`](./inference-api) — a FastAPI service with a `/predict`
  endpoint that returns a fake inference response plus latency metadata. Wires
  `vex package-model` against a 32-byte stub artifact so the packaging loop is
  end-to-end.
- [`local-rag/`](./local-rag) — an ollama-backed RAG agent with a naive
  substring retriever and a 5-file markdown corpus. Settings default to the
  local provider, no API key required.

## Pick the one closest to your use case

| If you are building...                 | Start from         | Key bits                                                   |
| -------------------------------------- | ------------------ | ---------------------------------------------------------- |
| A tool-using chat agent                | `support-bot`      | `agent.py` with `lookup_faq` + `track_order` tools         |
| A model-serving HTTP API               | `inference-api`    | `api.py` with `/predict`, `vex package-model` wiring       |
| A local, private, docs-grounded assist | `local-rag`        | `retriever.py` + `search_docs` tool, ollama by default     |

## Running any example

```bash
cd examples/<name>
uv sync --extra agent   # or --extra api for inference-api
vex dev
vex eval
vex deploy check --for all
```

Each example's `README.md` lists the exact invocations and what to expect.
