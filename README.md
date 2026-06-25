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

| Layer | Service |
| --- | --- |
| Frontend | Vercel (`apps/web`) |
| Backend | Render (`render.yaml`) |
| Database | Supabase Postgres |

See [docs/PRODUCT.md#deployment-strategy](docs/PRODUCT.md#deployment-strategy).

## Portfolio

Embedded at [venkat-ai-portfolio `/projects/aegisai`](https://github.com/vpeetla-ai/venkat-ai-portfolio) — set `NEXT_PUBLIC_AEGISAI_URL` to your Vercel deployment.
