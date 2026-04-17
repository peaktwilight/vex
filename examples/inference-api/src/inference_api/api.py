from __future__ import annotations

try:
    from fastapi import FastAPI, HTTPException
    import uvicorn
except ImportError as exc:
    raise SystemExit("Install API deps: uv sync --extra api") from exc

from .predictor import MODEL_NAME, MODEL_PATH, model_loaded, predict
from .schemas import (
    HealthResponse,
    ModelInfo,
    PredictRequest,
    PredictResponse,
)

app = FastAPI(title="vex inference api", version="0.1.0")


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(status="ok", model_loaded=model_loaded())


@app.get("/models", response_model=list[ModelInfo])
def list_models() -> list[ModelInfo]:
    if not model_loaded():
        return []
    return [
        ModelInfo(
            name=MODEL_NAME,
            engine="stub",
            path=str(MODEL_PATH.relative_to(MODEL_PATH.parents[1])),
        )
    ]


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(request: PredictRequest) -> PredictResponse:
    if not model_loaded():
        raise HTTPException(status_code=503, detail="model artifact missing")
    result = predict(request.text)
    return PredictResponse(**result)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
