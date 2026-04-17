from __future__ import annotations

import asyncio
import time

from .agent import build_agent


async def _measure(runs: int) -> list[float]:
    agent = build_agent()
    latencies: list[float] = []
    for _ in range(runs):
        start = time.perf_counter()
        await agent.run("ping")
        latencies.append((time.perf_counter() - start) * 1000)
    return latencies


def main() -> None:
    latencies = asyncio.run(_measure(3))
    if not latencies:
        print("no samples")
        return
    avg = sum(latencies) / len(latencies)
    print(
        f"benchmark samples={len(latencies)} "
        f"avg={avg:.1f}ms min={min(latencies):.1f}ms max={max(latencies):.1f}ms"
    )


if __name__ == "__main__":
    main()
