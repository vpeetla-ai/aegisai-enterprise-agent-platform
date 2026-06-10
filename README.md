# AegisAI Agent Governance Control Plane

Enterprise-grade AI production platform for governing agent sprawl, identity sprawl, tool sprawl, audit gaps, unmanaged cost, and safe multi-agent execution.

## Product Thesis

A production AI product is not just an LLM prompt or a dashboard. It is an end-to-end platform spanning user experience, guardrails, orchestration, data/knowledge, infrastructure, telemetry, feedback loops, and human accountability.

**AegisAI** implements that pattern as a portfolio-grade enterprise solution:

- **User Layer:** customers, employees, reviewers, auditors, and business systems.
- **Experience Layer:** buyer-facing governance dashboard, business-user examples, agent test console, HITL review queue, and admin views.
- **Guardrails / Policy Layer:** policy-as-code, risk scoring, evaluation gates, RBAC/ABAC, safety checks.
- **AI Orchestration Layer:** LangGraph-compatible workflow, planner, evidence, domain, compliance, and communication agents.
- **Data / Knowledge Layer:** transactional control-plane DB, vector memory, hybrid retrieval, evidence references.
- **Infrastructure Layer:** FastAPI backend, Next.js frontend, AWS-ready deployment model.
- **Telemetry Layer:** metrics, traces, audit events, eval outputs, reviewer SLA.
- **Feedback Loop:** human feedback, evaluation results, prompt/policy/retrieval improvement.
- **HITL:** approve, reject, request info, escalate.
- **Hybrid Retrieval:** vector memory plus metadata/policy filtering, with a production path to pgvector/OpenSearch.

## Market Problems Solved

- **Agent sprawl:** Agent Registry captures owner, domain, model, autonomy, risk, tools, cost, and incidents.
- **Identity sprawl:** Identity + RBAC controls reviewer authority and tool execution identity.
- **Tool sprawl:** Governed tool registry and execution broker prevent direct side-effecting tool calls.
- **Audit gaps:** Audit packet export produces JSON/PDF evidence for case review.
- **Unmanaged cost:** Registry cost posture and golden eval gates expose cost-quality tradeoffs before promotion.

## Repository Structure

```text
aegisai-agent-governance-control-plane/
  apps/
    web/                         # Next.js enterprise experience + control-plane UI
      components/
        control-plane/           # Buyer-facing governance product modules
        examples/                # Reference multi-agent workload examples
        navigation/              # Shell navigation and menu
      lib/api/                   # Typed frontend API contracts and client
  services/
    api/
      src/aegisai/
        domain/                  # Stable business contracts: proposals, decisions, traces, risk
        application/
          orchestration/         # LangGraph workflow, multi-agent supervisor, shared context
          guardrails/            # Risk, evaluation, policy, decision engine
          knowledge/             # LLM gateway, RAG pipeline, vector memory reference store
          execution/             # Approval-gated action execution broker
        infrastructure/
          persistence/           # Control-plane state store and audit ledger adapters
        interfaces/
          http/                  # FastAPI inbound API adapter
        observability/           # Langfuse/LangSmith exporter adapters and neutral trace service
        product/                 # Product-owner review artifacts and roadmap posture
      tests/                     # Backend and API tests
      requirements.txt
  platform/
    architecture/                # Enterprise AI architecture and product blueprints
    database/                    # Transactional DB and vector-memory schema
    deployment/                  # AWS deployment and cost strategy
    operations/                  # Security, production readiness, SLOs, runbooks
    product/                     # Startup product definition, ICP, roadmap, and market thesis
  adr/                           # Architecture decision records
  pyproject.toml
  requirements.txt
```

## Product First

The app now opens with the **Agent Governance Control Plane**: the buyer-facing product surface for executive posture, agent onboarding, runtime gateway enforcement, production readiness, integrations, observability, HITL, audit, and incident response.

The hamburger menu exposes **Reference Multi-Agent Examples**. Those scenarios prove the platform works by showing how governed agents handle refunds, low-risk credits, restricted data deletion, hybrid retrieval, eval gates, approvals, and execution audit. The control plane is the product enterprises buy; the multi-agent workflows are the proof workload.

## Core Runtime

The backend includes:

