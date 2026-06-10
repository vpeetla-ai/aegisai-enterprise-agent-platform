# ICP & Messaging

## Ideal Customer Profile (primary)

| Attribute | Definition |
| --- | --- |
| **Industry** | Banking, insurance, health payer, fintech, telco |
| **Size** | 2,000–50,000 employees; $500M–$20B revenue |
| **AI maturity** | 10–200 agents in pilot; 2+ frameworks in use |
| **Trigger** | Security blocked production agent; audit finding; refund incident |
| **Budget holder** | VP Enterprise AI + CISO + Ops SVP (joint) |

## Personas

### Economic buyer — CIO / CISO

- **Cares about:** Audit defensibility, incident containment, vendor neutrality  
- **Message:** *Prove every agent action with an exportable audit packet and runtime kill switches.*

### Champion — AI Platform Lead

- **Cares about:** Ship agents without being blamed for incidents  
- **Message:** *One gateway SDK — govern LangGraph, OpenAI, and Bedrock agents the same way.*

### User — Operations reviewer

- **Cares about:** Fast, safe decisions with evidence  
- **Message:** *Approve in Slack with risk score, policy reason, and citations — not another inbox.*

### Influencer — Risk / Compliance

- **Cares about:** Policy versioning, human oversight, EU AI Act alignment  
- **Message:** *Policy-as-code with simulation before production and post-hoc audit packets.*

## Messaging matrix

| Audience | Headline | Proof point |
| --- | --- | --- |
| Executive | Stop agent sprawl before it becomes agent risk | Executive posture dashboard |
| Platform | Govern any agent without rewriting your stack | Gateway SDK + integration posture |
| Security | No side effect without identity, policy, and token | Gateway enforcement steps |
| Compliance | Reconstruct any case in one PDF | Audit packet export |
| FinOps | See cost and risk per agent | FinOps dashboard + registry |

## Elevator pitches

**10 seconds:**  
AegisAI is the control plane that governs enterprise AI agents — who owns them, what tools they can call, and what gets executed after human approval.

**30 seconds:**  
Teams are deploying agents in LangGraph, Copilot, and Bedrock faster than they can control them. AegisAI inventories every agent, routes side-effecting tool calls through a governance gateway, requires HITL for high-risk work, executes only through an approval-gated broker, and exports audit packets compliance can sign off on. We start with financial operations: refunds, credits, and privacy remediation.

**60 seconds:**  
Add the architecture slide: agents propose, never directly execute; policy and eval gates decide; reviewers approve in Slack; Stripe and CRM connectors run with idempotency; hash-chained audit ledger captures the full chain.

## Words to use / avoid

| Use | Avoid |
| --- | --- |
| Control plane, governance gateway | “Chatbot platform” |
| Agent inventory, tool authority | “Prompt management only” |
| Audit packet, execution broker | “Fully autonomous AI” |
| Design partner, pilot | “Free forever for enterprise” |
