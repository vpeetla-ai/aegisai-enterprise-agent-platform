#!/usr/bin/env bash
# Tear down Acme embed local env artifacts (ADR-032).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_DIR="${ACME_EMBED_ENV_DIR:-$ROOT/.embed-acme}"

if [[ -d "$ENV_DIR" ]]; then
  rm -rf "$ENV_DIR"
  echo "Removed $ENV_DIR"
else
  echo "Nothing to remove at $ENV_DIR"
fi

echo "Rollback notes:"
echo "  - Restore previous service env files from your secrets store"
echo "  - Activate tenant kill-switch for acme if traffic must halt immediately"
echo "  - Strict ERAG: stop Render Starter or local run_strict_local process"
