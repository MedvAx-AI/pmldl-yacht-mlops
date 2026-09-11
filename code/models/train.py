"""Train one small model; package its preprocessing and log it to MLflow."""
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ["buoyancy", "prismatic", "length_displacement", "beam_draught", "length_beam", "froude"]


def train(root=ROOT):
    training = pd.read_csv(root / "data/processed/train.csv")
    testing = pd.read_csv(root / "data/processed/test.csv")
    x_train, y_train = training[FEATURES], training["resistance"]
    x_test, y_test = testing[FEATURES], testing["resistance"]
    model = Pipeline([
        ("features", ColumnTransformer([("speed_powers", PolynomialFeatures(degree=3, include_bias=False), ["froude"])], remainder="passthrough")),
        ("regressor", ExtraTreesRegressor(n_estimators=80, max_depth=12, random_state=42, n_jobs=1)),
    ])
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///" + (root / "mlflow.db").as_posix()))
    mlflow.set_experiment("yacht-resistance")
    with mlflow.start_run() as run:
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        metrics = {"mae": mean_absolute_error(y_test, predictions), "rmse": root_mean_squared_error(y_test, predictions),
                   "r2": r2_score(y_test, predictions), "baseline_rmse": root_mean_squared_error(y_test, [y_train.mean()] * len(y_test))}
        if not all(math.isfinite(v) for v in metrics.values()) or metrics["rmse"] >= metrics["baseline_rmse"]:
            raise ValueError("Model failed the finite-metrics / mean-baseline quality gate")
        mlflow.log_params({"model": "ExtraTreesRegressor", "n_estimators": 80, "max_depth": 12, "random_state": 42,
                           "features": "hull geometry + Froude number powers 1,2,3", "split": "held-out hulls", "train_rows": len(training), "test_rows": len(testing)})
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, name="model", input_example=x_train.head(2),
                                signature=infer_signature(x_train, model.predict(x_train)),
                                pip_requirements=(root / "requirements-model.txt").read_text().splitlines())
        (root / "models").mkdir(exist_ok=True)
        (root / "reports").mkdir(exist_ok=True)
        temporary = root / "models/model.tmp.joblib"
        joblib.dump(model, temporary, compress=3)
        temporary.replace(root / "models/model.joblib")
        digest = hashlib.sha256((root / "models/model.joblib").read_bytes()).hexdigest()
        metadata = {"model_sha256": digest, "mlflow_run_id": run.info.run_id, "trained_at": datetime.now(timezone.utc).isoformat(),
                    "features": FEATURES, "metrics": metrics, "training_ranges": {f: [float(x_train[f].min()), float(x_train[f].max())] for f in FEATURES}}
        (root / "models/metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (root / "reports/metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        pd.DataFrame({"actual": y_test, "predicted": predictions}).to_csv(root / "reports/predictions.csv", index=False)
        mlflow.log_artifact(str(root / "reports/data_quality.json"))
        mlflow.log_artifact(str(root / "models/metadata.json"))
        print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    train()