- `aegisai.domain`: stable contracts for proposals, governance decisions, risk, eval gates, traces, and audit events.
- `aegisai.application.orchestration`: LangGraph-compatible workflow, supervisor, specialized agents, and shared case context.
- `aegisai.application.guardrails`: risk scoring, evaluation gates, policy routing, and decision engine.
- `aegisai.application.knowledge`: deterministic LLM gateway, RAG pipeline, and vector-memory reference adapter.
- `aegisai.application.tools`: governed tool registry for RAG search and side-effecting enterprise actions.
- `aegisai.application.execution`: approved action broker with connector routing, idempotency, rollback metadata, and execution audit.
- `aegisai.product`: startup product services for agent inventory, policy simulation, onboarding, readiness scoring, governance gateway, integration posture, and executive risk posture.
- `aegisai.infrastructure.persistence`: transactional control-plane DB and hash-chained audit ledger.
- `aegisai.interfaces.http`: FastAPI API adapter for agents, RAG, reviewer actions, execution, metrics, and observability status.
- `aegisai.observability`: vendor-neutral trace export boundary with optional Langfuse and LangSmith adapters.

`aegisai.api` remains as the stable FastAPI entrypoint; implementation code lives in the layered packages above.

## Run Backend

```bash
UV_CACHE_DIR=.uv-cache uv venv
UV_CACHE_DIR=.uv-cache uv pip install -r requirements.txt
UV_CACHE_DIR=.uv-cache uv run --extra dev uvicorn aegisai.api:app --app-dir services/api/src --host 127.0.0.1 --port 8000
```

Open:

```text
http://localhost:8000/docs
```

The frontend control-plane CTAs call this local backend. AWS deployment and OpenAI keys are not required for the portfolio demo; the default local LLM mode returns deterministic responses so agent, RAG, policy, HITL, gateway, and audit flows can be tested offline.

Useful API flow:

```text
POST /api/agents/run
POST /api/control-plane/reviewer-action
POST /api/execution/execute
GET  /api/agent-registry
GET  /api/platform/posture
POST /api/platform/onboard-agent
GET  /api/platform/readiness/{agent_id}
POST /api/gateway/tool-request
GET  /api/platform/integrations
POST /api/policy/simulate
GET  /api/audit-packets/{tenant_id}/{case_id}.json
GET  /api/audit-packets/{tenant_id}/{case_id}.pdf
GET  /api/identity/posture
POST /api/kill-switches
POST /api/evaluations/golden/run
GET  /api/control-plane/metrics
```

## Use OpenAI LLM Mode

The repo defaults to `AEGISAI_LLM_PROVIDER=local` so demos and tests run without secrets. To use a real OpenAI model in the RAG/agent path:

```bash
export AEGISAI_LLM_PROVIDER=openai
export AEGISAI_LLM_MODEL=gpt-4.1-mini
export OPENAI_API_KEY=your_key_here
PYTHONPATH=services/api/src .venv/bin/python -m uvicorn aegisai.api:app --reload --host 0.0.0.0 --port 8000
```

The API response includes `llm.provider`, `llm.model`, `llm.content`, and `tools_available`. Agents do not call side-effecting tools directly; they propose actions, and the control plane plus execution broker decide whether tools can run.

For bring-your-own-agent scenarios, route tool requests through:

```text
POST /api/gateway/tool-request
```

That endpoint simulates the runtime pattern enterprises need: agent identity authorization, incident kill-switch checks, policy simulation, evaluation gates, approval routing, execution-token issuance, and audit evidence before side effects happen.

## Run Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Run Tests

Minimal backend tests:

```bash
PYTHONPATH=services/api/src python3 -m unittest discover -s services/api/tests
```

Full API test suite after installing dependencies:

```bash
PYTHONPATH=services/api/src .venv/bin/python -m unittest discover -s services/api/tests
```

Optional Langfuse/LangSmith exporters:

```bash
UV_CACHE_DIR=.uv-cache uv pip install -r services/api/requirements-observability.txt
```

Frontend build:

```bash
cd apps/web
npm run build
npm audit --json
```

One-command production verification (lint + build + backend tests):

```bash
./scripts/verify.sh
# or
make verify
```

## Startup Playbook & Pitch Deck

Commercial materials for positioning, pitching, marketing, and selling AegisAI:

- [Startup Playbook (index)](startup-playbook/README.md)
- [Full Pitch Deck](startup-playbook/pitch-deck/PITCH-DECK.md)
- [Sales Playbook](startup-playbook/gtm/sales-playbook.md)
- [Marketing Playbook](startup-playbook/gtm/marketing-playbook.md)
- [90-Day Design Partner Program](startup-playbook/design-partner/90-day-pilot-program.md)
- [Pitch Any Customer Playbook](startup-playbook/gtm/pitch-any-customer-playbook.md)

## Top 10 Startup Actions (implemented)

