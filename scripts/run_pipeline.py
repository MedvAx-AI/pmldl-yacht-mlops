"""Run all DVC stages once, or at a five-minute start-to-start cadence."""
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

from filelock import FileLock, Timeout

ROOT = Path(__file__).resolve().parents[1]


def run_once():
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    try:
        with FileLock(logs / "pipeline.lock", timeout=0):
            started = datetime.now(timezone.utc)
            tick = time.monotonic()
            log_path = logs / (started.strftime("%Y%m%dT%H%M%S_%fZ") + ".log")
            env = os.environ.copy()
            env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
            env["DVC_NO_ANALYTICS"] = "1"
            env["PYTHONUTF8"] = "1"
            logging.info("Starting complete pipeline; output: %s", log_path.name)
            code = 1
            try:
                with log_path.open("w", encoding="utf-8") as output:
                    result = subprocess.run([sys.executable, "-m", "dvc", "repro", "--force", "--no-run-cache"], cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT)
                    code = result.returncode
            finally:
                record = {"started_at": started.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
                          "duration_seconds": round(time.monotonic()-tick, 2), "exit_code": code, "log": log_path.name}
                if code == 0:
                    metadata = json.loads((ROOT / "models/metadata.json").read_text(encoding="utf-8"))
                    record.update({key: metadata[key] for key in ("mlflow_run_id", "model_sha256")})
                with (logs / "runs.jsonl").open("a", encoding="utf-8") as history:
                    history.write(json.dumps(record) + "\n")
                logging.info("Pipeline result: %s", json.dumps(record))
                # Keep 100 full logs; lightweight run history remains available for the demo.
                for old in sorted(logs.glob("20*.log"))[:-100]:
                    old.unlink()
            return code
    except Timeout:
        logging.warning("Another pipeline run is active; skipping overlapping invocation")
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once; suitable for cron or Windows Task Scheduler")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between starts (minimum 300)")
    args = parser.parse_args()
    if args.interval < 300:
        parser.error("Use an interval of at least 300 seconds")
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), RotatingFileHandler(ROOT / "logs/scheduler.log", maxBytes=2_000_000, backupCount=2)])
    while True:
        started = time.monotonic()
        code = run_once()
        if args.once:
            return code
        duration = time.monotonic() - started
        if duration >= args.interval:
            logging.warning("Run exceeded interval; waiting one full interval to avoid a catch-up loop")
        time.sleep(args.interval if duration >= args.interval else args.interval-duration)


if __name__ == "__main__":
    sys.exit(main())
