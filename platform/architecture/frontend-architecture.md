# Frontend Architecture

## Principal Decision

The frontend is structured as a product shell plus feature modules instead of one monolithic component.

- `components/ControlRoom.tsx`: thin client shell that owns local demo state and composes feature views.
- `components/navigation`: top-level navigation and hamburger menu.
- `components/control-plane`: buyer-facing Agent Governance Control Plane modules.
- `components/examples`: reference multi-agent workload examples that prove the platform behavior.
- `lib/api`: typed API payload contracts and the shared API client.
- `lib/controlPlaneData.ts`: static product copy, demo scenarios, and UI reference data.

## Production Rationale

This split keeps the portfolio app understandable to business viewers while making the codebase credible to engineering reviewers:

- API contracts are isolated from JSX.
- AWS/runtime configuration is centralized in `NEXT_PUBLIC_API_BASE_URL`.
- Control-plane product modules are separated from demo/reference workloads.
- The shell can later be replaced by real auth, tenant context, and server-side session loading.
- Feature components can move behind route groups when the app grows.

## AWS Readiness

The Next.js app builds with `output: "standalone"` and ships through a small Node runtime image. Build the container from the repository root:

```bash
docker build -f apps/web/Dockerfile \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.your-domain.com \
  -t aegisai-web .
```

Recommended AWS hosting options:

- **ECS Fargate + ALB:** best for showing enterprise container deployment, VPC routing, WAF, and private API integration.
- **AWS App Runner:** simplest container deployment path for a portfolio environment.
- **Amplify Hosting:** lowest operational burden if the API is separately hosted.

For ECS/App Runner, expose container port `3000` and set:

```text
NODE_ENV=production
PORT=3000
HOSTNAME=0.0.0.0
NEXT_PUBLIC_API_BASE_URL=https://api.your-domain.com
```
