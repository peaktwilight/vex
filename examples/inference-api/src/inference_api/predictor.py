"""Fake inference backend.

The real thing would load the artifact packaged by `vex package-model`, e.g.
via `onnxruntime.InferenceSession(model_path)`. Here we just do a deterministic
hash-based bucketing so the API has something plausible to return without
pulling any model weights.
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

LABELS = ("positive", "neutral", "negative")
MODEL_NAME = "stub-classifier"
MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "stub.bin"


def _bucket(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return digest[0] % len(LABELS)


def model_loaded() -> bool:
    return MODEL_PATH.exists()


def predict(text: str) -> dict[str, object]:
    start = time.perf_counter()
    # Fake "inference": deterministic label + score in [0.5, 1.0).
    idx = _bucket(text)
    label = LABELS[idx]
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    score = 0.5 + (digest[1] / 255) * 0.5
    inference_ms = (time.perf_counter() - start) * 1000
    # Simulate a tiny post-processing pass so total > inference.
    time.sleep(0.001)
    total_ms = (time.perf_counter() - start) * 1000
    return {
        "label": label,
        "score": round(score, 4),
        "latency": {
            "inference_ms": round(inference_ms, 3),
            "total_ms": round(total_ms, 3),
            "model": MODEL_NAME,
        },
    }
