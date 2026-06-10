# How to Pitch Any Customer — Same Product, Different Story

> **Use this doc before every demo, investor meeting, or design-partner call.**  
> AegisAI is always the same platform. Only the **story**, **proof workflow**, and **connector** change.

---

## The product (never changes)

**One sentence:**

> AegisAI is the runtime control plane that governs every agent tool call — policy, human approval, execution, and audit — across any AI framework and any enterprise system.

**Three pillars (memorize):**

| Pillar | Buyer hears | You show |
| --- | --- | --- |
| **Govern** | "Nothing side-effects without a decision" | Governance gateway + policy simulator |
| **Execute** | "Approved actions only, through our broker" | Connector catalog + execution token |
| **Assure** | "Audit can reconstruct any case in one export" | PDF/JSON audit packet + hash chain |

**What you are NOT selling:** Stripe, LangGraph hosting, or another chatbot.

---

## The SPAR framework (every meeting)

### S — Situation (2 min)

Ask, don't tell:

1. How many AI agents touch **production APIs** or **customer data** today?
2. Which frameworks — LangGraph, OpenAI, Bedrock, Copilot Studio, internal?
3. What **side-effecting tools** do they call (payments, CRM, tickets, data deletes, config)?

**Listen for:** sprawl, no owner, security blocked a launch.

### P — Pain (3 min)

1. When audit or legal asks *why* an automated action happened, how long to reconstruct?
2. Has anyone been surprised by an agent refund, case change, or data operation?
3. Who approves high-risk actions today — and where does that live (email, Jira, nowhere)?

**Quantify if possible:** hours per incident, $ per mistaken refund, weeks to pass security review.

### A — Alternative (1 min)

> "Most teams use observability — great traces, but traces don't hold approval authority. Others build one-off scripts per agent. Both break at scale and fail audits."

### R — Resolution (demo — 10 min)

> "Agents **propose**. AegisAI **decides**. The broker **executes** through **your** systems. Everything lands in an audit packet."

**Close with one metric:**

> "Our design partners target **100% of side-effecting tool calls through the gateway in 90 days**."

---

## Industry playbooks (same demo flow, different emphasis)

Use this table to pick **opening pain**, **hero workflow**, and **connector to highlight**.

| Industry / buyer | Open with this pain | Hero workflow (90 sec) | Lead connector | Avoid leading with |
| --- | --- | --- | --- | --- |
| **Bank / fintech / payments** | Mistaken refunds, SOX audit | $2.5k refund → escalate → Slack approve → execute | `payments` (Stripe/Adyen) | Generic "AI platform" |
| **Insurance** | Claims adjustment without approval trail | Claim credit + confidential data → HITL | `crm` + `payments` | Stripe-only narrative |
| **Health payer / provider** | PHI access + prior auth automation | Restricted data request → block or privacy officer | `customer_data_platform` | FinOps-only |
| **SaaS / product-led** | Support agents changing billing/accounts | Account credit + case update | `crm` + `custom` | Heavy compliance jargon |
| **Retail / e-commerce** | Return/refund bots at scale | Low-risk auto-approve vs high-risk HITL | `payments` | |
| **Telco** | Billing adjustments + account fixes | Fee reversal policy simulation | `payments` + `crm` | |
| **IT / platform engineering** | Agents changing prod config | Infra change → block / escalate | `servicenow` / `infrastructure` | Refunds |
| **Security / CISO** | Tool sprawl + no kill switch | Kill switch + gateway deny + audit export | Gateway + registry | Agent builder features |
| **Legal / privacy** | GDPR delete / export by agents | Mass delete → **block** + audit packet | `privacy` data connector | Auto-approve stories |
| **VP Enterprise AI** | Agent sprawl, no ROI | Executive posture + registry + FinOps | Registry + gateway SDK | Single use-case only |
| **Compliance / GRC / audit** | Cannot prove AI action chain for examiners | Signed audit JSON → verify → PDF workpapers | Assure (signed packet) | Refunds-only or LLM quality metrics |

### Compliance / GRC buyer (dedicated deck)

When the room is **Compliance, Internal Audit, Risk, Legal, or Privacy** — use the standalone slide deck, not the FinOps wedge:

- **Deck:** [compliance-buyer-slide.md](../pitch-deck/compliance-buyer-slide.md)  
- **Also in main deck:** [PITCH-DECK.md](../pitch-deck/PITCH-DECK.md) — Slide 7b  

