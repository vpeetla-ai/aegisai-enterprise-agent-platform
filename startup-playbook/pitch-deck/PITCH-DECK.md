# AegisAI — Investor & Enterprise Pitch Deck

> **Format:** One section = one slide. Copy into Google Slides, Keynote, or Pitch with your brand theme.

---

## Slide 1 — Title

**AegisAI**  
*Agent Governance Control Plane for regulated enterprise AI*

- Govern agents built anywhere: LangGraph, OpenAI, Bedrock, Copilot Studio, custom
- Discover → Govern → Execute → Assure
- **Founder:** [Your name] · **Contact:** [email] · **Stage:** Seed / Design partners

---

## Slide 2 — The problem (2026 reality)

Enterprises adopted AI agents **faster than they can govern them**.

| Pain | Business impact |
| --- | --- |
| **Agent sprawl** | No owner, no inventory, shadow production |
| **Tool sprawl** | Refunds, CRM updates, data deletes without consistent controls |
| **Policy opacity** | Nobody can explain why auto-approved vs blocked |
| **Audit gaps** | Compliance cannot reconstruct who approved what was executed |
| **Unclear ROI** | Leaders cannot tie agent spend to risk reduction or cycle time |

**Result:** Pilots stall. Production agents get blocked by security. Or worse — they ship without controls.

---

## Slide 3 — Why now

1. **Multi-framework agents** — no single vendor owns the stack  
2. **MCP tool standardization** — more tools, more attack surface  
3. **EU AI Act & SOC2 pressure** — traceability and human oversight required  
4. **AI FinOps** — CFOs demand cost and risk accountability per agent  
5. **HITL is back** — autonomy without accountability fails in regulated ops  

**Window:** First neutral **runtime control plane** wins the governance layer.

---

## Slide 4 — What we are (and are not)

### We are

The **runtime control plane** that lets enterprises:

- **Discover** every agent (owner, tools, risk, cost)
- **Govern** tool calls (policy, evals, kill switches)
- **Approve** high-risk work (HITL in Slack/Teams)
- **Execute** only approved side effects (broker + connectors)
- **Assure** auditors (signed audit packets, hash chain)

### We are not

- Another agent builder (LangGraph/CrewAI compete here — we partner)
- Another observability dashboard (Langfuse/LangSmith — we integrate)
- Generic workflow automation (ServiceNow/UiPath — we add LLM risk layer)

---

## Slide 5 — Product demo story (90 seconds)

1. **Executive opens control plane** — posture score, high-risk agents, open incidents  
2. **Platform engineer onboards agent** — readiness score, missing controls  
3. **Agent proposes $2,500 refund** — RAG evidence, risk escalate, HITL queue  
4. **Reviewer approves in Slack** — execution token issued  
5. **Broker executes via registered connector** (Stripe, Salesforce, ServiceNow, MCP, custom HTTP) — idempotent, auditable  
6. **Auditor exports PDF packet** — policy version, traces, approval, execution chain  

**Tagline:** *Agents propose. AegisAI decides. The broker executes.*

---

## Slide 6 — Solution architecture

```text
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Any Agent   │────▶│ Governance       │────▶│ Execution       │
│ Framework   │     │ Gateway + Policy │     │ Broker          │
└─────────────┘     │ + HITL + Evals   │     │ (Stripe, CRM…)  │
                    └────────┬─────────┘     └────────┬────────┘
                             │                        │
                    ┌────────▼─────────┐     ┌────────▼────────┐
                    │ Audit Ledger     │     │ Enterprise SoR  │
                    │ (hash-chained)   │     │                 │
                    └──────────────────┘     └─────────────────┘
```

**Design principle:** Observability exports traces; **AegisAI owns approval authority and audit truth.**

---

## Slide 7 — Initial wedge: FinOps & remediation

| Workflow | Why this wedge |
| --- | --- |
| Refunds & credits | Money movement + thresholds |
| Chargebacks | Dispute risk + audit |
| Fee reversals | High volume, policy rules |
| GDPR delete/export | Privacy officer routing |
| Fraud escalations | Critical risk, block paths |

**Buyer:** VP Enterprise AI + Ops SVP + CISO (shared pain)  
**Champion:** AI platform engineer blocked by security on production agents

---

## Slide 7b — Compliance / GRC buyer (dedicated)

**Audience:** Chief Compliance Officer, Internal Audit, Risk, Legal, Privacy, GRC  
**Use standalone:** [compliance-buyer-slide.md](compliance-buyer-slide.md)

### Headline

**Prove every AI agent action — not just observe it**

### The message (hero quote)

> **“Observability tools show traces; we provide tamper-evident audit artifacts your GRC team can archive.”**

### Their pain

- Traces explain model behavior — not **who authorized** a side effect  
- Policy PDFs ≠ proof of **what happened in production**  
- Reconstructing an automated action takes days — or fails entirely  

### What we deliver (Assure)

| Evidence | Included in audit packet |
| --- | --- |
| Policy version + reason codes | Why auto-approved, escalated, or blocked |
| Human oversight | Approver identity, role, timestamp |
| Execution proof | Broker-only side effects + external reference |
| Tamper evidence | Hash-chained ledger + **signed packet** + verify API |

### Observability vs AegisAI

