from __future__ import annotations

import os
from pathlib import Path

try:
    from pydantic_ai import Agent, RunContext
except ImportError as exc:
    raise SystemExit("Install agent deps: uv sync --extra agent") from exc

from . import retriever
from .settings import Settings

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system.md"


def build_agent(settings: Settings | None = None) -> Agent:
    settings = settings or Settings()
    if settings.is_local_fallback():
        os.environ.setdefault("OPENAI_API_KEY", "ollama")
        os.environ.setdefault("OPENAI_BASE_URL", settings.ollama_base_url)

    agent = Agent(
        settings.model_spec(),
        system_prompt=SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip(),
    )

    @agent.tool
    async def search_docs(_ctx: RunContext, query: str, k: int = 3) -> str:
        """Search the local docs corpus and return the top-k matching chunks.

        The retriever is a naive substring + token-overlap scorer backed by
        the files under `docs/`. Pass short keyword queries, not full
        sentences.
        """
        hits = retriever.search(query, k=max(1, min(k, 5)))
        return retriever.format_hits(hits)

    return agent
