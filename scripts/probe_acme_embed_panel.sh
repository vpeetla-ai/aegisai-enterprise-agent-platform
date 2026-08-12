#!/usr/bin/env bash
# Acme Support Agent Embed — zero-narration panel probe (ADR-032).
# Requires a running AegisAI API (local or Render). Does not start services.
# Mirrors services/api/tests/test_acme_embed.py break checks.
set -euo pipefail

BASE="${AEGISAI_URL:-${AEGISAI_BASE_URL:-http://127.0.0.1:8000}}"
BASE="${BASE%/}"
TENANT="${ACME_TENANT_ID:-acme}"

echo "== Acme embed probe → ${BASE} =="

python3 - "$BASE" "$TENANT" <<'PY'
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

base, tenant = sys.argv[1], sys.argv[2]
results = []


def record(step: str, code: int, ok: bool, extra=None):
    row = {"step": step, "status": code, "ok": ok}
    if extra:
        row["extra"] = extra
    results.append(row)
    print(json.dumps(row, indent=2))


def http(method: str, path: str, *, data=None, headers=None, form=None):
    url = f"{base}{path}"
    h = dict(headers or {})
    body = None
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        h.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif data is not None:
        body = json.dumps(data).encode()
        h.setdefault("Content-Type", "application/json")
    h.setdefault("Accept", "application/json")
    request = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(request, timeout=45) as resp:
            raw = resp.read().decode() or "{}"
            payload = json.loads(raw) if raw.strip().startswith(("{", "[")) else {"raw": raw}
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() if exc.fp else ""
        try:
            payload = json.loads(raw) if raw else {"error": str(exc)}
        except json.JSONDecodeError:
            payload = {"error": raw or str(exc)}
        return exc.code, payload


print("== 1. health ==")
code, _ = http("GET", "/health")
record("GET /health", code, 200 <= code < 300)

print("== 2. SAML panel ACS (form) ==")
code, saml = http(
    "POST",
    "/api/auth/saml/acs",
    form={
        "principal_id": f"panel@{tenant}.example",
        "tenant_id": tenant,
        "roles": "workflow_owner,reviewer",
    },
)
ok = code == 200 and isinstance(saml, dict) and "session_token" in saml
record("POST /api/auth/saml/acs", code, ok, {"auth_mode": saml.get("auth_mode") if isinstance(saml, dict) else None})

print("== 3. SCIM Users create ==")
code, _ = http(
    "POST",
    "/scim/v2/Users",
    data={
        "userName": f"panel.operator@{tenant}.example",
        "tenantId": tenant,
        "roles": ["workflow_owner", "reviewer"],
        "allowed_tools": ["notify.slack"],
    },
    headers={"X-AegisAI-Tenant": tenant},
)
record("POST /scim/v2/Users", code, code in {200, 201, 409})

print("== 4. webhook bad HMAC → 401 ==")
payload = {"webhook_id": "slack.interaction", "tenant_id": tenant, "payload": {"text": "approve x"}}
raw = json.dumps(payload).encode()
request = urllib.request.Request(
    f"{base}/api/webhooks/ingest",
    data=raw,
    headers={"Content-Type": "application/json", "X-AegisAI-Signature": "sha256=deadbeef"},
    method="POST",
)
try:
    with urllib.request.urlopen(request, timeout=45) as resp:
        code = resp.status
except urllib.error.HTTPError as exc:
    code = exc.code
record("POST /api/webhooks/ingest (bad sig)", code, code == 401)

print("== 5. tenant health ==")
code, health = http("GET", f"/api/tenants/{tenant}/health")
ok = code == 200 and isinstance(health, dict) and health.get("tenant_id") == tenant
record(f"GET /api/tenants/{tenant}/health", code, ok)

failed = [r for r in results if not r["ok"]]
print("== summary ==")
print(json.dumps({"base": base, "tenant": tenant, "failed": failed, "checks": results}, indent=2))
if failed:
    raise SystemExit("acme_embed_probe_failed")
print("acme_embed_probe_ok=true")
PY

echo "Next: operator wiring (IdP/Slack/SFDC/Stripe/Strict) →"
echo "  https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/ACME_EMBED_OPERATOR_WIRING.md"
echo "Cold Free-tier APIs: ai-architecture-portfolio/docs/PANEL_DAY_FREE_RUNBOOK.md"
echo "Optional harness: python scripts/run_acme_embed_harness.py --score"
