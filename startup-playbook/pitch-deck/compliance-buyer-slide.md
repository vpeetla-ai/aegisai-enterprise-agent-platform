# Slide — Compliance / GRC Buyer

> **Use when:** Chief Compliance Officer, Internal Audit, Risk, Legal, Privacy, or GRC lead.  
> **Do not lead with:** agent builders, FinOps refunds, or Stripe — lead with **Assure**.

---

## Headline

**Prove every AI agent action — not just observe it**

*Agent Governance Control Plane · Assure module*

---

## The quote (use on slide — large type)

> **“Observability tools show traces; we provide tamper-evident audit artifacts your GRC team can archive.”**

---

## Their world today

| What they hear | What they need |
| --- | --- |
| “We have Langfuse / LangSmith” | Traces explain model behavior — not **approval authority** |
| “We log prompts in the cloud” | Logs are not a **defensible audit record** for regulators |
| “Legal is reviewing our AI policy” | Policy documents ≠ **proof of what happened in production** |
| “Who approved this automated refund?” | Hours or days to reconstruct — if possible at all |

**Audit finding risk:** AI agents execute or propose actions without a reconstructable chain: policy → human decision → execution → outcome.

---

## What AegisAI provides (Assure pillar)

| Capability | GRC value |
| --- | --- |
| **Hash-chained audit ledger** | Append-only, tamper-evident event chain per tenant |
| **Case audit packet (JSON / PDF)** | One export: proposal, risk, policy version, HITL, execution |
| **Signed audit packets** | Cryptographic signature (HMAC demo / AWS KMS production) |
| **Verification API** | `POST /api/audit-packets/verify` — integrity check before archival |
| **Policy version on every decision** | Reproducible “why” for examiners |
| **Human oversight trail** | Approver identity, role, timestamp, reason codes |

**We do not replace GRC tools (Archer, ServiceNow GRC).** We feed them **evidence packs** from live agent runtime.

---

## Observability vs AegisAI (talk track)

```text
┌─────────────────────┬──────────────────────────┬─────────────────────────────┐
│ Question            │ Observability (traces)   │ AegisAI (control plane)     │
├─────────────────────┼──────────────────────────┼─────────────────────────────┤
│ What did the model  │ Yes — prompts, tokens    │ Yes — agent traces cited    │
│ see and say?        │                          │ in audit packet             │
├─────────────────────┼──────────────────────────┼─────────────────────────────┤
│ Who authorized the  │ No — not source of truth │ Yes — HITL + policy routing │
│ side effect?        │                          │                             │
├─────────────────────┼──────────────────────────┼─────────────────────────────┤
│ Was execution       │ No                       │ Yes — broker + external ref │
│ allowed and run?    │                          │                             │
├─────────────────────┼──────────────────────────┼─────────────────────────────┤
│ Can we archive      │ Trace export (mutable)   │ Signed packet + verify API  │
│ tamper-evident      │                          │                             │
│ evidence?           │                          │                             │
└─────────────────────┴──────────────────────────┴─────────────────────────────┘
```

**Partner message:** Keep Langfuse/LangSmith for engineering. **AegisAI owns regulated workflow state.**

---

## 90-second demo (compliance script)

| Step | Show | Say |
| --- | --- | --- |
| 1 | Agent run completes | “An agent proposed a customer-impacting action.” |
| 2 | Governance decision | “Policy version X routed this to human approval — here are reason codes.” |
| 3 | Reviewer action | “Named approver, role, timestamp — not an anonymous API call.” |
| 4 | Execution result | “Only the broker executed — with external reference.” |
| 5 | **Download signed JSON** | “This is what your GRC team archives.” |
| 6 | **Verify signature** | “Valid — packet unchanged since signing.” |
| 7 | PDF export | “Examiner-ready summary for your audit workpapers.” |

---

## Regulatory alignment (talking points, not legal advice)

| Framework | How AegisAI helps |
| --- | --- |
| **SOC 2** | Change management, logical access, monitoring — execution + approval evidence |
| **EU AI Act** | Record-keeping, human oversight, transparency — audit packet + HITL |
| **Internal audit** | Reconstruct any case ID in one export |

Detailed mapping: [eu-ai-act-soc2-mapping.md](../compliance/eu-ai-act-soc2-mapping.md)

---

## Objection → response

| They say | You say |
| --- | --- |
| “We already export Langfuse traces.” | “Perfect for engineering. Traces don’t sign approval authority or execution outcomes.” |
| “Our GRC tool tracks controls.” | “We produce the **runtime evidence** your GRC tool attaches to control tests.” |
| “AI is not in production.” | “Archive the control now — examiners will ask about agents eventually.” |

---

## Pilot ask (compliance sponsor)

**90-day success criteria:**

- [ ] Compliance reviews **one signed audit packet** and signs off on format  
- [ ] Internal audit reconstructs a sample case in **&lt; 30 minutes** using export only  
- [ ] Policy version + approver identity present on **100%** of high-risk cases in pilot scope  

**Design partner offer:** Co-design audit packet schema for your GRC archive.

---

## Closing line

> **Observability tools show traces; we provide tamper-evident audit artifacts your GRC team can archive.**

**Next step:** Live walkthrough of signed audit packet + verification on a real case.

**Contact:** [email] · [calendar link]
