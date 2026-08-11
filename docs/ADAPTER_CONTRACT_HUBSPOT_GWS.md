# Connector adapter contract — HubSpot / Google Workspace (Out of scope)

**Status:** Interface-only. Acme Support Agent Embed (ADR-032) ships **Slack** + **Salesforce** Case.
HubSpot CRM and Google Workspace are **explicitly out of scope** for the 90-day wedge — this page exists so panels see how a third connector would plug in without fake logos.

## Contract

Every enterprise connector must:

1. Implement `EnterpriseConnector` (`can_handle` / `execute`) in AegisAI `connectors/`.
2. Accept `ConnectorExecutionContext` with `tenant_id`, `idempotency_key`, `dry_run`.
3. Retry with bounded backoff; surface failures to operator DLQ / webhook engine.
4. Never bypass AegisAI gateway / HITL for irreversible side effects.
5. Emit FinOps usage under `scope_type=tenant` when paid APIs are called.

## HubSpot (future)

| Concern | Expected shape |
|---------|----------------|
| Auth | OAuth2 private app / refresh token in env |
| Objects | Ticket create/update minimal |
| Tool names | `crm.hubspot.update_ticket` |
| Failure | HTTP 5xx → retry → DLQ |

## Google Workspace (future)

| Concern | Expected shape |
|---------|----------------|
| Auth | Service account domain-wide delegation |
| Objects | Gmail draft / Docs append (read-mostly preferred) |
| Tool names | `gws.gmail.draft_reply` |
| Failure | Same retry/DLQ contract |

## Honesty

Do not claim HubSpot or GWS packs are Demonstrated. Point reviewers here + to Slack/Salesforce code paths instead.
