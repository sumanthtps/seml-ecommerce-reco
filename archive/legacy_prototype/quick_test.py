"""Start both services, run the demo client, and shut everything down.

Use this script when you want a quick proof that the implementation works
without opening three separate terminals.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests

PROJECT_DIR = Path(__file__).resolve().parent
EVIDENCE_DIR = PROJECT_DIR / "evidence"


def find_free_port(start_port: int, blocked_ports: set[int] | None = None) -> int:
    """Return the first available local port at or above start_port."""
    blocked_ports = blocked_ports or set()
    for port in range(start_port, start_port + 50):
        if port in blocked_ports:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"no free port found from {start_port} to {start_port + 49}")


def wait_for_health(url: str, process: subprocess.Popen | None = None, timeout_seconds: int = 45) -> None:
    """Wait until a service responds to its health endpoint."""
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError(f"service process exited before it became healthy: {url}")
        try:
            response = requests.get(url, timeout=(1, 5))
            if response.status_code == 200:
                return
            last_error = RuntimeError(f"{url} returned {response.status_code}")
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"service did not become healthy: {url}") from last_error


def start_service(args: list[str], env: dict[str, str], log_name: str) -> subprocess.Popen:
    """Start one uvicorn process and write its logs under evidence/."""
    EVIDENCE_DIR.mkdir(exist_ok=True)
    log_path = EVIDENCE_DIR / log_name
    log_file = log_path.open("w", encoding="utf-8", buffering=1)
    return subprocess.Popen(
        args,
        cwd=PROJECT_DIR,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )


def stop_service(process: subprocess.Popen | None) -> None:
    """Stop a subprocess without leaving a local server running."""
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> None:
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
            "quick_test_recommendation_api.log",
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
            "quick_test_gateway.log",
        )
        wait_for_health(f"{gateway_url}/health", process=gateway_process)

        demo_env = os.environ.copy()
        demo_env["GATEWAY_URL"] = gateway_url
        print("Running demo_requests.py", flush=True)
        subprocess.run([sys.executable, "demo_requests.py"], cwd=PROJECT_DIR, env=demo_env, check=True)

        print("\nDemo completed successfully.", flush=True)
        print("Evidence written under: evidence/", flush=True)
        print("The temporary services will now stop.", flush=True)
        print("To keep Swagger open, run: python start_services.py", flush=True)
    finally:
        stop_service(gateway_process)
        stop_service(reco_process)


if __name__ == "__main__":
    main()

