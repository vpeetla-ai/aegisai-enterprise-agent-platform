# Deployment, Secrets & Agent Blueprint Compliance

> **Parent doc:** [`ARCHITECTURE.md`](ARCHITECTURE.md) (north star)  
> **Quick start:** [`docs/PRODUCT.md`](../../docs/PRODUCT.md)

This document answers three questions:

1. Do our agents follow the **8-step AI agent blueprint**?
2. Should agents live in a **separate repo**?
3. How do we **deploy the full platform** and which **API keys** are required?

---

## Part 1 — Blueprint compliance (8 steps)

Reference blueprint: **Define Purpose → System Prompt → LLM → Tools → Memory → Orchestration → UI → Testing**

### Scorecard by orchestrator

| Blueprint step | AI Content Pipeline | Stock Research | Website Build | Control plane (refund path) |
| --- | --- | --- | --- | --- |
| **1. Purpose & scope** | ✅ `FOCUS_AREAS`, schedule, Slack output defined | ✅ Tickers, 6AM EST briefing, success = markdown delivered | ✅ User requirement form, acceptance criteria in LLM output | ✅ BusinessRequest + workflow types |
| **2. System prompt design** | ⚠️ Implicit in agent classes; not externalized per agent | ⚠️ Same — prompts inline in `AnchorAgent` / briefing template | ✅ Per-node prompts in LangGraph (`requirements`, `ui_design`, `fe`, `be`) | ✅ Agent personas in `multi_agent.py` |
| **3. Choose LLM** | ✅ `LLMGateway` — Gemini default (`TopicArchitectAgent`) | ✅ `LLMGateway` in `AnchorAgent` | ✅ `LLMGateway` on every LangGraph node | ✅ RAG + orchestrator |
| **4. Tools & integrations** | ⚠️ Scout/Researcher use **synthetic data** (comments say bind Perplexity/news APIs) | ⚠️ Collector uses **synthetic** market news | ✅ GitHub, Vercel, Render connectors + **AI Gateway** on deploy | ✅ Stripe, CRM, MCP proxy, gateway |
| **5. Memory systems** | ❌ No episodic/vector memory per run | ❌ No persistent memory | ❌ Stateless per run (no vector DB for build history) | ✅ `SQLiteVectorMemoryStore` + RAG in `EnterpriseAgentGraph` |
| **6. Orchestration** | ✅ Linear multi-agent chain; Render cron trigger | ✅ Linear chain; Render cron | ✅ **LangGraph** `StateGraph` + sequential fallback | ✅ **LangGraph** 3-node graph |
| **7. User interface** | ✅ Slack + Telegram via `NotificationDeliveryService` | ✅ Slack + Telegram | ✅ Control plane **Website Build** form + Orchestrators UI | ✅ Full control plane UI |
| **8. Testing & evals** | ❌ No pipeline-specific golden evals yet | ❌ Same | ❌ No automated eval gate before deploy | ✅ `GoldenEvalService`, `RedTeamEvalService` at platform level |

**Legend:** ✅ implemented · ⚠️ partial / stub · ❌ gap

### Overall verdict

**Partially following the blueprint — strong on orchestration, gateway, UI, and LLM; weak on memory and agent-specific evals.**

What is **ahead** of a typical blueprint:

- **Governance layer** (gateway, HITL, policy, audit) — not in the consumer blueprint but required for enterprise
- **Agent registry + onboard wizard** — production onboarding path
- **Langfuse + LangSmith** tracing on website runs

What to close next (priority order):

1. **Externalize system prompts** — `platform/agents/{content,stock,website}/*.yaml` per agent
2. **Replace synthetic Scout/Collector** with real news APIs (see secrets below)
3. **Per-pipeline memory** — store last N runs in Postgres + optional vector recall
4. **Pipeline eval gates** — run golden eval before Publisher / before deploy
5. **MCP servers** — Figma for UI agent, GitHub MCP for review agent (gateway already supports MCP posture)

