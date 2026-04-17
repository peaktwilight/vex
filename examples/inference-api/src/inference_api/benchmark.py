from __future__ import annotations

import time

from .predictor import predict


def main() -> None:
    runs = 10
    latencies: list[float] = []
    for i in range(runs):
        start = time.perf_counter()
        predict(f"benchmark sample {i}")
        latencies.append((time.perf_counter() - start) * 1000)
    avg = sum(latencies) / len(latencies)
    print(
        f"predict benchmark runs={runs} "
        f"avg={avg:.2f}ms min={min(latencies):.2f}ms max={max(latencies):.2f}ms"
    )


if __name__ == "__main__":
    main()
