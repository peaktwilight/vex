from __future__ import annotations

import asyncio
import sys

from .agent import build_agent
from .settings import Settings


async def _run(prompt: str) -> str:
    result = await build_agent().run(prompt)
    return str(result.output)


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        prompt = "Hi, what can you help me with?"
    settings = Settings()
    provider = settings.resolve_provider()
    print(f"[vex agent] provider={provider} model={settings.model_spec()}")
    print(asyncio.run(_run(prompt)))


if __name__ == "__main__":
    main()
