"""Build both images, replace services, and verify the deployed model identity."""
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ["docker", "compose", "-f", str(ROOT / "code/deployment/docker-compose.yml")]
SAMPLE = {"buoyancy": -2.3, "prismatic": 0.558, "length_displacement": 4.78, "beam_draught": 3.99, "length_beam": 3.17, "froude": 0.3}


def deploy():
    # Build before touching healthy running services. A training/build failure leaves them running.
    subprocess.run(COMPOSE + ["build"], cwd=ROOT, check=True, timeout=1800)
    subprocess.run(COMPOSE + ["up", "-d", "--force-recreate", "--wait", "--wait-timeout", "120"], cwd=ROOT, check=True, timeout=180)
    metadata = json.loads((ROOT / "models/metadata.json").read_text(encoding="utf-8"))
    request = Request("http://localhost:8000/predict", data=json.dumps(SAMPLE).encode(), headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        prediction = json.load(response)
    if prediction["model_sha256"] != metadata["model_sha256"] or prediction["mlflow_run_id"] != metadata["mlflow_run_id"]:
        raise RuntimeError("API is serving a stale model")
    if not math.isfinite(prediction["resistance"]) or prediction["resistance"] < 0:
        raise RuntimeError("Invalid deployed prediction")
    with urlopen("http://localhost:8501/_stcore/health", timeout=15) as response:
        if response.status != 200:
            raise RuntimeError("Streamlit is unhealthy")
    # Also exercise the app container's internal route to the API.
    subprocess.run(COMPOSE + ["exec", "-T", "app", "python", "-c",
        "import os,requests; r=requests.post(os.environ['API_URL']+'/predict',json=" + repr(SAMPLE) + ",timeout=15); r.raise_for_status(); print(r.json())"], check=True, timeout=30)
    receipt = {"deployed_at": datetime.now(timezone.utc).isoformat(), "status": "healthy", "prediction": prediction}
    (ROOT / "reports/deployment.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    deploy()
