#!/usr/bin/env bash
# Canonical local API — must use PYTHONPATH=services/api/src so buyer-module routes load.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${AEGISAI_PORT:-8000}"
CANARY_URL="http://127.0.0.1:${PORT}/api/platform/developer-quickstart"

kill_stale_listener() {
  local pids
  pids="$(lsof -t -iTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -z "${pids}" ]]; then
    return 0
  fi
  echo "Stopping process(es) on port ${PORT}: ${pids}"
  kill ${pids} 2>/dev/null || true
  sleep 1
  pids="$(lsof -t -iTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    kill -9 ${pids} 2>/dev/null || true
    sleep 1
  fi
}

if lsof -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  if curl -sf "${CANARY_URL}" >/dev/null 2>&1; then
    echo "API already running on port ${PORT} with buyer-module routes. Open http://127.0.0.1:${PORT}/docs"
    exit 0
  fi
  echo "Port ${PORT} is in use by a STALE API (buyer routes missing — you get {\"detail\":\"Not Found\"})."
  if [[ "${AEGISAI_FORCE_RESTART:-}" == "1" ]]; then
    kill_stale_listener
  else
    echo "Re-run with: AEGISAI_FORCE_RESTART=1 ./scripts/start-api.sh"
    echo "Or manually: kill \$(lsof -t -iTCP:${PORT} -sTCP:LISTEN)"
    exit 1
  fi
fi

cd "${ROOT}/services/api"
export PYTHONPATH="${ROOT}/services/api/src${PYTHONPATH:+:$PYTHONPATH}"
echo "Starting AegisAI API on http://127.0.0.1:${PORT} (buyer-module routes enabled)"
exec python3 -m uvicorn aegisai.api:app --reload --host 127.0.0.1 --port "${PORT}"
