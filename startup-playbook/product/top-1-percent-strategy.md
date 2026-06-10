# Top 1% Product Strategy — AegisAI Re-Review

**Date:** Principal Architect + Product Owner review  
**Verdict:** You are building the **right category** (agent governance control plane). Stripe was never the product — it was one **example connector** in one **go-to-market wedge**. To reach top 1%, sharpen the **horizontal platform story** and prove **one irreplaceable runtime path** per design partner.

---

## 1. You are right: this is NOT a Stripe product

### What AegisAI actually is

```text
ANY agent (LangGraph, OpenAI, Bedrock, Copilot, custom)
        │
        ▼
Governance Gateway  ──►  policy + risk + eval + HITL
        │
        ▼
Execution Broker    ──►  Connector Registry  ──►  ANY system of record
                              ├── payments (Stripe, Adyen, …)
                              ├── CRM (Salesforce, Dynamics, …)
                              ├── ITSM (ServiceNow, Jira, …)
                              ├── data (Snowflake, Databricks, privacy APIs)
                              ├── comms (Slack, email, SMS)
                              └── MCP / custom HTTP / webhooks
```

**Stripe** = optional adapter for the **FinOps wedge** (refunds).  
**The product** = **govern any tool call, execute through any connector, audit everything.**

If pitch decks or demos over-index on Stripe, buyers think "payments plugin." That caps ACV and wrong-fits non-financial buyers.

### Engineering change (done in this repo)

- Universal **`ConnectorRegistry`** with pluggable `EnterpriseConnector` implementations
- Stripe is **one** connector among Salesforce, ServiceNow, data platform, MCP, custom HTTP
- API: `GET /api/connectors/catalog`

**Rule for all future work:** Never hardcode vendor logic in the broker. Every integration is a connector implementing the same contract.

---

## 2. Product re-review — what makes top 1%

Top 1% B2B products share three traits:

| Trait | AegisAI today | Top 1% target |
| --- | --- | --- |
| **One sentence everyone repeats** | "Agent governance control plane" ✓ | Same — do not dilute |
| **One metric that proves value** | Posture score (weak) | **% side-effecting tool calls through gateway** |
| **One thing only you do** | Gateway + audit SoR (strong) | **Runtime authority** — not traces, not agent building |

### The real-world problem (universal pitch)

> **"Your agents can already call your APIs. Your organization cannot prove it was safe, approved, and auditable."**

That applies to:

- Banks (refunds) — **wedge**
- Insurers (claims adjustments)
- Health payers (prior auth, member data)
- SaaS (account changes, billing credits)
- IT ops (incident remediation, config changes)
- HR (access grants, PII updates)

**Same platform. Different connector pack + policy pack. Different demo story.**

### What NOT to be

- Not "Stripe for AI"
- Not "LangGraph hosting"
- Not "another Langfuse"
- Not "generic RPA"

### What TO be

**The Okta + ServiceNow layer for agent actions:** identity, policy, approval, execution, audit — **framework-neutral**.

---

## 3. How to pitch ANY customer (impact framework)

Use **SPAR** in every meeting:

| Step | Script |
| --- | --- |
| **S — Situation** | "How many agents touch production APIs or customer data today?" |
| **P — Pain** | "When audit asks why an automated action happened, how long to reconstruct?" |
| **A — Alternative** | "Most teams use observability (see traces) or build internal scripts (no governance)." |
| **R — Resolution** | "AegisAI is the control plane: agents propose, we decide, broker executes, audit packet exports." |

### Demo pivot by industry (same product, 90-second story)

| Buyer | Show | Connector in demo |
| --- | --- | --- |
| FinOps | Refund / credit escalation | payments |
| Customer support | Case update + sensitive field change | crm |
| Security / IT | Kill switch + block infra change | itsm / infrastructure |
| Privacy / legal | Block mass delete, escalate export | data platform |
| Platform team | BYOA gateway SDK + registry | mcp / custom |

**Never lead with Stripe unless they're FinOps.**

### The ONE number that closes deals

Track and promise:

> **"Within 90 days, 100% of side-effecting agent tool calls route through AegisAI gateway in your pilot environment."**

Everything else (posture score, evals, FinOps) supports that.

---

## 4. Engineering re-review — honest gaps

| Layer | Status | Top 1% requirement |
| --- | --- | --- |
| **Gateway SDK** | ✓ Python + TS | Sidecar / MCP proxy mode |
| **Connector model** | ✓ Registry (just refactored) | Connector SDK + marketplace UI |
| **Policy** | ✓ Builtin + OPA path | Git-backed policies, same engine sim + runtime |
| **Persistence** | ⚠ SQLite + hybrid Postgres | **Full Postgres-only** (next sprint) |
| **Identity** | ⚠ Mock RBAC | OIDC + agent workload identity (SPIFFE-style) |
| **HITL** | ✓ API + Slack stub | Slack/Teams apps in prod |
| **Audit** | ✓ Hash chain + PDF | KMS-signed packets + retention tiers |