**Lead with this quote:**

> *“Observability tools show traces; we provide tamper-evident audit artifacts your GRC team can archive.”*

**Demo order:** governance decision → HITL trail → signed audit JSON → `POST /api/audit-packets/verify` → PDF export.

---

## Demo script (12 minutes — any industry)

| Min | Beat | Screen / API |
| --- | --- | --- |
| 0–1 | SPAR Situation + Pain (questions) | Slide or verbal only |
| 1–2 | One-liner + architecture | "Propose → govern → execute → assure" |
| 2–3 | **Connector catalog + register HTTP** | `GET /api/connectors/catalog` then register their API in the UI (demo mode) |
| 3–5 | Agent registry + executive posture | Control plane / posture API |
| 5–7 | Gateway test (their industry's tool) | `POST /api/gateway/tool-request` |
| 7–9 | HITL + execution token + broker | Reviewer action + execute |
| 9–11 | Audit packet export | PDF/JSON |
| 11–12 | MCP / BYOA (platform teams only) | `POST /api/mcp/tool-call` |
| 12 | Ask + next step | Design partner / pilot scope |

**Rule:** Show **connector catalog** before gateway test in every demo.

---

## Objection → response (cheat sheet)

| They say | You say |
| --- | --- |
| "We already use Langfuse." | "Keep it. Langfuse traces; AegisAI owns approval and execution authority." |
| "We only use Copilot/Bedrock." | "Register those agents. Route tool calls through our gateway — no rip-and-replace." |
| "We don't use Stripe." | "Neither do most customers. Stripe is one connector. Here's your catalog slot for Salesforce/ServiceNow/MCP." |
| "We'll build internally." | "12–18 months for broker + audit + HITL. Pilot in 90 days with our SDK." |
| "AI isn't in production yet." | "Perfect time — governance debt is cheaper before incidents." |
| "Security will never allow auto-approve." | "Risk-based HITL. Auto-approve only low risk; sample near thresholds." |

---

## Discovery → demo mapping

| If they said… | Demo emphasis |
| --- | --- |
| "We have 50+ agents, no inventory" | Registry + readiness scores |
| "Audit failed on an automated change" | Audit packet + policy version |
| "Security froze our agent project" | Gateway + kill switch + identity |
| "Support bot issued wrong refund" | FinOps wedge + HITL |
| "We standardize on MCP tools" | MCP proxy through gateway |
| "Everything is on Salesforce" | CRM connector + gateway |

---

## Email / LinkedIn outreach templates

### Cold (platform lead)

**Subject:** Agent tool calls without governance?

Hi [Name] — teams are shipping LangGraph/OpenAI agents that call production APIs, but audit and security often can't answer *who approved what ran*.

AegisAI is a **governance control plane**: gateway → policy/HITL → execution broker → audit packet. Framework-neutral.

Worth 20 minutes to see if this matches your 2026 agent rollout?

### Warm (post-incident)

**Subject:** Re: [incident] — governance layer for agent actions

Hi [Name] — incidents like [X] usually mean agents can **execute** without a control-plane decision trail.

We help enterprises route **every side-effecting tool call** through policy + approval before execution, with exportable audit evidence.

Happy to walk through a 90-second flow on your stack ([CRM/payments/data]).

---

## Pilot close (design partner)

**Offer:**

- 90-day pilot
- Success metric: **≥80% gateway coverage** on side-effecting tools
- Their connector (not yours) in staging
- Weekly office hours

**Get signed:**

- [ ] Executive sponsor (name)
- [ ] Technical lead (name)
- [ ] Security reviewer engaged week 2
- [ ] One workflow in writing (e.g. "Salesforce case update" not "AI strategy")

---

## Internal checklist (before you pitch)

- [ ] Researched their industry row in the table above
- [ ] Picked hero workflow + connector (not default refund unless FinOps)
- [ ] Backend running; connector catalog loads in UI
- [ ] Audit PDF sample ready
- [ ] SPAR questions written in calendar invite
- [ ] Avoid saying "Stripe product" — say "payments connector"

---

## Related assets

- [Top 1% product strategy](../product/top-1-percent-strategy.md)
- [Sales playbook](sales-playbook.md)
- [ICP & messaging](icp-and-messaging.md)
- [90-day design partner program](../design-partner/90-day-pilot-program.md)
- [Full pitch deck](../pitch-deck/PITCH-DECK.md)
