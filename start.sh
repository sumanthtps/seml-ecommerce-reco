#!/usr/bin/env bash
set -e

export GATEWAY_URL=${GATEWAY_URL:-http://127.0.0.1:8000}
export RECOMMENDATION_SERVICE_URL=${RECOMMENDATION_SERVICE_URL:-http://127.0.0.1:8001}

echo "Starting internal recommendation service on port 8001..."
python -m uvicorn recommendation_api:app --host 127.0.0.1 --port 8001 &

echo "Starting API gateway on port 8000..."
python -m uvicorn api_gateway:app --host 127.0.0.1 --port 8000 &

echo "Starting Streamlit UI on public port 7860..."
streamlit run frontend_app.py \
  --server.address=0.0.0.0 \
  --server.port=7860 \
  --server.headless=true