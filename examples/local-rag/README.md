# local-rag

A minimal ollama-backed RAG agent. No embedding model, no vector database:
the retriever is naive substring + token-overlap scoring so the whole thing
stays readable in a single sitting.

## What this shows

- `Settings.provider` defaults to `"ollama"` instead of `"auto"` so this example
  runs end-to-end on a laptop with nothing pinned behind an API key
- A PydanticAI tool that calls a tiny retriever module (`retriever.py`) which
  scores a markdown corpus and returns the top-k chunks
- A tutorial-grade corpus under `docs/` (five small markdown files) that the
  agent can cite
- A minimal eval that checks the model output contains a fact present in the
  retrieved context

## How to run

Install ollama and pull a tiny model first:

```bash
ollama pull llama3.2
```

Then:

```bash
cd examples/local-rag
uv sync --extra agent

vex dev "What is the vex product boundary?"
vex dev "Which runtime does vex use for native inference?"
vex eval
vex deploy check --for all
vex deploy docker
```

If you want to point at a different local model, set `VEX_OLLAMA_MODEL=...`
in `.env` (see `.env.example`). To switch to a hosted provider, set
`VEX_PROVIDER=openai` and `OPENAI_API_KEY` and re-run `vex dev`.

## Files

```
local-rag/
  pyproject.toml                  package deps and vex scripts
  deploy.targets.toml             default + prod profiles
  .env.example
  prompts/system.md               grounding persona
  docs/                           the 5-file corpus the agent cites
    architecture.md
    boundary.md
    commands.md
    roadmap.md
    runtime.md
  src/local_rag/
    __init__.py
    settings.py                   provider defaults to ollama
    retriever.py                  naive substring + token overlap
    agent.py                      PydanticAI agent with `search_docs` tool
    main.py                       async entrypoint
    benchmark.py                  retriever-only latency probe
    eval.py                       JSONL harness with grounded-fact assertions
  evals/
    run_eval.py
    datasets/cases.jsonl          6 cases grounded in the 5-doc corpus
```

## How the retriever works

`retriever.search(query, k)` walks every markdown file under `docs/`, splits
each file into paragraph-sized chunks, and scores chunks by:

1. raw substring hits of each query token in the chunk text
2. a small bonus for query tokens that appear in the document filename

The top-k chunks are returned with `doc`, `score`, and `text`. This is
deliberately crude. When you want to graduate to a real RAG pipeline, replace
`retriever.py` with an embedding + vector store (e.g. `chromadb` + `sentence-
transformers`) without touching `agent.py`.
