# AegisAI — Product & Deployment Quick Start

> **Architecture (north star):** [`platform/architecture/ARCHITECTURE.md`](../platform/architecture/ARCHITECTURE.md)  
> **Deployment & all API keys:** [`platform/architecture/DEPLOYMENT-AND-SECRETS.md`](../platform/architecture/DEPLOYMENT-AND-SECRETS.md)

Enterprise **Agent Governance Control Plane**: gateway-first policy enforcement, HITL approvals, signed audit, FinOps, and governed multi-agent orchestration.

---

## Product summary

| Layer | Responsibility |
| --- | --- |
| **Experience** | Next.js control plane — dashboard, monitor, governance, gateway, orchestrators, onboard |
| **Product** | Agent registry, gateway, FinOps, Agent Cloud, dashboard, orchestrators |
| **Application** | LangGraph orchestration, guardrails, RAG/LLM gateway, execution broker |
| **Domain** | Proposals, decisions, risk, audit events |
| **Infrastructure** | SQLite (local) or Postgres (production) |
| **Interfaces** | FastAPI HTTP API |

**Pillars:** Monitor → Govern → Remediate

---

## UI map

| Screen | Content |
| --- | --- |
| **Dashboard** | Navy hero, KPI metrics, pillar shortcuts, tiles, violations preview |
| **Monitor** | Lineage board (agent → identity → app → tool), activity table |
| **Governance** | Control plane pillars, violations table, undo, HITL queue |
| **AI Gateway** | Connection status, coverage, live intercept, SDK snippets |
| **Orchestrators** | Website Build form + content/stock pipelines |
| **Onboard** | Agent registration wizard (shadow → approved) |

Design tokens: `apps/web/app/aegis-ui.css`

---

## Run locally

From **repo root**:

```bash
./scripts/dev.sh
```

Open http://localhost:3000

```bash
make verify
```

---

## Production

- **API:** `https://aegisai-api.onrender.com` — agents call gateway directly
- **FE:** Vercel (`apps/web`)
- **DB:** Supabase Postgres
- **Cron:** Content Mon/Thu 07:00 UTC · Stock weekdays 11:00 UTC (6AM EST)

See [`platform/architecture/ARCHITECTURE.md`](../platform/architecture/ARCHITECTURE.md) for env vars, gateway flow, and orchestrator details.