---

## Part 2 — Separate repo for agents?

### Recommendation: **Yes — separate deployable agent repos; keep governance in this repo**

| Approach | Pros | Cons | When to use |
| --- | --- | --- | --- |
| **Monorepo (current)** | Fast iteration, shared `LLMGateway`, one Render deploy | Agents coupled to control plane release; harder to scale teams | Now — portfolio / MVP |
| **Multi-repo (target)** | Independent agent CI/CD; clear gateway contract; matches “onboard any agent” story | More repos to manage; need SDK versioning | Production + multiple agent teams |

### Target layout

```
aegisai-enterprise-agent-platform/     ← THIS REPO (control plane only)
  apps/web, services/api, platform/, sdk/

aegisai-agent-content-pipeline/          ← separate repo (optional phase 2)
  calls POST https://aegisai-api.onrender.com/api/gateway/tool-request
  uses sdk/python/aegisai_gateway

aegisai-agent-stock-research/
aegisai-agent-website-build/
```

**Rule:** Agents never bypass the gateway. They call Render API directly with `agent_id` registered in the control plane.

**Migration path:**

1. **Now** — orchestrators live in `services/api/.../orchestration/` (monorepo)
2. **Phase 2** — extract to `orchestrators/` worker services; cron hits agent service URL, agent service calls gateway on Render
3. **Phase 3** — each agent team owns a repo; control plane only governs

You do **not** need separate repos today to deploy. Separate repos help when different teams own different agents or release cadences diverge.

---

## Part 3 — Full deployment strategy

### Topology

```
┌──────────────────────────────────────────────────────────────────────────┐
│ VERCEL                          RENDER                                    │
│ ┌─────────────────────┐         ┌─────────────────────────────────────┐  │
│ │ apps/web            │ rewrite │ aegisai-api (web service, Docker)   │  │
│ │ Control plane UI    │ ──────► │ FastAPI :8000                       │  │
│ └─────────────────────┘  /api/* └──────────┬──────────────────────────┘  │
│                                             │                               │
│ ┌─────────────────────┐         ┌───────────▼──────────┐                   │
│ │ venkat-ai-portfolio │ iframe  │ GitHub Actions cron  │                   │
│ │ /projects/aegisai   │         │ (free tier)          │                   │
│ └─────────────────────┘         └───────────┬──────────┘                   │
│                                             └──────► POST /api/orchestrators/*/run
│                         Render Cron (paid Blueprint only) ──► same endpoints
└──────────────────────────────────────────────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
            │  Supabase    │          │  Slack /     │          │  GitHub /    │
            │  Postgres    │          │  Telegram    │          │  Vercel /    │
            │  DATABASE_URL│          │  webhooks    │          │  Render APIs │
            └──────────────┘          └──────────────┘          └──────────────┘
```

### Recommended free stack ($0/month)

| Layer | Service | Cost |
| --- | --- | --- |
| Database | **Supabase** Postgres | Free |
| API | **Render** web service (`plan: free`) | Free |
| UI | **Vercel** (`apps/web`) | Free |
| LLM | **Gemini** (Google AI Studio) | Free tier |
| Schedulers | **GitHub Actions** (`.github/workflows/orchestrator-cron.yml`) | Free |

> **Do not use Blueprint on free tier.** `render.yaml` uses `plan: starter` (~$7/mo) plus two Render Cron jobs (~$1/mo each), which triggers Render’s payment prompt.

### Deploy order — free tier (recommended)

