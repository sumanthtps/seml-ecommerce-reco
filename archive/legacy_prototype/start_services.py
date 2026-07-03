"""Start both FastAPI services and keep them running for manual testing.

Use this when you want to open Swagger UI or send manual API requests.
Press Ctrl+C to stop both services.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from quick_test import find_free_port, start_service, stop_service, wait_for_health

PROJECT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run gateway and recommendation services together.")
    parser.add_argument("--seconds", type=int, default=0, help="Stop automatically after this many seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    reco_port = find_free_port(8001)
    gateway_port = find_free_port(8000, blocked_ports={reco_port})
    reco_url = f"http://127.0.0.1:{reco_port}"
    gateway_url = f"http://127.0.0.1:{gateway_port}"

    reco_process: subprocess.Popen | None = None
    gateway_process: subprocess.Popen | None = None

    try:
        print(f"Starting recommendation service: {reco_url}", flush=True)
        reco_process = start_service(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "recommendation_api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(reco_port),
            ],
            os.environ.copy(),
            "start_services_recommendation_api.log",
        )
        wait_for_health(f"{reco_url}/health", process=reco_process)

        gateway_env = os.environ.copy()
        gateway_env["RECO_SERVICE"] = reco_url
        print(f"Starting API gateway: {gateway_url}", flush=True)
        gateway_process = start_service(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api_gateway:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(gateway_port),
            ],
            gateway_env,
            "start_services_gateway.log",
        )
        wait_for_health(f"{gateway_url}/health", process=gateway_process)

        print("\nServices are running.", flush=True)
        print(f"Gateway Swagger UI: {gateway_url}/docs", flush=True)
        print(f"Internal service Swagger UI: {reco_url}/docs", flush=True)
        print(f"Use this gateway URL for demo_requests.py: {gateway_url}", flush=True)
        print("Press Ctrl+C to stop.", flush=True)

        if args.seconds > 0:
            time.sleep(args.seconds)
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...", flush=True)
    finally:
        stop_service(gateway_process)
        stop_service(reco_process)
        print("Stopped.", flush=True)


if __name__ == "__main__":
    main()


