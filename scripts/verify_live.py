"""Start both services, run the real HTTP demo, and shut them down safely."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import IO
from urllib.error import URLError
from urllib.request import urlopen

from ecom_ml.ml.data import generate_demo_interactions
from ecom_ml.ml.pipeline import train_pipeline
from run_demo import execute_demo

ROOT = Path(__file__).resolve().parents[1]


def wait_for(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return
        except URLError:
            time.sleep(0.1)
    raise TimeoutError(f"service did not become ready: {url}")


def start_service(module: str, port: int, log_handle: IO[str]) -> subprocess.Popen[str]:
    environment = os.environ.copy()
    environment["SEML_DATA_PATH"] = str(ROOT / "data" / "interactions.csv")
    environment["SEML_ARTIFACT_DIR"] = str(ROOT / "artifacts")
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            module,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=environment,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )


def main() -> int:
    data_path = ROOT / "data" / "interactions.csv"
    artifact_dir = ROOT / "artifacts"
    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    generate_demo_interactions(data_path)
    train_pipeline(data_path, artifact_dir)

    command_log_path = evidence_dir / "command_service.log"
    query_log_path = evidence_dir / "query_service.log"
    with (
        command_log_path.open("w", encoding="utf-8") as command_log,
        query_log_path.open("w", encoding="utf-8") as query_log,
    ):
        command_process = start_service("ecom_ml.command_service.main:app", 8101, command_log)
        query_process = start_service("ecom_ml.query_service.main:app", 8102, query_log)
        try:
            wait_for("http://127.0.0.1:8101/health")
            wait_for("http://127.0.0.1:8102/health")
            transcript = execute_demo("http://127.0.0.1:8101", "http://127.0.0.1:8102")
            output = evidence_dir / "live_demo.json"
            output.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
            recommendations = transcript["recommendation_query"]["recommendations"]
            assert len(recommendations) == 5
            print("LIVE VERIFICATION PASSED")
            print(f"model_version={transcript['recommendation_query']['model_version']}")
            print(f"recommendations={recommendations}")
            print(f"transcript={output}")
        finally:
            for process in (query_process, command_process):
                process.terminate()
            for process in (query_process, command_process):
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