| Step | Service | Action |
| --- | --- | --- |
| 1 | **Supabase** | Create project → run `platform/database/postgres-migration.sql` → copy `DATABASE_URL` |
| 2 | **Render** | **New → Web Service** (not Blueprint) → Docker, **Free** instance — see steps below |
| 3 | **Vercel** | Import repo, root `apps/web` → deploy → copy URL |
| 4 | **Render CORS** | Set `AEGISAI_CORS_ORIGINS` to your Vercel URL → redeploy API |
| 5 | **Gemini** | API key from Google AI Studio → set `GEMINI_API_KEY` on Render |
| 6 | **GitHub Actions** | Repo **Settings → Secrets → Actions** → add `AEGISAI_API_BASE_URL` |
| 7 | **Slack** (optional) | Incoming webhooks for content + stock + HITL |
| 8 | **Smoke test** | `GET /health` → UI → manual orchestrator run → check Actions schedule |

#### Step 2 detail — Render free web service (skip Blueprint)

1. Render Dashboard → **New → Web Service** (not Blueprint).
2. Connect repo `aegisai-enterprise-agent-platform`.
3. Configure:

| Setting | Value |
| --- | --- |
| Name | `aegisai-api` |
| Runtime | Docker |
| Dockerfile path | `services/api/Dockerfile` |
| Docker context | `.` (repo root) |
| **Instance type** | **Free** |
| Health check path | `/health` |

4. Set Tier A env vars (Part 5) — minimum: `DATABASE_URL`, `AEGISAI_DB_BACKEND=postgres`, `GEMINI_API_KEY`, `AEGISAI_LLM_PROVIDER=gemini`, `AEGISAI_EXECUTION_TOKEN_SECRET`, `AEGISAI_AUDIT_SIGNING_KEY`.

> **Supabase `DATABASE_URL` tip:** Use **Connect → Session pooler** (port `5432`) for Render — it is a long-running web service, not serverless. **Do not type the hostname by hand.** Copy the full URI from Supabase; new projects may use `aws-1-…` or `aws-2-…`, not `aws-0-…`. If passwords contain `#`, `@`, or `%`, the app auto-encodes them.

**If you see `tenant/user postgres.<project-ref> not found`:** the pooler **hostname is wrong** (wrong cluster or region), not your password. Open Supabase → **Connect** → copy **Session pooler** or **Transaction pooler** host exactly (e.g. `aws-1-us-west-2.pooler.supabase.com`, not guessed `aws-0-uswest-2`).
5. Deploy. Note your URL, e.g. `https://aegisai-api.onrender.com`.

**Free tier limits:** spins down after 15 min idle (~30–60s cold start); 750 instance hours/month.

#### Step 6 detail — GitHub Actions cron (replaces Render Cron)

Workflow: `.github/workflows/orchestrator-cron.yml`

1. GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**
2. Name: `AEGISAI_API_BASE_URL` — value: your Render API URL (no trailing slash), e.g. `https://aegisai-api.onrender.com`
3. Schedules (UTC):

| Pipeline | Cron | Meaning |
| --- | --- | --- |
| AI content | `0 7 * * 1,4` | Mon & Thu 07:00 UTC |
| Stock research | `0 11 * * 1-5` | Weekdays 11:00 UTC (~6 AM EST) |

4. **Manual test:** Actions → **Orchestrator cron** → **Run workflow** → choose pipeline.

Update `apps/web/vercel.json` rewrites if your Render URL differs from `https://aegisai-api.onrender.com`.

### Deploy order — paid Blueprint (optional)

| Step | Service | Action |
| --- | --- | --- |
| 1 | **Supabase** | Same as free tier |
| 2 | **Render** | Blueprint from `render.yaml` → payment method required (~$9/mo) |
| 3–9 | … | Same as before |

### Render services (`render.yaml` — paid Blueprint)

| Service | Type | Schedule / URL |
| --- | --- | --- |
| `aegisai-api` | Web (`starter`) | `https://aegisai-api.onrender.com` |
| `aegisai-content-pipeline` | Cron | `0 7 * * 1,4` (Mon & Thu 07:00 UTC) |
| `aegisai-stock-research` | Cron | `0 11 * * 1-5` (weekdays ≈ 6AM EST) |

