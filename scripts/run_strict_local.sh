#!/usr/bin/env bash
# Local Strict AegisAI — fail-closed policy profile for panels (no cloud bill).
# Usage: ./scripts/run_strict_local.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT="${AEGISAI_PORT:-8000}"
TOKEN_SECRET="${AEGISAI_EXECUTION_TOKEN_SECRET:-}"
if [[ -z "$TOKEN_SECRET" ]]; then
  TOKEN_SECRET="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)"
  echo "Generated AEGISAI_EXECUTION_TOKEN_SECRET for this session:"
  echo "  export AEGISAI_EXECUTION_TOKEN_SECRET='$TOKEN_SECRET'"
fi

export PRODUCTION_STRICT=true
export AEGISAI_REQUIRE_EXECUTION_TOKEN=true
export AEGISAI_ENFORCE_AUTH=true
export AEGISAI_POLICY_ENGINE="${AEGISAI_POLICY_ENGINE:-opa}"
export AEGISAI_EXECUTION_TOKEN_SECRET="$TOKEN_SECRET"
export AEGISAI_PORT="$PORT"

echo "Starting Strict AegisAI on http://127.0.0.1:${PORT}"
echo "Expect /health.enforcement.production_strict=true and policy_plane.fail_closed_for_irreversible=true"
echo "Docs: docs/STRICT_PANEL_PACK.md"
echo "Probe:  ./scripts/probe_strict_panel.sh"

# Prefer canonical starter with force-restart so Strict env replaces a demo listener.
export AEGISAI_FORCE_RESTART=1
exec ./scripts/start-api.sh
