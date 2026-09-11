import importlib.util
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load("prepare", "code/datasets/prepare.py")


def test_cleaning_rejects_missing_duplicates_and_invalid_values():
    row = [-2.3, 0.558, 4.78, 3.99, 3.17, 0.3, 5.0]
    rows = [row, row.copy(), [np.nan] + row[1:], row[:5] + [-1, 5], row[:6] + [-1], row[:2] + [np.inf] + row[3:]]
    assert len(prepare.clean_data(pd.DataFrame(rows, columns=prepare.FEATURES + [prepare.TARGET]))) == 1


def test_outlier_filter_removes_extreme_training_feature():
    frame = pd.DataFrame({f: list(np.linspace(1, 2, 100)) + [1000] for f in prepare.FEATURES})
    frame[prepare.TARGET] = 1
    cleaned, _ = prepare.remove_training_outliers(frame)
    assert len(cleaned) == 100


def test_split_is_reproducible_and_hulls_do_not_overlap(tmp_path):
    (tmp_path / "data/raw").mkdir(parents=True)
    shutil.copy(ROOT / "data/raw/yacht_hydrodynamics.data", tmp_path / "data/raw")
    prepare.prepare(tmp_path)
    train = pd.read_csv(tmp_path / "data/processed/train.csv")
    test = pd.read_csv(tmp_path / "data/processed/test.csv")
    hulls = prepare.FEATURES[:5]
    assert set(map(tuple, train[hulls].to_numpy())).isdisjoint(set(map(tuple, test[hulls].to_numpy())))
    before = (tmp_path / "data/processed/train.csv").read_bytes()
    prepare.prepare(tmp_path)
    assert before == (tmp_path / "data/processed/train.csv").read_bytes()
    assert len(train) + len(test) == 308


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("MODEL_DIR", str(ROOT / "models"))
    api = load("yacht_api", "code/deployment/api/main.py")
    with TestClient(api.app) as client:
        yield client


SAMPLE = {"buoyancy": -2.3, "prismatic": 0.558, "length_displacement": 4.78, "beam_draught": 3.99, "length_beam": 3.17, "froude": 0.3}


def test_api_uses_packaged_model_and_reports_identity(client):
    import joblib
    metadata = json.loads((ROOT / "models/metadata.json").read_text())
    expected = joblib.load(ROOT / "models/model.joblib").predict(pd.DataFrame([SAMPLE], columns=metadata["features"]))[0]
    response = client.post("/predict", json=SAMPLE)
    assert response.status_code == 200
    assert response.json()["resistance"] == pytest.approx(expected)
    assert client.get("/health").json()["model_sha256"] == metadata["model_sha256"]


@pytest.mark.parametrize("payload", [{}, {**SAMPLE, "froude": -1}, {**SAMPLE, "prismatic": 2}, {**SAMPLE, "surprise": 1}])
def test_api_rejects_invalid_input(client, payload):
    assert client.post("/predict", json=payload).status_code == 422


def test_ui_prediction_uses_api_and_displays_result(monkeypatch):
    calls = []
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"resistance": 4.321, "unit": "dimensionless", "warnings": [], "mlflow_run_id": "test-run"}
    def post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()
    monkeypatch.setattr("requests.post", post)
    app = AppTest.from_file(str(ROOT / "code/deployment/app/app.py")).run()
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "4.321"
    assert calls[0][0].endswith("/predict")
    assert calls[0][1]["json"] == SAMPLE


def test_ui_handles_api_outage(monkeypatch):
    import requests
    def post(*args, **kwargs):
        raise requests.ConnectionError("unavailable")
    monkeypatch.setattr("requests.post", post)
    app = AppTest.from_file(str(ROOT / "code/deployment/app/app.py")).run()
    app.button[0].click().run()
    assert not app.exception
    assert "temporarily unavailable" in app.error[0].value
