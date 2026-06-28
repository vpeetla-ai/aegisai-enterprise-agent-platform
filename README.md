# AegisAI — Enterprise Agent Governance Control Plane

[![Live UI](https://img.shields.io/badge/demo-Vercel-brightgreen)](https://aegisai-enterprise-agent-platform.vercel.app)
[![API](https://img.shields.io/badge/API-Render-blue)](https://aegisai-api.onrender.com/docs)
[![Stack](https://img.shields.io/badge/stack-free--tier%20ready-purple)]()

**Monitor → Govern → Remediate** — a production control plane for live AI agent fleets, not another agent builder.

> Production agents connect through an **AI Gateway** for tool authorization: identity, RBAC, policy, HITL approval, signed audit, and FinOps — before side effects execute.

[▶ Live control plane](https://aegisai-enterprise-agent-platform.vercel.app) · [📖 North-star architecture](platform/architecture/ARCHITECTURE.md) · [🔗 Ecosystem map](docs/ECOSYSTEM.md) · [🔑 Deploy & secrets](platform/architecture/DEPLOYMENT-AND-SECRETS.md)

---

## Why this exists

Most teams ship agents first and add governance later. That fails when agents can deploy code, call financial APIs, or push to production without oversight.

AegisAI is a **governance control plane**:

| Problem | AegisAI answer |
|---------|----------------|
| Unknown agent behavior | Monitor lineage, FinOps, activity board |
| Ungoverned tool calls | AI Gateway intercept on every tool request |
| Risky deploy actions | OPA policy + **forced HITL** for `deploy_*` tools |
| No audit trail | Signed audit packets + export |
| Shadow agents | Onboarding lifecycle: Shadow → Pilot → Approved |

---

## Implementation status (honest)

| Component | Status |
|-----------|--------|
| AI Gateway (`POST /api/gateway/tool-request`) | ✅ Production |
| Website Build orchestrator + HITL on deploy | ✅ Gateway-integrated |
| Python gateway SDK (`sdk/python/`) | ✅ |
| TypeScript reference client (`apps/web/lib/gateway/`) | ✅ In-repo reference (not npm package) |
| Control plane UI (dashboard, monitor, governance) | ✅ |
| Content + Stock cron orchestrators | ✅ Managed runs (no per-tool gateway intercept yet) |
| Agent registry Postgres persistence | 🟡 In-memory today; gateway enforces lifecycle + allowlists |
| OPA policy engine | 🟡 Optional — default is builtin policy simulator |
| VAP notify gateway | ✅ Wired (`aegis_gateway.py`) |
| ai-content-factory publish | 🟡 Planned |
| Cron orchestrator notify | 🟡 Planned |

**Free tier:** manual Render web service + GitHub Actions cron ([DEPLOYMENT-AND-SECRETS.md](platform/architecture/DEPLOYMENT-AND-SECRETS.md)). **`render.yaml` Blueprint** is optional paid (~$9/mo).

---

## 60-second overview

```text
Agent fleet → AI Gateway (policy + HITL) → Connectors (GitHub, Vercel, Render, Stripe…)
           ↘ Control plane UI (dashboard, monitor, governance, onboard)
```

---

## Architecture

### North-star control plane

```mermaid
flowchart TB
    subgraph Fleet["Production agent fleet"]
        VAP["Venkat AI Platform<br/>3 orchestrators · notify"]
        CONTENT["AI Content Pipeline<br/>Mon/Thu cron"]
        STOCK["Stock Research<br/>Weekdays 6AM EST"]
        WEB["Website Build<br/>On-demand LangGraph"]
    end

    subgraph Gateway["AI Gateway — runtime intercept"]
        GW["POST /api/gateway/tool-request"]
        ID["Identity · RBAC · Kill switch"]
        POL["Policy · OPA · HITL queue"]
        TOK["Execution token"]
    end

    subgraph Pillars["Governance pillars"]
        MON["Monitor<br/>Lineage · FinOps"]
        GOV["Govern<br/>Policy · Approvals"]
        REM["Remediate<br/>Undo · Freeze"]
    end

    subgraph UI["Control plane UI — Next.js / Vercel"]
        DASH["Dashboard"]
        MON_UI["Monitor"]
        GOV_UI["Governance"]
        ONB["Onboard wizard"]
    end

    subgraph Exec["Execution layer"]
        BRK["Execution broker"]
        CONN["Connectors<br/>GitHub · Vercel · Render · Stripe"]
    end

    Fleet -->|"tool calls (VAP notify · Website Build · SDK)"| GW
    GW --> ID --> POL
    POL -->|"allow"| TOK --> BRK --> CONN
    POL -->|"approval_required"| GOV_UI
    GW --> MON
    GW --> GOV
    GW --> REM
    UI --- Gateway
    MON -.-> MON_UI
    GOV -.-> GOV_UI
```

### Layered backend (clean architecture)

```mermaid
flowchart LR
    subgraph Experience
        WEB["apps/web<br/>Next.js"]
    end
    subgraph Interfaces
        API["FastAPI HTTP<br/>auth · enforcement"]
    end
    subgraph Product
        REG["Agent registry"]
        FIN["FinOps"]
        DASH["Dashboard"]
    end
    subgraph Application
        LG["LangGraph workflows"]
        RAG["RAG / LLM gateway"]
        GR["Guardrails · OPA"]
    end
    subgraph Domain
        DOM["Proposals · decisions · audit"]
    end
    subgraph Infra
        DB["Postgres / Supabase"]
        NTF["Slack · Telegram"]
    end
    subgraph Obs
        LF["Langfuse · LangSmith"]
    end

    WEB --> API --> Product --> Application --> Domain --> Infra
    Application -.-> Obs
```

### Website Build orchestrator (LangGraph)

```mermaid
flowchart LR
    REQ["Requirements"] --> UI["UI design"]
    UI --> FE["FE engineer"]
    FE --> BE["BE engineer"]
    BE --> REV["Review + deploy"]
    REV --> HITL{"HITL gate<br/>deploy tools"}
    HITL -->|"approved"| LIVE["GitHub + Vercel + Render"]
```

Deploy tools (`deploy.vercel_release`, `deploy.render_release`, `github.create_pull_request`, `github.push_files`) are **`approval_required`** at runtime.

### VAP notify flow (integrated)

```mermaid
sequenceDiagram
    participant VAP as venkat-ai-platform
    participant GW as AI Gateway
    participant REG as Agent registry
    participant N as Slack/Telegram/WhatsApp
    VAP->>GW: notify.slack / notify.telegram / notify.whatsapp
    GW->>REG: lifecycle + allowlist check
    GW-->>VAP: allow + token / HITL / deny
    VAP->>N: deliver if allowed
```

---

## Key capabilities

| Capability | Details |
|------------|---------|
| **AI Gateway** | Intercept, simulate policy, issue execution tokens |
| **HITL approvals** | In-app queue + Slack approvals |
| **Agent onboarding** | Register → Shadow → Pilot → Approved |
| **Managed orchestrators** | Content pipeline, stock research, website build |
| **Policy engine** | Builtin simulator + optional OPA (`platform/policy/aegisai.rego`) |
| **Observability** | Langfuse + LangSmith traces |
| **SDKs** | Python: `sdk/python/` · TS reference: `apps/web/lib/gateway/client.ts` |

---

## Quick start (local)

```bash
./scripts/dev.sh
# or: make dev
```

| Service | URL |
|---------|-----|
| Control plane UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |

```bash
make verify
```

---

## Deploy (free tier)

| Layer | Service |
|-------|---------|
| Frontend | Vercel (`apps/web`) |
| API | Render (Docker) |
| Database | Supabase Postgres |
| Schedulers | GitHub Actions + Render cron |

Step-by-step: [DEPLOYMENT-AND-SECRETS.md](platform/architecture/DEPLOYMENT-AND-SECRETS.md)

---

## Project structure

```text
aegisai-enterprise-agent-platform/
├── apps/web/              # Next.js control plane UI
├── services/api/          # FastAPI — gateway, product, orchestration
├── orchestrators/         # Phase-2 stubs (canonical code: services/api/.../orchestration/)
├── sdk/python/            # Gateway SDK
├── platform/
│   ├── architecture/      # North-star docs
│   ├── policy/              # OPA Rego rules
│   └── database/            # Postgres migrations
└── adr/                   # Architecture decision records
```

---

## Related projects

See [docs/ECOSYSTEM.md](docs/ECOSYSTEM.md) for how repos connect.

| Project | Role |
|---------|------|
| [venkat-ai-platform](https://github.com/vpeetla-ai/venkat-ai-platform) | Multi-agent OS — notify gateway integrated |
| [ai-content-factory](https://github.com/vpeetla-ai/ai-content-factory) | Content pipeline — application layer with its own HITL gate |
| [enterprise_rag_platform](https://github.com/vpeetla-ai/enterprise_rag_platform) | Governed RAG reference architecture |

Built by [Venkata Peetla](https://github.com/vpeetla-ai) — [venkat-ai.com](https://venkat-ai.com)

If this helps your agent governance work, a ⭐ helps other architects find it.