Cron jobs call the **web service** — API must be up when cron fires. On free tier, use GitHub Actions instead.

### Vercel (`apps/web`)

- Root directory: `apps/web`
- Rewrites: `/api/*` and `/health` → Render API (see `vercel.json`)
- No LLM keys on Vercel — all agent logic runs on Render

### Website Build (on-demand)

- Triggered only from UI: `POST /api/orchestrators/website-build/run`
- Not on cron
- Deploy steps pause at **`pending_hitl`** until reviewer approves in Governance

---

## Part 4 — LLM configuration & API keys

### Free / low-cost LLMs configured today

| Provider | Env vars | Model default | Cost | Where to get key |
| --- | --- | --- | --- | --- |
| **Google Gemini** (recommended now) | `AEGISAI_LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, optional `AEGISAI_LLM_MODEL=gemini-2.0-flash` | `gemini-2.0-flash` | **Free tier** on Google AI Studio (rate limits apply) | [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| **OpenAI** (swap later) | `AEGISAI_LLM_PROVIDER=openai`, `OPENAI_API_KEY`, `AEGISAI_LLM_MODEL=gpt-4.1-mini` | `gpt-4.1-mini` | Paid (small $ for dev) | [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **Local / offline** | `AEGISAI_LLM_PROVIDER=local` | deterministic fallback | Free | No key — for CI and offline dev |

**Production default in `render.yaml`:** `AEGISAI_LLM_PROVIDER=gemini` + `GEMINI_API_KEY`.

Code path: `services/api/src/aegisai/application/knowledge/llm_gateway.py`

### Not yet wired (future free options)

| Provider | Notes |
| --- | --- |
| **Groq** | Fast free tier — needs adapter in `LLMGateway` |
| **Together / Mistral** | Add as provider enum when needed |
| **Ollama** | Local only — good for dev, not Render |

---

## Part 5 — Complete secrets matrix

### Tier A — Required for production control plane

| Variable | Required | Where to get | Set on |
| --- | --- | --- | --- |
| `DATABASE_URL` | **Yes** | Supabase → Project Settings → Database → connection string (pooler) | Render |
| `AEGISAI_DB_BACKEND` | **Yes** | `postgres` | Render |
| `AEGISAI_CORS_ORIGINS` | **Yes** | Your Vercel URL, e.g. `https://your-app.vercel.app` | Render |
| `GEMINI_API_KEY` | **Yes** (if using Gemini) | Google AI Studio | Render |
| `AEGISAI_LLM_PROVIDER` | **Yes** | `gemini` | Render |
| `AEGISAI_EXECUTION_TOKEN_SECRET` | **Yes** (pilot+) | Generate random 32+ char string | Render |
| `AEGISAI_AUDIT_SIGNING_KEY` | **Yes** | Generate random string | Render |

### Tier B — Orchestrator notifications

| Variable | Required | Where to get | Set on |
| --- | --- | --- | --- |
| `SLACK_CONTENT_WEBHOOK_URL` | Recommended | Slack → App → Incoming Webhooks → #content channel | Render |
| `SLACK_STOCK_WEBHOOK_URL` | Recommended | Same, #stock or same channel | Render |
| `SLACK_APPROVAL_WEBHOOK_URL` | Recommended | HITL / approvals channel | Render |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram @BotFather → `/newbot` | Render |
| `TELEGRAM_CHAT_ID` | Optional | Message @userinfobot or getUpdates API | Render |

### Tier C — Website Build deploy (real tools)

| Variable | Required | Where to get | Set on |
| --- | --- | --- | --- |
| `GITHUB_TOKEN` | For real commits | GitHub → Settings → Developer settings → PAT (repo scope) | Render |
| `GITHUB_REPO_OWNER` | Yes with GitHub | Your GitHub username or org | Render |
| `GITHUB_REPO_NAME` | Yes with GitHub | Target repo name | Render |
| `GITHUB_BASE_BRANCH` | Optional | Default `main` | Render |
| `VERCEL_TOKEN` | For FE deploy | Vercel → Account → Tokens | Render |
| `VERCEL_PROJECT_ID` | For FE deploy | Vercel project → Settings → General | Render |
| `RENDER_API_KEY` | For BE deploy | Render → Account → API Keys | Render |
| `RENDER_SERVICE_ID` | For BE deploy | Render service → Connect → service id in URL | Render |

