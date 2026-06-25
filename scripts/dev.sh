#!/usr/bin/env bash
# Start API + web together from repo root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Starting API (port 8000)…"
AEGISAI_FORCE_RESTART=1 "${ROOT}/scripts/start-api.sh" &
API_PID=$!

sleep 2

echo "==> Starting web (port 3000)…"
AEGISAI_FORCE_RESTART=1 AEGISAI_CLEAN_NEXT=1 "${ROOT}/scripts/start-web.sh" &
WEB_PID=$!

trap 'kill $API_PID $WEB_PID 2>/dev/null' EXIT

echo ""
echo "  Frontend:  http://localhost:3000"
echo "  API:       http://localhost:8000"
echo "  API docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both."

wait
