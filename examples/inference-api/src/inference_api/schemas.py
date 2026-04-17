from __future__ import annotations

try:
    from pydantic import BaseModel, Field
except ImportError as exc:
    raise SystemExit("Install API deps: uv sync --extra api") from exc


class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)


class LatencyMeta(BaseModel):
    inference_ms: float
    total_ms: float
    model: str


class PredictResponse(BaseModel):
    label: str
    score: float
    latency: LatencyMeta


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class ModelInfo(BaseModel):
    name: str
    engine: str
    path: str
