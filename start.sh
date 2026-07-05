#!/usr/bin/env bash
set -e

export PYTHONPATH=/app:/app/backend

echo "Starting Command Service on port 8101..."
python -m uvicorn ecom_ml.command_service.main:app \
  --host 127.0.0.1 \
  --port 8101 &

COMMAND_PID=$!

echo "Starting Query Service on port 8102..."
python -m uvicorn ecom_ml.query_service.main:app \
  --host 127.0.0.1 \
  --port 8102 &

QUERY_PID=$!

sleep 3

if ! kill -0 "$COMMAND_PID" 2>/dev/null; then
  echo "Command Service failed to start"
  exit 1
fi

if ! kill -0 "$QUERY_PID" 2>/dev/null; then
  echo "Query Service failed to start"
  exit 1
fi

echo "Starting Streamlit UI on public port 7860..."
streamlit run frontend/app.py \
  --server.address=0.0.0.0 \
  --server.port=7860 \
  --server.headless=true