"""Dev-mode JSONL trace writer for `vex dev`.

Minimal, stdlib-only OTel-GenAI-shaped JSONL logger. Activated by the
`VEX_TRACE_DIR` env var so scaffolded agents stay zero-dep and only emit traces
during `vex dev`.

Schema (one JSON object per line):

    {
      "ts": "2026-04-17T12:00:00.000000+00:00",
      "session_id": "9d1f...",
      "kind": "llm_call" | "tool_call" | "error",
      "latency_ms": 123.4,
      "gen_ai.system": "openai",
      "gen_ai.request.model": "gpt-4o-mini",
      "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
      "gen_ai.usage.input_tokens": 42,
      "gen_ai.usage.output_tokens": 17
    }

Any failure — import errors, filesystem errors, logging framework quirks — is
swallowed. Tracing is strictly best-effort; it must never bring the agent down.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


__all__ = [
    "enable_dev_tracing",
    "record_llm_call",
    "record_tool_call",
    "record_error",
]


_SESSION_ID: str | None = None
_WRITER_LOCK = threading.Lock()
_ACTIVE_WRITER: "_JsonlWriter | None" = None
_PYDANTIC_AI_HANDLER: logging.Handler | None = None


OTEL_GEN_AI_KEYS: tuple[str, ...] = (
    "gen_ai.system",
    "gen_ai.request.model",
    "gen_ai.response.model",
    "gen_ai.usage.input_tokens",
    "gen_ai.usage.output_tokens",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session_id() -> str:
    global _SESSION_ID
    if _SESSION_ID is None:
        _SESSION_ID = uuid.uuid4().hex
    return _SESSION_ID


class _JsonlWriter:
    """Append-only JSONL file writer with a sibling `latest.jsonl` pointer."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Touch the file so `tail -f latest.jsonl` has something to read.
        path.touch(exist_ok=True)

    def write(self, record: dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=False, default=str)
        with self._lock:
            try:
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
                    fh.flush()
            except OSError:
                # Never take down the agent because tracing failed.
                pass


def _update_latest_pointer(dir_path: Path, target: Path) -> None:
    """Make `<dir>/latest.jsonl` point at `target`.

    Uses a symlink on POSIX. Falls back to writing a one-line pointer file if
    symlinks are unavailable (e.g. unprivileged Windows). Tail consumers that
    can't follow symlinks will still see the current session file path.
    """
    latest = dir_path / "latest.jsonl"
    try:
        if latest.exists() or latest.is_symlink():
            try:
                latest.unlink()
            except OSError:
                pass
        os.symlink(target.name, latest)
        return
    except (OSError, NotImplementedError, AttributeError):
        pass
    try:
        # Fallback: best-effort copy of current (empty) file so `tail -f` has a
        # path that exists. The tail thread in cli.py tails the resolved latest
        # symlink/file anyway.
        latest.write_text("", encoding="utf-8")
    except OSError:
        pass


class _PydanticAiLogHandler(logging.Handler):
    """Capture PydanticAI structured log records and emit trace rows.

    PydanticAI log records carry LLM/tool call metadata in their `extra` dict.
    We translate whatever fields we recognize onto the OTel GenAI envelope.
    Unknown events are ignored.
    """

    def __init__(self, writer: _JsonlWriter) -> None:
        super().__init__(level=logging.DEBUG)
        self._writer = writer

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            payload = _log_record_to_trace(record)
            if payload is not None:
                self._writer.write(payload)
        except Exception:
            # Must never raise from inside logging.
            pass


def _log_record_to_trace(record: logging.LogRecord) -> dict[str, Any] | None:
    """Best-effort mapping from a pydantic_ai LogRecord to a trace row."""
    event = getattr(record, "event", None) or record.name or ""
    event = str(event).lower()

    kind: str | None = None
    if record.levelno >= logging.ERROR:
        kind = "error"
    elif "tool" in event:
        kind = "tool_call"
    elif "llm" in event or "model" in event or "request" in event:
        kind = "llm_call"
    if kind is None:
        return None

    payload: dict[str, Any] = {
        "ts": _utc_now_iso(),
        "session_id": _session_id(),
        "kind": kind,
        "latency_ms": float(getattr(record, "latency_ms", 0.0) or 0.0),
    }

    for key in OTEL_GEN_AI_KEYS:
        attr = key.replace(".", "_")
        value = getattr(record, attr, None)
        if value is None:
            value = record.__dict__.get(key)
        if value is not None:
            payload[key] = value

    message = record.getMessage()
    if message and kind == "error":
        payload["error.message"] = message

    return payload


