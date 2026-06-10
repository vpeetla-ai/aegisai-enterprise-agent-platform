#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "==> [1/3] Frontend lint"
npm -C "apps/web" run lint

echo "==> [2/3] Frontend build"
npm -C "apps/web" run build

echo "==> [3/3] Backend tests"
python3 -m pytest -q

echo "==> Verification complete"
