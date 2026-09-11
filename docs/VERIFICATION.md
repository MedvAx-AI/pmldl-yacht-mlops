# Verification evidence

Verified on 2026-09-11 with Python 3.13 on Windows and Docker Desktop running Linux containers.

- Complete DVC prepare → train → deploy run: **passed**, 33.85 seconds with cached dependencies.
- Data: 308 clean observations; 238 training rows / 17 hulls, 70 testing rows / 5 hulls; no shared hull identities.
- Held-out metrics: MAE **0.566369**, RMSE **1.280232**, R² **0.993053**. Training-mean baseline RMSE: **15.360400**.
- `python -m pytest -q`: **10 passed**. Two upstream deprecation warnings concern the Starlette test client's HTTPX/AnyIO compatibility and do not affect serving.
- `python -m pip check`: **No broken requirements found**.
- Docker Compose: **two separate healthy containers**, `pmldl-yacht-api-1` and `pmldl-yacht-app-1`.
- Deployment smoke checks: a valid API prediction, matching model checksum and MLflow run ID, Streamlit health, and app-container-to-API prediction request all passed.

The initial verification caught overly aggressive outlier filtering of deliberately sparse experimental settings; the final code preserves those valid designs and tests preserve all 308 original observations. A one-time overlapping image warm-up caused an initial build failure; the subsequent complete run passed after the warm-up finished. Full development and scheduled-run history is retained locally under `logs/`.

Example generated reports are included under `reports/example-*.json`. Current reports, model packages, and MLflow storage are regenerated locally. This document records observed checks, not a guarantee of the service state after the machine is shut down.
