# Low-Cost Deployment Runbook

## Recommendation

Deploy the portfolio version cheaply first:

- **Frontend:** Vercel Hobby from `apps/web`
- **Backend:** Render web service from `services/api/Dockerfile`
- **Database:** local/ephemeral SQLite for the free demo, then Neon Postgres when persistence matters
- **LLM:** `AEGISAI_LLM_PROVIDER=local` for no-key demos, OpenAI later
- **Enterprise edition later:** AWS ECS/App Runner + RDS PostgreSQL + S3 + Secrets Manager

This gives a working public product demo without AWS baseline cost.

## What Works In The Free Demo

The current product can run without paid cloud services:

- Control Plane Action Center
- Agent registry
- Policy simulator
- Governance gateway
- Agent onboarding
- Readiness scoring
- Golden evals
- HITL demo actions
- Audit packet generation
- Local deterministic LLM responses

The free demo uses SQLite in `/tmp`, so data can reset when the provider restarts the service. That is acceptable for a portfolio demo and avoids paying for a database before the product needs persistent tenants.

## Deploy Backend On Render

1. Push this repo to GitHub.
2. In Render, create a new Blueprint or Web Service.
3. Use the repository root as the deploy root.
4. Render can read `render.yaml`, or configure manually:
   - Runtime: Docker
   - Dockerfile: `services/api/Dockerfile`
   - Health check: `/health`
   - Plan: Free for portfolio demo
5. Set environment variables:

```text
AEGISAI_LLM_PROVIDER=local
AEGISAI_CONTROL_PLANE_DB_PATH=/tmp/aegisai-control-plane.sqlite
AEGISAI_VECTOR_DB_PATH=/tmp/aegisai-vector-memory.sqlite
AEGISAI_CORS_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000
LANGSMITH_PROJECT=aegisai-agent-governance-control-plane
```

6. After deployment, verify:

```text
https://your-render-service.onrender.com/health
https://your-render-service.onrender.com/docs
```

Render free services may sleep after inactivity. The first request can be slow; that is a free-tier tradeoff, not an application failure.

## Deploy Frontend On Vercel

1. Import the repo into Vercel.
2. Set the Vercel project root to:

```text
apps/web
```

3. Set environment variable:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com
```

4. Deploy and test:

```text
https://your-vercel-app.vercel.app
```

The control-plane CTAs call the backend URL above. If they show a backend unavailable message, check Render service health and CORS.

## Optional: Google Cloud Run Instead Of Render

Cloud Run is often better than Render when you want scale-to-zero containers without sleeping behavior.

Build and deploy from repo root:

```bash
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/aegisai/aegisai-api
gcloud run deploy aegisai-api \
  --image REGION-docker.pkg.dev/PROJECT/aegisai/aegisai-api \
  --region REGION \
  --allow-unauthenticated \
  --set-env-vars AEGISAI_LLM_PROVIDER=local,AEGISAI_CONTROL_PLANE_DB_PATH=/tmp/aegisai-control-plane.sqlite,AEGISAI_VECTOR_DB_PATH=/tmp/aegisai-vector-memory.sqlite
```

Then set Vercel:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-cloud-run-url
```

## Optional: Neon Postgres Upgrade

Use Neon when you want persistent multi-tenant data and pgvector. This repo currently keeps the portfolio runtime on SQLite to stay free and simple. The production path is to add Postgres persistence adapters for:

- control-plane store
- vector memory
- audit packet retention metadata
- eval results
- agent registry and RBAC

Do this before treating the deployment as a real customer pilot.

## Cost Notes

Expected free or near-free demo:

- Vercel Hobby frontend: free
- Render free backend: free, but sleeps
- SQLite `/tmp`: free, ephemeral
- Local deterministic LLM mode: free

Expected low-cost always-on demo:

- Vercel frontend: free
- Render paid small backend or Cloud Run: usually low monthly cost
- Neon free/paid Postgres: start free, upgrade when needed

Expected enterprise edition:

- AWS ECS/App Runner
- RDS PostgreSQL + pgvector
- S3
- Secrets Manager
- CloudWatch
- Optional Bedrock/OpenAI/Langfuse/LangSmith

Use the AWS runbook when the goal is enterprise credibility or a production pilot, not the cheapest portfolio demo.