Without Tier C, website pipeline still runs but connectors return dry-run messages.

### Tier D — Observability (free tiers available)

| Variable | Required | Where to get | Set on |
| --- | --- | --- | --- |
| `LANGFUSE_PUBLIC_KEY` | Optional | [https://cloud.langfuse.com](https://cloud.langfuse.com) → Project → API Keys | Render |
| `LANGFUSE_SECRET_KEY` | Optional | Same | Render |
| `LANGFUSE_HOST` | Optional | Default cloud URL or self-host | Render |
| `LANGSMITH_API_KEY` | Optional | [https://smith.langchain.com](https://smith.langchain.com) → Settings → API Key | Render |
| `LANGSMITH_PROJECT` | Optional | e.g. `aegisai-agent-governance-control-plane` | Render |

### Tier E — Vercel frontend only

| Variable | Required | Where to get | Set on |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Optional | Leave empty for same-origin proxy | Vercel |
| (rewrites) | **Yes** | `vercel.json` points to Render API URL | Vercel project |

### Tier F — Production hardening (when ready)

| Variable | Purpose |
| --- | --- |
| `AEGISAI_PILOT_MODE=true` | Stricter enforcement |
| `AEGISAI_REQUIRE_EXECUTION_TOKEN=true` | Block broker without token |
| `AEGISAI_ENFORCE_AUTH=true` | Require auth on protected routes |
| `AEGISAI_AUTH_MODE=oidc` | Okta / Azure AD |
| `AEGISAI_OIDC_ISSUER`, `AEGISAI_OIDC_JWKS_URI`, `AEGISAI_OIDC_AUDIENCE` | IdP config |
| `OPENAI_API_KEY` | When switching from Gemini |

### Tier G — Not required for current agents

| Variable | Notes |
| --- | --- |
| `STRIPE_SECRET_KEY` | Refund demo path only |
| `SLACK_BOT_TOKEN` | Interactive HITL (stub); webhooks enough for now |

---

## Part 6 — Checklist before go-live

### Control plane

- [ ] Render `aegisai-api` healthy at `/health`
- [ ] Vercel UI loads; API banner green
- [ ] `DATABASE_URL` connected (health shows `postgres`)
- [ ] CORS allows Vercel origin

### Each agent

- [ ] Registered in **Onboard** wizard or seed registry
- [ ] `GEMINI_API_KEY` set; Topic Architect / website nodes return real LLM text
- [ ] Content cron: Monday/Thursday — check Slack/Telegram
- [ ] Stock cron: weekday 6AM EST — check Slack/Telegram
- [ ] Website: submit requirement → status `pending_hitl` → approve deploy in Governance

### Gateway

- [ ] `POST /api/gateway/tool-request` returns decision from Render URL
- [ ] Deploy tools return `approval_required`
- [ ] Langfuse/LangSmith show traces (if keys set)

---

## Part 7 — Local dev vs production

| Concern | Local (`./scripts/dev.sh`) | Production |
| --- | --- | --- |
| DB | SQLite (`AEGISAI_DB_BACKEND=sqlite`) | Postgres (`DATABASE_URL`) |
| LLM | `local` or `gemini` with key in `.env` | `gemini` on Render |
| Agents | Same code paths | Cron + UI triggers |
| Gateway URL | `http://localhost:8000` | `https://aegisai-api.onrender.com` |
| Secrets | Root `.env` (copy from `.env.example`) | Render dashboard + Vercel env |

---

*Last updated: 2026-06-24*