| # | Capability | How to use |
| --- | --- | --- |
| 1 | Gateway SDK | Python: `sdk/python/` · TypeScript: `apps/web/lib/gateway/client.ts` |
| 2 | Postgres (full SoR) | `AEGISAI_DB_BACKEND=postgres` + `AEGISAI_DATABASE_URL` — no SQLite hybrid |
| 2b | Connector catalog UI | Control plane → Enterprise connector catalog panel |
| 2d | HTTP connector registration | Control plane → Register custom HTTP connector · `POST /api/connectors/http` |
| 2c | MCP proxy | `POST /api/mcp/tool-call` · MCP panel in UI |
| 3 | OIDC / auth | `AEGISAI_AUTH_MODE=oidc` + `Authorization: Bearer` + `X-AegisAI-Principal` |
| 4 | OPA policies | `AEGISAI_POLICY_ENGINE=opa` + `platform/policy/aegisai.rego` |
| 5 | Stripe refunds | `STRIPE_SECRET_KEY` for live mode; mock mode when unset |
| 6 | Slack HITL | `SLACK_APPROVAL_WEBHOOK_URL` + `POST /api/hitl/slack/approval-task` |
| 7 | Compliance map | `startup-playbook/compliance/eu-ai-act-soc2-mapping.md` |
| 8 | FinOps dashboard | `GET /api/finops/dashboard` · UI: FinOps panel on control plane |
| 9 | Red-team evals | `POST /api/evaluations/red-team/run` |
| 10 | Design partners | `startup-playbook/design-partner/90-day-pilot-program.md` |

Gateway tool calls return an `execution_token` when `gateway_decision` is `allow`. Pass it as header `X-AegisAI-Execution-Token` to `POST /api/execution/execute`.

## Enterprise assurance (latest)

| Feature | Endpoints / config |
| --- | --- |
| **Signed audit packets** | `GET .../audit-packets/{tenant}/{case}.signed.json`, `POST /api/audit-packets/verify` |
| **SSO on mutating APIs** | `AEGISAI_AUTH_MODE=oidc`, `AEGISAI_ENFORCE_AUTH=true`, `GET /api/auth/posture` |

See [signed-audit-and-sso.md](platform/operations/signed-audit-and-sso.md).

## Key Docs

- [Startup Product Definition](platform/product/startup-product-definition.md)
- [Enterprise AI Production Architecture](platform/architecture/enterprise-ai-production-architecture.md)
- [End-to-End Product Blueprint](platform/architecture/e2e-product-blueprint.md)
- [LLM + LangGraph + RAG + FastAPI](platform/architecture/llm-langgraph-rag-api.md)
- [Frontend Architecture](platform/architecture/frontend-architecture.md)
- [Low-Cost Deployment Runbook](platform/deployment/low-cost-deployment-runbook.md)
- [AWS Deployment Strategy](platform/deployment/aws-deployment-strategy.md)
- [AWS E2E Deployment Runbook](platform/deployment/aws-e2e-deployment-runbook.md)
- [Database Schema](platform/database/db-schema.sql)
- [Production Readiness Review](platform/operations/production-readiness-review.md)
- [Observability Integrations](platform/operations/observability-integrations.md)
- [Principal Product Owner Review](platform/architecture/principal-product-owner-review.md)

## AWS Recommendation

## Low-Cost Deployment Recommendation

For the first public portfolio deployment, use the cheapest working architecture:

- **Frontend:** Vercel Hobby from `apps/web`
- **Backend:** Render Docker web service using `render.yaml`
- **Database:** SQLite `/tmp` for free demo state, Neon Postgres later when persistence matters
- **LLM:** `AEGISAI_LLM_PROVIDER=local` by default, OpenAI key optional

This runs the control-plane CTAs without AWS or OpenAI spend. See [Low-Cost Deployment Runbook](platform/deployment/low-cost-deployment-runbook.md).

## AWS Enterprise Edition Recommendation

For an enterprise pilot:

- **Frontend:** ECS Fargate/App Runner container using Next.js standalone output.
- **Backend:** App Runner for simple deployment, ECS Fargate for stronger enterprise controls.
- **LLM:** Amazon Bedrock on-demand.
- **Transactional + Vector DB:** RDS PostgreSQL with pgvector.
- **Evidence Store:** S3.
- **Async Events:** SQS + EventBridge.
- **Secrets:** Secrets Manager + KMS.
- **Telemetry:** CloudWatch + OpenTelemetry/X-Ray.
- **Execution:** EventBridge + SQS + ECS worker or Lambda for production connector calls.

Use OpenSearch Serverless only when search scale justifies its minimum capacity cost. For this product stage, RDS PostgreSQL + pgvector is the cleaner and lower-cost default.
