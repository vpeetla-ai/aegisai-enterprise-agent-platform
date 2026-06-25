#!/usr/bin/env bash
# Start Next.js dev server with a clean .next cache (fixes missing CSS / broken layout).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${AEGISAI_WEB_PORT:-3000}"

kill_stale() {
  local pids
  pids="$(lsof -t -iTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    echo "Stopping process(es) on port ${PORT}: ${pids}"
    kill ${pids} 2>/dev/null || true
    sleep 1
  fi
}

if lsof -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  if [[ "${AEGISAI_FORCE_RESTART:-}" == "1" ]]; then
    kill_stale
  else
    echo "Port ${PORT} in use. Open http://localhost:${PORT} or re-run with AEGISAI_FORCE_RESTART=1"
    exit 0
  fi
fi

cd "${ROOT}/apps/web"
if [[ "${AEGISAI_CLEAN_NEXT:-1}" == "1" ]]; then
  echo "Clearing stale .next cache (fixes broken CSS)…"
  rm -rf .next
fi

echo "Starting AegisAI web on http://localhost:${PORT}"
exec npm run dev -- --port "${PORT}"
