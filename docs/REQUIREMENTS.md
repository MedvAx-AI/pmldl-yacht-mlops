# Assignment coverage

The submission is the public repository URL: https://github.com/MedvAx-AI/pmldl-yacht-mlops.

| Requirement | Implementation | Inspectable evidence |
|---|---|---|
| Allowed dataset, neither CelebFaces nor smoking status | UCI Yacht Hydrodynamics | Included raw data, source, checksum and license |
| Load raw files | `code/datasets/prepare.py` | DVC `prepare` stage |
| Remove/impute missing values and remove outliers | Numeric coercion, missing/invalid row deletion, training-only IQR outlier filtering | Cleaning report and injected-corruption tests |
| Split and save train/test files | Deterministic split by hull identity | `data/processed/train.csv`, `test.csv`; disjoint-hull test |
| Feature engineering | Froude number powers in a packaged transformer | `code/models/train.py` |
| Train a simple model | Extra Trees, 80 bounded-depth trees | `models/model.joblib` |
| Evaluate and log test metrics | MAE, RMSE, R², baseline RMSE | `reports/metrics.json`, MLflow experiment |
| Package and log the model | Joblib pipeline plus MLflow sklearn flavor | Local model and MLflow model artifact |
| API in Docker | FastAPI with health, metadata and prediction endpoints | API Dockerfile; Compose API service |
| App in a separate Docker container | Streamlit form, prediction button and result display | App Dockerfile; Compose app service |
| App communicates with API | HTTP request to `http://api:8000/predict` | UI tests and deployment smoke test from app container |
| Pipeline deployment builds images and starts containers | `code/deployment/deploy.py` | `reports/deployment.json` |
| Automate the complete pipeline every 5 minutes | Forced DVC reproduction through a scheduled Python runner | Windows task / portable scheduler, `logs/runs.jsonl` |
| Logical repository structure | Recommended `code`, `data`, `models` layout; DVC instead of Airflow | Repository tree |
| Run/access instructions | Platform-specific setup, scheduler, service addresses, cleanup | README and `docs/DEMO.md` |
| Public GitHub repository | `MedvAx-AI/pmldl-yacht-mlops` | Public repository link |

The assignment's example tools and folder layout are recommendations. This solution adopts DVC, MLflow, FastAPI, Streamlit and Docker, while using the host scheduler instead of Airflow. A public internet server is not requested: deployment is to the local Docker host, ready to demonstrate through a browser.
