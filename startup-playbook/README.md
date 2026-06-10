# AegisAI Startup Playbook

Commercial playbook for positioning, pitching, marketing, and selling **AegisAI Agent Governance Control Plane**.

## Contents

| Document | Audience | Purpose |
| --- | --- | --- |
| **[gtm/pitch-any-customer-playbook.md](gtm/pitch-any-customer-playbook.md)** | Sales, founders, SEs | **How to pitch any customer — same product, different story (SPAR)** |
| [pitch-deck/PITCH-DECK.md](pitch-deck/PITCH-DECK.md) | Investors, executives, design partners | Full narrative pitch deck (slide-by-slide) |
| [pitch-deck/compliance-buyer-slide.md](pitch-deck/compliance-buyer-slide.md) | Compliance, GRC, Internal Audit, Legal | Dedicated slide + talk track with signed audit quote |
| [gtm/icp-and-messaging.md](gtm/icp-and-messaging.md) | Marketing, sales | ICP, personas, messaging matrix |
| [gtm/sales-playbook.md](gtm/sales-playbook.md) | Sales, founders | Discovery, demo, objection handling, pricing |
| [gtm/marketing-playbook.md](gtm/marketing-playbook.md) | Marketing | Channels, content, campaigns, events |
| [compliance/eu-ai-act-soc2-mapping.md](compliance/eu-ai-act-soc2-mapping.md) | Security, compliance, procurement | Control mapping for enterprise buyers |
| [design-partner/90-day-pilot-program.md](design-partner/90-day-pilot-program.md) | Customer success, founders | Design partner pilot structure and success criteria |

## Product one-liner

**AegisAI helps regulated enterprises move AI agents from pilot to production by governing every agent, tool, policy decision, human approval, execution, and audit trail.**

## Wedge (go-to-market)

Start with **Financial Operations and Customer Remediation**: refunds, credits, chargebacks, fee reversals, account corrections, GDPR deletion/export, and compliance escalations.

## Implementation artifacts (Top 10 actions)

| # | Action | Location |
| --- | --- | --- |
| 1 | Governance Gateway SDK | `sdk/python/`, `apps/web/lib/gateway/` |
| 2 | Postgres persistence (full read/write) | `postgres_control_plane_store.py` · `AEGISAI_DB_BACKEND=postgres` |
| 2b | Connector catalog UI | `apps/web/components/control-plane/ConnectorCatalogPanel.tsx` |
| 2c | MCP governance proxy | `application/gateway/mcp_proxy.py` · `POST /api/mcp/tool-call` |
| 3 | OIDC / auth enforcement | `interfaces/http/auth.py` |
| 4 | OPA policy engine | `platform/policy/aegisai.rego`, `application/guardrails/opa_policy.py` |
| 5 | Enterprise connectors | `application/execution/connectors/registry.py` · `GET /api/connectors/catalog` (Stripe is one adapter) |
| 6 | Slack HITL approvals | `product/slack_approvals.py`, `POST /api/hitl/slack/*` |
| 7 | Compliance mapping | `compliance/eu-ai-act-soc2-mapping.md` |
| 8 | FinOps dashboard | `product/finops.py`, `GET /api/finops/dashboard`, UI panel |
| 9 | Red-team eval pack | `product/red_team_evals.py`, `POST /api/evaluations/red-team/run` |
| 10 | Design partner program | `design-partner/90-day-pilot-program.md` |
| 11 | **Signed audit packets + SSO** | `platform/operations/signed-audit-and-sso.md` |