def _build_payload(
    kind: str,
    latency_ms: float,
    fields: dict[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ts": _utc_now_iso(),
        "session_id": _session_id(),
        "kind": kind,
        "latency_ms": float(latency_ms),
    }
    if fields:
        for key, value in fields.items():
            if value is None:
                continue
            payload[key] = value
    return payload


def record_llm_call(latency_ms: float, **fields: Any) -> None:
    """Record an LLM call row into the active trace writer.

    No-op if `enable_dev_tracing` was never called (or failed).
    """
    writer = _ACTIVE_WRITER
    if writer is None:
        return
    try:
        writer.write(_build_payload("llm_call", latency_ms, fields))
    except Exception:
        pass


def record_tool_call(latency_ms: float, **fields: Any) -> None:
    """Record a tool call row."""
    writer = _ACTIVE_WRITER
    if writer is None:
        return
    try:
        writer.write(_build_payload("tool_call", latency_ms, fields))
    except Exception:
        pass


def record_error(latency_ms: float, **fields: Any) -> None:
    """Record an error row."""
    writer = _ACTIVE_WRITER
    if writer is None:
        return
    try:
        writer.write(_build_payload("error", latency_ms, fields))
    except Exception:
        pass


def enable_dev_tracing(dir: str | os.PathLike[str]) -> Path | None:
    """Start JSONL trace writing at `<dir>/dev-<YYYYMMDD-HHMMSS>.jsonl`.

    Also updates `<dir>/latest.jsonl` to point at the new file. Returns the
    path of the new trace file, or None if setup failed.

    Tracing is intentionally best-effort:
      - import failures inside this function are swallowed
      - filesystem errors are swallowed
      - any exception raised during set-up results in a silent no-op
    """
    global _ACTIVE_WRITER, _PYDANTIC_AI_HANDLER

    try:
        dir_path = Path(dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        trace_path = dir_path / f"dev-{stamp}.jsonl"
        # Guarantee a unique filename if two sessions start in the same second.
        counter = 0
        while trace_path.exists():
            counter += 1
            trace_path = dir_path / f"dev-{stamp}-{counter}.jsonl"

        writer = _JsonlWriter(trace_path)
        with _WRITER_LOCK:
            _ACTIVE_WRITER = writer
        _update_latest_pointer(dir_path, trace_path)

        # Attach a logger handler to pydantic_ai so structured LLM / tool call
        # log records turn into trace rows. If logfire is present, it usually
        # grabs the same records via its own instrumentation — that's fine,
        # the handler here remains a no-cost fallback.
        try:
            logger = logging.getLogger("pydantic_ai")
            handler = _PydanticAiLogHandler(writer)
            # Detach any previous handler from a prior enable call.
            if _PYDANTIC_AI_HANDLER is not None:
                try:
                    logger.removeHandler(_PYDANTIC_AI_HANDLER)
                except Exception:
                    pass
            logger.addHandler(handler)
            # Don't lower the user's configured level; just make sure ours sees
            # records when they propagate here.
            if logger.level == logging.NOTSET:
                logger.setLevel(logging.INFO)
            _PYDANTIC_AI_HANDLER = handler
        except Exception:
            pass

        return trace_path
    except Exception:
        return None


def _reset_for_tests() -> None:
    """Test helper: forget the active writer + session id."""
    global _ACTIVE_WRITER, _SESSION_ID, _PYDANTIC_AI_HANDLER
    if _PYDANTIC_AI_HANDLER is not None:
        try:
            logging.getLogger("pydantic_ai").removeHandler(_PYDANTIC_AI_HANDLER)
        except Exception:
            pass
    _ACTIVE_WRITER = None
    _SESSION_ID = None
    _PYDANTIC_AI_HANDLER = None


# Keep an import-time side effect for visibility only when debugging.
if os.environ.get("VEX_TRACE_DEBUG") == "1":  # pragma: no cover - diagnostic
    print(f"[vex.trace] module loaded (pid={os.getpid()})", file=sys.stderr)
