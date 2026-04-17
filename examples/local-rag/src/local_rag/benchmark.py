from __future__ import annotations

import time

from . import retriever

QUERIES = (
    "architecture principles",
    "product boundary",
    "package model runtime",
    "vex commands",
    "ollama fallback",
)


def main() -> None:
    latencies: list[float] = []
    for query in QUERIES:
        start = time.perf_counter()
        retriever.search(query, k=3)
        latencies.append((time.perf_counter() - start) * 1000)
    avg = sum(latencies) / len(latencies)
    print(
        f"retriever benchmark queries={len(QUERIES)} "
        f"avg={avg:.2f}ms min={min(latencies):.2f}ms max={max(latencies):.2f}ms"
    )


if __name__ == "__main__":
    main()