### Postgres — why it matters for selling

Enterprise buyers ask on call #2: *"Where is the system of record?"*  
Hybrid SQLite cache = **credibility hit**. Full Postgres-only is a **P0 for paid pilots**, not optional polish.

**Recommended approach:**

1. Extract `ControlPlaneStore` protocol (interface)
2. `SQLiteControlPlaneStore` — dev/demo
3. `PostgresControlPlaneStore` — production (all reads/writes, RLS by tenant)
4. Single factory via `AEGISAI_DB_BACKEND`

### Connector — why registry matters for selling

Enterprise buyers ask: *"We use Salesforce + ServiceNow + internal APIs — not Stripe."*  
Answer: *"Same gateway. We register your tools, attach policies, route execution to the right connector."*

Show `GET /api/connectors/catalog` in every demo.

---

## 5. Roadmap to "next level" (prioritized)

### Phase A — Credibility (0–8 weeks) — *required to sell*

1. **Full Postgres-only persistence**
2. **Gateway SDK** in customer's staging agent (one framework)
3. **Connector catalog UI** + **HTTP connector registration UI** (`POST /api/connectors/http`, demo mode for live pitches)
4. **Signed audit PDF** demo that compliance actually reviews
5. **One design partner** with written success metric (gateway coverage %)

### Phase B — Expansion (2–6 months)

6. **MCP proxy** — govern MCP tool calls without rewriting agents
7. **Policy packs** by vertical (FinOps, IT ops, privacy) — config, not code forks
8. **Slack/Teams approval apps** (production)
9. **Agent shadow discovery** from Langfuse/OTel traces
10. **SOC2 Type I** narrative + evidence collection

### Phase C — Category leadership (6–18 months)

11. Connector marketplace + SI partnerships
12. Cost budget enforcement in gateway (FinOps++)
13. EU AI Act documentation pack as sales SKU
14. Multi-region VPC / data residency

---

## 6. Positioning one-liner (use everywhere)

**Old (too narrow):**  
*"We govern AI refunds with Stripe integration."*

**New (top 1%):**  
*"AegisAI is the runtime control plane that governs every agent tool call — policy, approval, execution, and audit — across any framework and any enterprise system."*

**Wedge (how you land):**  
*"We start where the pain is highest: actions that move money, data, or customer trust."*

---

## 7. Scorecard — where you are vs top 1%

| Dimension | Now (1–5) | Top 1% bar |
| --- | --- | --- |
| Category clarity | **5** | Agent governance control plane |
| Horizontal platform story | **4** (improving) | Connector registry + BYOA |
| Production credibility | **2** | Postgres + SSO + one live connector |
| Demo → pilot conversion | **3** | Gateway coverage metric |
| Defensibility | **3** | Audit corpus + policy history moat |
| Pitch universality | **4** | SPAR + industry pivots |

**Bottom line:** You do not need more features. You need **one customer story** where an agent **cannot** side-effect without AegisAI — with **their** system (not necessarily Stripe).

---

## 8. Recommended next actions (this week)

1. Update all sales materials: **Stripe = example connector**, not product name
2. In demos, open **connector catalog** before gateway test
3. Pick design partner industry → pick **their** connector (not default Stripe)
4. Sprint **Postgres-only** store (blocks enterprise procurement)
5. Publish case study template: gateway coverage %, MTTR approval, audit sign-off

---

*This document supersedes any Stripe-centric demo scripts. FinOps remains the recommended first wedge; the platform is industry-agnostic by design.*

## 9. Execution update — P0/P1/P2 backlog status

### Completed in current implementation pass

**P0 (buyer clarity + flow)**
- Buyer-first default UI with explicit Buyer/Platform mode toggle.
- API health gate to prevent false-negative demos on stale backend routes.
- Buyer-flow auto-bootstrap (prefetch + guided demo run) once API is healthy.
- Postgres persistence badge and pilot north-star CTA in buyer surface.
- Architect-heavy areas remain available in Platform mode but collapsed by default.

**P1 (proof modules + enterprise packaging)**
- Policy replay diff module and identity graph visualization module shipped.
- Connector registration wizard integrated into control plane.
- Signed audit PDF access integrated into buyer outcomes.
- Gateway SDK snippet and design partner checklist integrated.
- MCP proxy invocation now emits explicit success/failure toast feedback.
- Observability adapter export panel added for Langfuse/LangSmith posture.

**P2 (polish + trust signals)**
- Skeleton loading blocks for buyer narrative surfaces.
- Toast infrastructure and stack styling.
- Additional responsive and accessibility-minded CSS polish.
- Reduced motion handling for shimmer/spinner effects.

### Verification

- Frontend production build validated successfully:
  - `npm -C "apps/web" run build`
- Lint diagnostics checked for edited files with no new errors.
