"""The API loads the model baked into its image once at startup."""
import hashlib
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, Request
from pydantic import BaseModel, ConfigDict, Field


class YachtInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    buoyancy: float = Field(ge=-10, le=10, description="Dimensionless longitudinal buoyancy position")
    prismatic: float = Field(gt=0, lt=1)
    length_displacement: float = Field(gt=0, le=20)
    beam_draught: float = Field(gt=0, le=20)
    length_beam: float = Field(gt=0, le=20)
    froude: float = Field(gt=0, le=1)


@asynccontextmanager
async def lifespan(app):
    folder = Path(os.getenv("MODEL_DIR", "models"))
    app.state.metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    if hashlib.sha256((folder / "model.joblib").read_bytes()).hexdigest() != app.state.metadata["model_sha256"]:
        raise RuntimeError("Model checksum does not match metadata")
    app.state.model = joblib.load(folder / "model.joblib")
    yield


app = FastAPI(title="Yacht resistance API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health(request: Request):
    return {"status": "ok", "model_sha256": request.app.state.metadata["model_sha256"],
            "mlflow_run_id": request.app.state.metadata["mlflow_run_id"]}


@app.get("/model-info")
def model_info(request: Request):
    return request.app.state.metadata


@app.post("/predict")
def predict(values: YachtInput, request: Request):
    metadata = request.app.state.metadata
    row = values.model_dump()
    prediction = float(request.app.state.model.predict(pd.DataFrame([row], columns=metadata["features"]))[0])
    outside = [name for name, value in row.items() if not metadata["training_ranges"][name][0] <= value <= metadata["training_ranges"][name][1]]
    return {"resistance": prediction, "unit": "dimensionless (source dataset scale)",
            "mlflow_run_id": metadata["mlflow_run_id"], "model_sha256": metadata["model_sha256"],
            "warnings": ["Outside training range: " + ", ".join(outside)] if outside else []}
