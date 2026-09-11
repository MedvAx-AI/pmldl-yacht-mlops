# TA demonstration (about 7 minutes)

1. Open the public GitHub repository. Show `dvc.yaml` and its prepare → train → deploy dependency graph (`dvc dag`).
2. Show Docker Desktop running Linux containers. Open http://localhost:8501 and http://localhost:8000/docs.
3. Show the six input fields, press **Predict resistance**, and change Froude number to see a different prediction. Expand the model explanation. The result includes an MLflow run ID.
4. Run `docker compose -f code/deployment/docker-compose.yml ps` to show **two separate healthy containers**. Explain `API_URL=http://api:8000` and the model baked into the API image.
5. Open generated `reports/data_quality.json`, `data/processed/train.csv`, and `test.csv`. Explain why hull identity is held out, and why learned outlier fences use only training data. The bundled clean data requires no artificial deletion.
6. Start `mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000`. At http://localhost:5000 show `yacht-resistance`, the test metrics, parameters, signature, and saved model.
7. Show the enabled Windows task (`Get-ScheduledTaskInfo -TaskName PMLDL-Yacht-Pipeline`) or the portable scheduler terminal. Show the timestamps in `logs/runs.jsonl`. Wait for the next five-minute start and inspect its timestamped log: **all three stages** execute.
8. After that run succeeds, refresh http://localhost:8000/model-info and make another prediction in the app. Match the new run ID with `models/metadata.json` and MLflow. The model checksum may stay the same because training is deterministic; the **run ID changes**.

## Useful commands

```powershell
Get-Content logs/runs.jsonl -Tail 3
Get-Content logs/scheduler.log -Tail 10
Get-ScheduledTaskInfo -TaskName PMLDL-Yacht-Pipeline
docker compose -f code/deployment/docker-compose.yml ps
```

If you need a manual run, disable the schedule first or wait for an active run to finish, then run `python scripts/run_pipeline.py --once`. The runner's lock prevents concurrent writes. Read the latest timestamped log on failure. A training quality-gate failure, missing raw file, or unavailable Docker daemon causes a failed run instead of a false success.

## Troubleshooting

- **Cannot connect to Docker:** start Docker Desktop, select Linux containers, and wait until `docker version` includes a Server section.
- **Ports already allocated:** stop the other program using ports 8000/8501. Keep the documented ports consistent with the deployment smoke test.
- **First build is slow:** allow downloads to finish before installing the schedule. Cached runs should fit within five minutes. Increase the interval if your hardware requires it.
- **Windows task did not run:** the user must be signed in, the computer awake, and Docker running. Check the task's last result and local logs. Reinstall the task if the repository is moved.
- **Model missing on a fresh clone:** run the complete pipeline; generated model binaries are intentionally not committed.
- **App reports temporary unavailability:** deployment briefly replaces containers. Wait for both health checks to pass and try again.

Disable the scheduler after the demonstration and use `docker compose -f code/deployment/docker-compose.yml down` to release the ports. Do not run two scheduler types simultaneously.
