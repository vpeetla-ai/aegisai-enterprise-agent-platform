# AegisAI Agent Governance Control Plane

Enterprise control plane for governing AI agents: Monitor → Govern → Remediate.

**Documentation:** [platform/architecture/ARCHITECTURE.md](platform/architecture/ARCHITECTURE.md) (north star) · [docs/PRODUCT.md](docs/PRODUCT.md) (quick start)

## Quick start

```bash
# From repo root
./scripts/dev.sh
# or: make dev
```

| Service | URL |
| --- | --- |
| UI | http://localhost:3000 |
| API | http://localhost:8000/docs |

```bash
make verify
```

## Deploy

**Free tier ($0):** Supabase + Render free web service + Vercel + GitHub Actions cron.

| Layer | Service |
| --- | --- |
| Frontend | Vercel (`apps/web`) |
| Backend | Render free web service (Docker) |
| Database | Supabase Postgres |
| Schedulers | GitHub Actions (`.github/workflows/orchestrator-cron.yml`) |

Step-by-step: [platform/architecture/DEPLOYMENT-AND-SECRETS.md](platform/architecture/DEPLOYMENT-AND-SECRETS.md).

Paid Blueprint (`render.yaml`, ~$9/mo): optional for always-on API + native Render Cron.

## Portfolio

Embedded at [venkat-ai-portfolio `/projects/aegisai`](https://github.com/vpeetla-ai/venkat-ai-portfolio) — set `NEXT_PUBLIC_AEGISAI_URL` to your Vercel deployment.