| | Langfuse / LangSmith | AegisAI |
| --- | --- | --- |
| Model traces | ✓ | ✓ (cited in packet) |
| Approval authority | ✗ | ✓ system of record |
| Signed archival artifact | ✗ | ✓ JSON/PDF + verification |

**Partner, don’t replace:** Keep observability for engineering. **AegisAI feeds GRC the evidence pack.**

### Demo (60 seconds)

Signed audit JSON → Verify signature → PDF for workpapers

### Pilot ask

Compliance signs off on **one audit packet format** + internal audit reconstructs a case in &lt; 30 minutes.

---

## Slide 8 — Differentiation

| Category | Gap | AegisAI |
| --- | --- | --- |
| Agent frameworks | Build, don't govern execution | Gateway + registry across frameworks |
| LLM observability | Traces, not approval tokens | SoR for HITL + policy + execution |
| iPaaS / workflow | Deterministic automation | LLM uncertainty + eval gates |
| Cloud AI guardrails | Single-cloud | Multi-cloud, BYOA neutral |
| GRC tools | Documentation | **Live** tool-call enforcement |

**Moat over time:** Policy history + audit corpus + domain risk packs per vertical.

---

## Slide 9 — Business model

| Tier | Price signal | Includes |
| --- | --- | --- |
| **OSS / Developer** | Free | Gateway SDK, simulator, single-tenant registry |
| **Team** | $2.5k–8k/mo | SSO, Postgres, Slack approvals, 3 connectors |
| **Enterprise** | $100k–500k ACV | ABAC, VPC, GRC export, SLA, domain packs |
| **Design partner** | Discounted 90-day pilot | Co-build + case study rights |

**Expansion:** Seats → agents governed → tool calls/month → connectors → compliance modules

---

## Slide 10 — Traction & proof (portfolio → pilot)

**Built today:**

- Layered enterprise architecture (domain / application / infrastructure)
- Governance gateway, agent registry, policy simulator, kill switches
- HITL + execution broker + audit packets (JSON/PDF)
- Golden + red-team eval gates
- Gateway SDK (Python + TypeScript)
- Stripe connector path, Slack approval path, OPA policies

**Next 90 days (design partner):**

- 100% side-effecting tool calls through gateway
- 1 production connector live
- SSO + signed audit packets
- Executive ROI dashboard

---

## Slide 11 — Market size (bottom-up)

**SAM:** Regulated mid-market + enterprise with 10+ agents in pilot  
- ~5,000 target accounts (NA + EU financial services, insurance, health payers)  
- Average $150k ACV governance platform → **~$750M SAM**

**SOM (3 years):** 50 customers × $200k = **$10M ARR** (credible seed outcome)

---

## Slide 12 — Competition

```text
                    High governance depth
                            ▲
                            │  ★ AegisAI
                            │
         GRC tools          │     Custom internal platforms
                            │
    ◄───────────────────────┼───────────────────────►
    Observability           │              Agent builders
                            │
                            │   Cloud guardrails
                            ▼
                    Low cross-framework coverage
```

**Win:** Neutral layer + FinOps wedge + audit packet buyers already need.

---

## Slide 13 — Go-to-market

**Phase 1 — Design partners (0–6 mo)**  
- 3 FinOps/remediation teams  
- Gateway SDK in their LangGraph/OpenAI agents  
- Success metric: % tool calls through gateway  

**Phase 2 — Team product (6–12 mo)**  
- Slack app, Stripe connector, OPA in Git, FinOps dashboard  

**Phase 3 — Enterprise (12–24 mo)**  
- SOC2 Type II, EU AI Act mapping, ServiceNow GRC export  

**Channels:** AI platform community, fintech ops conferences, SI partners (ServiceNow implementers)

---

## Slide 14 — Team (customize)

| Role | Focus |
| --- | --- |
| CEO / Product | FinOps wedge, design partners, compliance narrative |
| CTO / Architect | Gateway, policy engine, broker, security |
| Eng #1 | SDK, integrations (Slack, Stripe) |
| Eng #2 | Data plane, Postgres, evals |

**Advisors:** Enterprise CISO, VP AI platform from target vertical

---

## Slide 15 — The ask

**Raising:** $[X] seed  
**Use of funds:**

- 60% engineering (gateway, identity, connectors)  
- 25% design partner success + security review  
- 15% GTM (content, conferences, first AE)  

**18-month milestones:**

- 5 paying customers  
- $1M ARR run-rate  
- SOC2 in progress  
- Category: *Agent Governance Control Plane*

---

## Slide 16 — Appendix: module map

| Module | Buyer value |
| --- | --- |
| Discover (registry) | End agent sprawl |
| Govern (gateway, policy) | Consistent decisions |
| Execute (broker) | Safe side effects |
| Assure (audit packets) | Pass audits |
| Secure (identity/RBAC) | Least privilege |
| Evaluate (golden + red-team) | Safe releases |
| Enforce (kill switch) | Incident response |
| Integrate (SDK) | BYOA without rip-and-replace |

---

## Slide 17 — Closing

> **Your agents are already in production. Your governance is not.**

**AegisAI** — the control plane enterprises need before the next agent moves money, data, or customer trust.

**[Schedule design partner call]**
