# HTTP Connector Registration

Register customer HTTP endpoints so approved agent actions execute against **their** APIs — not only built-in adapters (Stripe, Salesforce, etc.).

## Control plane UI

Control plane → **Register custom HTTP connector**

1. Enter display name, base URL, target system key, and tool names  
2. **Test connection** (demo mode skips live HTTP)  
3. **Register connector** — appears in the enterprise catalog immediately  

## API

```text
GET    /api/connectors/http
POST   /api/connectors/http
POST   /api/connectors/http/test
DELETE /api/connectors/http/{connector_id}
```

### Register (demo-friendly)

```bash
curl -X POST http://localhost:8000/api/connectors/http \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Acme Billing API",
    "base_url": "https://billing.acme.example",
    "target_system": "acme_billing",
    "tool_names": ["acme_billing.issue_credit"],
    "demo_mode": true
  }'
```

### Test before register

```bash
curl -X POST http://localhost:8000/api/connectors/http/test \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://billing.acme.example", "demo_mode": true}'
```

## Persistence

Registrations are stored in `AEGISAI_HTTP_CONNECTORS_FILE` (default: `services/api/data/http_connectors.json`).  
**Secrets are not persisted** — use `auth_secret_env` or pass `auth_value` only for local demos.

## Execution payload

On live execution (`demo_mode: false`), the broker `POST`s to `{base_url}{execute_path}`:

```json
{
  "tenant_id": "...",
  "case_id": "...",
  "proposal_id": "...",
  "action_type": "...",
  "target_system": "...",
  "amount_usd": 0,
  "idempotency_key": "..."
}
```

## Demo script

Use `demo_mode: true` for Bay Area / Zoom demos — catalog and governance flow work; HTTP is not called until the customer is ready for a pilot.
