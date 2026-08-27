#!/bin/bash
set -e

echo "=== MPLAD-SHIELD: Full Stack Startup ==="

echo "[1/3] Seeding database..."
python data/seed.py

echo "[2/3] Running ML pipeline..."
python pipeline/run_pipeline.py

echo "[3/3] Starting services..."
echo "  Starting API server on :8000..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "  Starting frontend on :5173..."
cd frontend && npm run dev &
FE_PID=$!

echo ""
echo "=== MPLAD-SHIELD Ready ==="
echo "  API:  http://localhost:8000/docs"
echo "  UI:   http://localhost:5173"
echo "  Press Ctrl+C to stop"
echo ""

wait $API_PID $FE_PID
