# Dev-mode tracing

`vex dev` ships a minimal, stdlib-only trace logger so you can see LLM and tool
calls flow past in real time without paying for a hosted observability product.
The goal is first-five-minutes feedback — not a replacement for Logfire /
Langfuse / Phoenix / Datadog.

## What gets written

When `vex dev` starts (and `--no-trace` is not passed), it:

1. Creates `artifacts/traces/` under the project root.
2. Exports `VEX_TRACE_DIR=<root>/artifacts/traces` to the child process env.
3. Scaffolded agents read that env var and call
   `vex.trace.enable_dev_tracing(dir)` in `main.py`.
4. `enable_dev_tracing` opens `dev-<YYYYMMDD-HHMMSS>.jsonl` for append and
   updates `latest.jsonl` to point at it (symlink on POSIX; plain pointer
   file on platforms where symlinks are restricted).
5. A background handler attached to the `pydantic_ai` logger translates each
   structured log record into one JSONL line.

If stderr is a TTY, `vex dev` also spawns a short tail thread that prints each
new line back to stderr with a dim `[trace]` prefix so the reload loop and the
trace share a single terminal.

## Schema

One JSON object per line. Fields:

| field                             | required | notes                                               |
| --------------------------------- | -------- | --------------------------------------------------- |
| `ts`                              | yes      | UTC ISO 8601 timestamp                              |
| `session_id`                      | yes      | UUID generated once per process                     |
| `kind`                            | yes      | `"llm_call"` \| `"tool_call"` \| `"error"`          |
| `latency_ms`                      | yes      | float                                               |
| `gen_ai.system`                   | no       | `"openai"` \| `"anthropic"` \| `"ollama"` \| ...    |
| `gen_ai.request.model`            | no       | model id the request asked for                      |
| `gen_ai.response.model`           | no       | model id the provider actually served               |
| `gen_ai.usage.input_tokens`       | no       | integer                                             |
| `gen_ai.usage.output_tokens`      | no       | integer                                             |

The `gen_ai.*` keys follow the
[OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/),
so any Langfuse / Phoenix / Datadog ingestor that speaks OTel-GenAI JSON can
eat these logs with minimal glue.

## Viewer tips

The trace file is plain JSONL. Normal Unix tools work:

```bash
# Follow the current session.
tail -f artifacts/traces/latest.jsonl

# Pretty-print every row.
tail -f artifacts/traces/latest.jsonl | jq '.'

# Only LLM calls with their latency + model.
jq -r 'select(.kind=="llm_call") | "\(.latency_ms)ms \(."gen_ai.request.model")"' \
    artifacts/traces/dev-*.jsonl

# Sum token usage across a session.
jq -s 'map(."gen_ai.usage.input_tokens" // 0) | add' artifacts/traces/latest.jsonl
```

## Upgrading to a real backend

The JSONL is deliberately minimal. When you're ready for a hosted backend,
add the appropriate env var and the scaffolded `main.py` picks it up without
further edits:

- **Logfire** — set `LOGFIRE_TOKEN=pylf_v1_...`. The scaffolded
  `main.py` already calls `logfire.configure()` + `logfire.instrument_pydantic_ai()`
  when the token is present.
- **Langfuse / Phoenix / Datadog** — point
  `OTEL_EXPORTER_OTLP_ENDPOINT=https://...` and
  `OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer ..."` at your collector.
  The OTel SDK auto-config does the rest.

The local JSONL stays on; it's additive, not exclusive.

## Turning it off

Pass `--no-trace` to `vex dev`:

```bash
vex dev --no-trace
```

That skips the `VEX_TRACE_DIR` export and the tail thread entirely.
