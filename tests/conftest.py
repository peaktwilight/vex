"""Shared pytest fixtures and guardrails for the vex test suite.

This file is intentionally minimal. It exists so that:

1. Pytest picks up ``tests/`` as a test root and adds it to ``sys.path``.
2. When ``pydantic-ai`` is installed (e.g. inside a scaffolded agent project's
   venv), we globally disable real model requests. No test, unit or
   integration, should ever be able to accidentally hit a live LLM API.

``pydantic-ai`` is NOT a dependency of the vex CLI itself, only of
scaffolded agent projects, so the import is guarded.
"""

from __future__ import annotations

try:  # pragma: no cover - guardrail, exercised only when pydantic-ai is present
    import pydantic_ai.models

    pydantic_ai.models.ALLOW_MODEL_REQUESTS = False
except ImportError:
    # pydantic-ai isn't installed in minimal test runs (e.g. the vex CLI
    # unit suite). That's fine - there are no agent objects to protect.
    pass
