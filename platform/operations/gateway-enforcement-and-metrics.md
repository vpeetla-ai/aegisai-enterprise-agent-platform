# Gateway Enforcement & North-Star Metrics

## North-star KPI

**Gateway coverage %** — side-effecting agent tool calls routed through `POST /api/gateway/tool-request` before execution.

```text
GET /api/governance/metrics?tenant_id=bank-demo
```

Pilot target: **100%** within 90 days (`pilot_target_pct`).

## Mandatory execution token

When `AEGISAI_REQUIRE_EXECUTION_TOKEN=true`:

- `POST /api/execution/execute` **requires** header `X-AegisAI-Execution-Token`
- Token must be valid, unexpired, `gateway_decision=allow`
- Token `proposal_id` and `tool_name` must match the execution request
- Missing token → audit event `execution.denied.no_token`

### How agents get a token

1. **Auto-approve path:** `POST /api/gateway/tool-request` when `gateway_decision=allow`
2. **HITL path:** `POST /api/control-plane/reviewer-action` with `action=approve` returns `execution_token`

## Audit events (metrics source)

| Event | Meaning |
| --- | --- |
| `gateway.tool_request` | Tool call evaluated by gateway |
| `execution.token_bound` | Broker executed with valid token |
| `execution.denied.no_token` | Bypass attempt blocked |
| `gateway.token_issued` | Token issued after reviewer approval |

## OIDC JWKS (Okta / Azure AD)

```bash
AEGISAI_AUTH_MODE=oidc
AEGISAI_OIDC_ISSUER=https://login.microsoftonline.com/{tenant}/v2.0
AEGISAI_OIDC_AUDIENCE={application-client-id}
# Optional override:
AEGISAI_OIDC_JWKS_URI=
```

When `AEGISAI_OIDC_ISSUER` is set, Bearer tokens are verified against JWKS (not unverified decode).

## UI

Control plane shows **Gateway coverage** as the primary KPI, with a **12-minute buyer demo** stepper and collapsible reference sections.
