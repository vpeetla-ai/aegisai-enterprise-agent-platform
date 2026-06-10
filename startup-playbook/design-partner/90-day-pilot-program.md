# AegisAI Design Partner — 90-Day Pilot Program

## Purpose

Co-develop the **Governance Gateway** with 2–3 enterprises in **financial operations / customer remediation** and convert to paid Team or Enterprise tier.

## Production pilot configuration

```bash
AEGISAI_PILOT_MODE=true
AEGISAI_DB_BACKEND=postgres
AEGISAI_REQUIRE_EXECUTION_TOKEN=true
AEGISAI_ENFORCE_AUTH=true
AEGISAI_AUTH_MODE=oidc
AEGISAI_OIDC_ISSUER=https://your-tenant.okta.com/oauth2/default
AEGISAI_OIDC_AUDIENCE=api://aegisai
```

**North-star success metric:** `GET /api/governance/metrics` → **gateway_coverage_pct = 100%** for all in-scope side-effecting tools.

## Eligibility

- Regulated industry (financial services, insurance, health payer)  
- At least **one** production-bound agent workflow with side effects (refunds, CRM, data ops)  
- Executive sponsor (VP AI or Ops) + security stakeholder engaged  
- Willing to share anonymized metrics for case study  

## Pilot scope (in scope / out of scope)

### In scope

- Agent registry for up to **25** agents  
- Gateway SDK integration (Python or TypeScript)  
- One production connector (Stripe refunds **or** Salesforce cases)  
- Slack approval notifications  
- Policy simulator + OPA policy pack (FinOps)  
- Audit packet export for pilot workflows  
- Weekly office hours with AegisAI team  

### Out of scope (available as paid add-on)

- Multi-region VPC deployment  
- Custom GRC integrations  
- Unlimited connectors  
- 24/7 SLA  

## 90-day timeline

| Week | Milestone | Deliverable |
| --- | --- | --- |
| 1 | Kickoff | Success metrics signed, agent inventory imported |
| 2–3 | Dev integration | Gateway SDK wrapping tool calls in staging |
| 4 | Policy alignment | OPA policies reviewed with risk/compliance |
| 5–6 | HITL | Slack approvals live for medium+ risk |
| 7–8 | Production connector | Stripe or Salesforce in staging → prod |
| 9 | Red-team eval | Run red-team suite; remediate failures |
| 10–11 | Production pilot | ≥80% side-effecting calls through gateway |
| 12 | Executive review | ROI report + go/no-go for expansion |

## Success metrics (must agree at kickoff)

| Metric | Target |
| --- | --- |
| **Gateway coverage** | ≥80% of side-effecting tool calls routed through AegisAI |
| **Mean time to approve (p95)** | ≤30 minutes for medium risk (baseline vs pilot) |
| **Audit packet acceptance** | Compliance/risk signs off on sample packet |
| **Blocked high-risk actions** | ≥1 demonstrated block or escalate correctly handled |
| **Incident response** | Kill switch drill completed in <60 seconds |
| **Eval gate** | Golden + red-team pass before production promotion |

## Roles

| Role | Organization | AegisAI |
| --- | --- | --- |
| Executive sponsor | Accountable for pilot success | Quarterly business review |
| Technical lead | SDK + agent integration | Solution architect |
| Security | Policy + identity review | Security engineer |
| Ops reviewer | HITL user acceptance | Product |

## Commercial terms (template)

- **Duration:** 90 days  
- **Fee:** $[15k–35k] pilot fee *or* discounted Year 1 Team tier  
- **IP:** Customer owns their policies and data; AegisAI owns platform  
- **Case study:** Mutual approval for anonymized public reference  
- **Exit:** Export audit packets and registry; no lock-in of agent code  

## Go / no-go at day 90

### Go (expand)

- Gateway coverage ≥80%  
- Audit sign-off obtained  
- Executive sponsor approves budget for Team/Enterprise  

### Iterate

- Coverage 50–79% — extend 30 days with remediation plan  

### No-go

- Coverage <50% without committed engineering — pause and document learnings  

## Kickoff agenda (90 minutes)

1. Introductions and success metrics (20 min)  
2. Architecture walkthrough: propose → govern → execute (20 min)  
3. Agent inventory workshop (20 min)  
4. SDK integration planning (20 min)  
5. Weekly cadence and Slack channel (10 min)  

## Application form (copy for website)

- Company name, industry, employee count  
- Number of agents in pilot/production  
- Primary workflow for pilot (refund, dispute, deletion, other)  
- Frameworks in use  
- Executive sponsor name/title  
- Target start date  
