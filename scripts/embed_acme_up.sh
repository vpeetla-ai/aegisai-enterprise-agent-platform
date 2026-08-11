#!/usr/bin/env bash
# Acme Support Agent Embed — one-click bring-up (ADR-032 / FDE P7).
# Spins Demo-local spine pieces with env templates. Strict ERAG optional.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_DIR="${ACME_EMBED_ENV_DIR:-$ROOT/.embed-acme}"
mkdir -p "$ENV_DIR"

cat > "$ENV_DIR/aegisai.env" <<'EOF'
AEGISAI_AUTH_MODE=dev
AEGISAI_SAML_PANEL_MODE=true
AEGISAI_SAML_DEFAULT_TENANT=acme
AEGISAI_WEBHOOK_HMAC_SECRET=acme-embed-dev-secret
AEGISAI_ENFORCE_AUTH=false
EOF

cat > "$ENV_DIR/finops.env" <<'EOF'
AGENTFINOPS_DB_BACKEND=sqlite
STRIPE_METER_LOCAL=true
STRIPE_METER_MIRROR=false
# STRIPE_API_KEY=sk_test_...
EOF

cat > "$ENV_DIR/erag.env" <<'EOF'
# Strict twin: PRODUCTION_STRICT=true RAG_JWT_SECRET=...
# Demo local leaves PRODUCTION_STRICT unset.
EOF

cat > "$ENV_DIR/SMOKE.md" <<'EOF'
# Acme embed smoke checklist

1. AegisAI `/health` 200
2. `POST /api/auth/saml/acs` panel login → session token
3. `POST /scim/v2/Users` creates acme user
4. `POST /api/webhooks/ingest` with bad sig → 401
5. Tenant health `GET /api/tenants/acme/health`
6. Optional: Strict ERAG `/health` with `review_mode=strict`
7. FinOps `GET /v1/billing/stripe/invoice-preview/acme`

Rollback: `./scripts/embed_acme_down.sh` then restore previous env files.
Gateway deny-all: set kill-switch scope tenant=acme via control plane.
EOF

echo "Wrote env templates to $ENV_DIR"
echo "Next:"
echo "  # Export and start services in separate terminals, e.g.:"
echo "  set -a; source $ENV_DIR/aegisai.env; set +a"
echo "  # from aegisai-enterprise-agent-platform: uvicorn ..."
echo "Smoke: $ENV_DIR/SMOKE.md"
echo "Strict ERAG: see enterprise_rag_platform/scripts/run_strict_local.sh or setup_strict_render.sh"
