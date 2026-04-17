from __future__ import annotations

import os
from pathlib import Path

try:
    from pydantic_ai import Agent, RunContext
except ImportError as exc:
    raise SystemExit("Install agent deps: uv sync --extra agent") from exc

from .settings import Settings

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system.md"

FAQS: dict[str, str] = {
    "refund": "Refunds are processed within 5 business days.",
    "refunds": "Refunds are processed within 5 business days.",
    "hours": "Support hours are 09:00-17:00 UTC, Mon-Fri.",
    "shipping": "Standard shipping takes 3-5 business days.",
    "returns": "You can return any unopened item within 30 days.",
    "warranty": "All office chairs carry a 2-year warranty.",
}

ORDERS: dict[str, dict[str, str]] = {
    "ORD-1234": {
        "order_id": "ORD-1234",
        "status": "shipped",
        "carrier": "UPS",
        "tracking": "1Z999AA10123456784",
        "eta": "2025-11-03",
    },
    "ORD-5678": {
        "order_id": "ORD-5678",
        "status": "processing",
        "carrier": "",
        "tracking": "",
        "eta": "2025-11-06",
    },
    "ORD-9999": {
        "order_id": "ORD-9999",
        "status": "delivered",
        "carrier": "FedEx",
        "tracking": "7999 1234 5678",
        "eta": "2025-10-21",
    },
}


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
    async def lookup_faq(_ctx: RunContext, topic: str) -> str:
        """Look up a canned FAQ entry by topic keyword."""
        return FAQS.get(topic.lower().strip(), "No FAQ entry for that topic.")

    @agent.tool
    async def track_order(_ctx: RunContext, order_id: str) -> dict[str, str]:
        """Return status, carrier, tracking, and ETA for an order id."""
        key = order_id.strip().upper()
        if key in ORDERS:
            return ORDERS[key]
        return {
            "order_id": key,
            "status": "unknown",
            "carrier": "",
            "tracking": "",
            "eta": "",
        }

    return agent
