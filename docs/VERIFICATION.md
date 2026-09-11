# Verification evidence

Verified on 2026-09-11 with Python 3.13 on Windows and Docker Desktop running Linux containers.

- Complete DVC prepare → train → deploy run: **passed**, 33.85 seconds with cached dependencies.
- Data: 308 clean observations; 238 training rows / 17 hulls, 70 testing rows / 5 hulls; no shared hull identities.
- Held-out metrics: MAE **0.566369**, RMSE **1.280232**, R² **0.993053**. Training-mean baseline RMSE: **15.360400**.
- `python -m pytest -q`: **10 passed**. Two upstream deprecation warnings concern the Starlette test client's HTTPX/AnyIO compatibility and do not affect serving.
- `python -m pip check`: **No broken requirements found**.
- Docker Compose: **two separate healthy containers**, `pmldl-yacht-api-1` and `pmldl-yacht-app-1`.
- Deployment smoke checks: a valid API prediction, matching model checksum and MLflow run ID, Streamlit health, and app-container-to-API prediction request all passed.
- Browser verification: submitted the form against the live containers. Froude **0.300 → 3.903** predicted resistance; changing only Froude to **0.400 → 21.215**. A [screenshot](app-prediction.png) records the second result.
- Independent [GitHub Actions Linux run](https://github.com/MedvAx-AI/pmldl-yacht-mlops/actions/runs/34609059815): **passed**, including fresh dependency installation, all three DVC stages, real Docker deployment, and all 10 tests.

## Observed five-minute automation

Windows Task Scheduler task **PMLDL-Yacht-Pipeline** launched these runs without manual intervention. Times below are UTC (add three hours for the local Moscow timezone):

| Started | Duration | Result | MLflow run ID |
|---|---:|---|---|
| 2026-09-11 14:15:05.800 | 34.35 s | Success | `9c6fdde85c804f42a0f55f12f9fe799c` |
| 2026-09-11 14:20:06.760 | 34.18 s | Success | `dac3827f1f9d4235a43733b9b1d463d1` |

Starts are 300.96 seconds apart (normal task-launch jitter). Both full logs contain `prepare`, `train`, and `deploy`; both deployment receipts verify the new run ID. The Task Scheduler last result was **0**, and its repetition interval is **PT5M**. A compact machine-readable copy is in [example-scheduled-runs.json](../reports/example-scheduled-runs.json).

The deterministic model SHA-256 remained `4cacb457db90bdf90524757b73064fc897870a72ce0802d50112f9a93830bf36`, while the run IDs changed, proving repeated training and deployment. Keep Docker Desktop running, the computer awake, and the user signed in for future scheduled runs.

The initial verification caught overly aggressive outlier filtering of deliberately sparse experimental settings; the final code preserves those valid designs and tests preserve all 308 original observations. A one-time overlapping image warm-up caused an initial build failure; the subsequent complete run passed after the warm-up finished. Full development and scheduled-run history is retained locally under `logs/`.

Example generated reports are included under `reports/example-*.json`. A small trained model package and matching metadata are included in `models/`; current reports, packages, and MLflow storage are regenerated locally. This document records observed checks, not a guarantee of the service state after the machine is shut down.
