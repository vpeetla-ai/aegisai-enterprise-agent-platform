#!/usr/bin/env bash
# Acme Support Agent Embed — env templates + smoke pointer (ADR-032 / FDE P7).
# Honesty: this writes Demo-local env files; it does not start Render services or
# wire live IdP/Slack/SFDC. Run probe_acme_embed_panel.sh against a live API.
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

cat > "$ENV_DIR/SMOKE.md" <<EOF
# Acme embed smoke checklist

## Zero-narration probe (preferred)

With AegisAI running (local uvicorn or Render):

\`\`\`bash
set -a; source ${ENV_DIR}/aegisai.env; set +a
export AEGISAI_URL=http://127.0.0.1:8000   # or https://aegisai-api.onrender.com
./scripts/probe_acme_embed_panel.sh
\`\`\`

Expect: \`acme_embed_probe_ok=true\` (health, SAML ACS, SCIM, bad webhook→401, tenant health).

## Manual checklist

1. AegisAI \`/health\` 200
2. \`POST /api/auth/saml/acs\` panel login → \`session_token\`
3. \`POST /scim/v2/Users\` creates acme user
4. \`POST /api/webhooks/ingest\` with bad sig → 401
5. Tenant health \`GET /api/tenants/acme/health\`
6. Optional: Strict ERAG \`/health\` with \`review_mode=strict\`
7. FinOps \`GET /v1/billing/stripe/invoice-preview/acme\`

## Honesty

- \`embed_acme_up.sh\` = **env templates** + this smoke pointer (not live IdP/Slack/SFDC).
- Operator wiring (live vendors): [ACME_EMBED_OPERATOR_WIRING.md](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/ACME_EMBED_OPERATOR_WIRING.md)
- Free-tier cold starts: [PANEL_DAY_FREE_RUNBOOK.md](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/PANEL_DAY_FREE_RUNBOOK.md)

Rollback: \`./scripts/embed_acme_down.sh\` then restore previous env files.
Gateway deny-all: set kill-switch scope tenant=acme via control plane.
EOF

chmod +x "$ROOT/scripts/probe_acme_embed_panel.sh" 2>/dev/null || true

echo "Wrote env templates to $ENV_DIR"
echo "Honesty: templates only — not live vendor wiring."
echo "Next:"
echo "  set -a; source $ENV_DIR/aegisai.env; set +a"
echo "  # start AegisAI API, then:"
echo "  AEGISAI_URL=http://127.0.0.1:8000 ./scripts/probe_acme_embed_panel.sh"
echo "Smoke: $ENV_DIR/SMOKE.md"
echo "Operator wiring:"
echo "  https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/ACME_EMBED_OPERATOR_WIRING.md"
