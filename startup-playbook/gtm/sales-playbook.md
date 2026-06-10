# Sales Playbook

## Sales motion

**Land:** Design partner pilot (90 days) → **Expand:** More agents, connectors, tenants → **Renew:** Compliance + FinOps modules

## Discovery questions

### Situation

1. How many AI agents are in pilot vs production?  
2. Which frameworks (LangGraph, Bedrock, Copilot, custom)?  
3. What side-effecting tools do they call (payments, CRM, data platform)?  

### Pain

4. Has security or audit blocked an agent deployment? Tell me about it.  
5. Can you produce evidence for *why* an automated refund or data change happened?  
6. Who owns each agent today — by name and business domain?  

### Impact

7. What does a mistaken refund or unauthorized data change cost?  
8. How long does manual approval take for high-risk cases today?  

### Decision

9. Who must sign off for production AI in your org (CISO, legal, ops)?  
10. What would a successful 90-day pilot prove?

## Demo script (25 minutes)

| Min | Section | Show |
| --- | --- | --- |
| 0–3 | Problem | Agent sprawl slide; ask discovery Q1–3 |
| 3–8 | Executive value | Control plane posture, registry, FinOps |
| 8–15 | Runtime | Gateway test → escalate → Slack approval → execute |
| 15–20 | Assurance | Audit PDF export, policy simulator |
| 20–23 | BYOA | Gateway SDK snippet (Python) |
| 23–25 | Next steps | Design partner one-pager |

## Objection handling

| Objection | Response |
| --- | --- |
| “We use Langfuse already.” | Great for traces. AegisAI owns **approval authority** and **execution** — we export to Langfuse, not replace it. |
| “Our cloud has guardrails.” | Point solutions per cloud. You have agents on 3 frameworks — we govern all tool calls one way. |
| “We’ll build internally.” | 12–18 months for broker + audit + HITL + policy. Pilot in 90 days with our gateway SDK. |
| “Too early for agents.” | Refund and dispute bots are already here. Governance debt compounds every quarter. |
| “Security will never allow auto-approve.” | Risk-based HITL — auto-approve only low risk; sample near-threshold actions. |

## Pricing talk track

- **Design partner:** Discounted pilot, case study, roadmap influence  
- **Team:** Per month + included tool calls tier  
- **Enterprise:** ACV based on agents governed + connectors + VPC  

## Closing criteria (qualified opportunity)

- [ ] Named executive sponsor  
- [ ] Champion with production agent timeline  
- [ ] At least one workflow with money or PII movement  
- [ ] Security engaged (not surprised at week 8)  
- [ ] Success metrics agreed (gateway coverage %, audit sign-off)

## CRM stages

1. **Qualified** — ICP fit + discovery complete  
2. **Pilot scoped** — 90-day doc signed  
3. **Technical win** — Gateway integrated in dev  
4. **Production pilot** — % tool calls through gateway  
5. **Commercial** — MSA + expansion plan  
