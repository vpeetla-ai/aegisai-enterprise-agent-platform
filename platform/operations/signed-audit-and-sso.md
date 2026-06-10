# Signed Audit Packets & SSO Enforcement

## Why this upgrade

| Capability | Buyer value |
| --- | --- |
| **Signed audit packets** | Compliance can trust archived evidence was not altered (SOC2, EU AI Act) |
| **SSO on mutating APIs** | Security approves production pilots; every action tied to a principal |

## Signed audit packets

### Modes

| Mode | Environment variable | Use case |
| --- | --- | --- |
| `local_hmac` | `AEGISAI_AUDIT_SIGNING_MODE=local_hmac` | Portfolio, local dev |
| `kms` | `AEGISAI_AUDIT_SIGNING_MODE=kms` + `AEGISAI_AUDIT_KMS_KEY_ID` | Production (AWS KMS) |

### API

```text
GET  /api/audit-packets/{tenant_id}/{case_id}.signed.json
GET  /api/audit-packets/{tenant_id}/{case_id}.pdf?signed=true
POST /api/audit-packets/verify
GET  /api/audit-signing/posture
```

### Demo flow

1. Run an agent case (`POST /api/agents/run`)
2. Download signed packet from control plane UI
3. Click **Verify signature** — shows Valid/Invalid

## SSO / authentication

### Configuration

```bash
# Development (headers)
AEGISAI_AUTH_MODE=dev
AEGISAI_ENFORCE_AUTH=false
# curl -H "X-AegisAI-Principal: platform-lead" -H "X-AegisAI-Roles: workflow_owner" ...

# Production pilot
AEGISAI_AUTH_MODE=oidc
AEGISAI_ENFORCE_AUTH=true
# curl -H "Authorization: Bearer <id_token>" -H "X-AegisAI-Roles: senior_domain_approver" ...
```

### API

```text
GET /api/auth/posture
```

All `POST` mutating control-plane routes require `AuthRequired` or `ReviewerAuthRequired` dependencies.

When `AEGISAI_ENFORCE_AUTH=true`, anonymous `portfolio-user` defaults are rejected.
