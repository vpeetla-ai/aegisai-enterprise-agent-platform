# ADR 0003: Auth Gate on Cron Orchestrator Endpoints, Corrected Registry Persistence Claim

## Status

Accepted

## In one breath (panel)

I'd put the same auth dependency on cron orchestrator runs that every other mutating route already has — leaving the LLM/Vercel triggers uniquely open was an accident, not a product choice.

## Context

A security audit of the gateway request path found `POST /api/orchestrators/ai-content/run`, `…/stock-research/run`, and `…/website-build/run` had no `AuthRequired` at all. Every other mutating route in the same file already required it. Those three fire real LLM calls (and website-build hits Vercel). Cron (`render.yaml`, GitHub Actions) and the free-tier frontend never sent credentials — so nothing in the current deploy *depended* on them being open. Still: unique exemption is how demos become prod holes.

Separately, the README understated registry persistence ("in-memory today") when `PostgresAgentRegistryStore` already exists behind `AEGISAI_DB_BACKEND=postgres`. Honesty cuts both ways — don't oversell, don't undersell.

OPA remains optional and **fails open** (advisory) when unavailable. Worth saying out loud.

## Decision

1. Add `auth: AuthRequired` to the three orchestrator run routes — same pattern as the rest of `api.py`. Enforcement only rejects when `AEGISAI_ENFORCE_AUTH=true` (default `false`), so this is a no-op until an operator opts in.
2. Update cron callers to send `X-AegisAI-Principal: render-cron` / `github-actions-cron` so flipping enforcement later doesn't silently break schedules.
3. Correct the README registry row to ✅ with the real mechanism, and label OPA fail-open explicitly.

**Demo vs Strict:** Demo stays open by default (`ENFORCE_AUTH=false`). Strict is operator opt-in — not claimed as the live public demo posture.

## Consequences

### Positive

- Orchestrator endpoints are no longer uniquely exempt
- Cron keeps working today; won't break silently when enforcement turns on
- README matches reality on Postgres registry

### Negative

- Auth still defaults off — this ADR closes the inconsistency, not the bigger "public internet should enforce by default" product call
- FinOps `monthly_cost_usd` was still seed data at the time (fixed for Website Build in ADR-0004; other orchestrators remain partial)
- OPA violations stay advisory → HITL, not hard fail-closed

### Follow-ups

- ADR-0004 (done): real FinOps metering — [ADR-0004](./0004-real-finops-metering-website-build.md)
- Decide whether `AEGISAI_ENFORCE_AUTH=true` should be default for public deploys (needs OIDC for every client, including the demo UI)
- OPA fail-closed for critical actions — future ADR, not assumed here

## References

- `services/api/src/aegisai/interfaces/http/api.py::run_ai_content_pipeline`, `run_stock_research`, `run_website_build`
- `services/api/src/aegisai/interfaces/http/auth.py::AuthRequired`, `require_authenticated`
- Same pattern org-wide: [loop-engine-agent-platform ADR-002](https://github.com/vpeetla-ai/loop-engine-agent-platform/blob/main/docs/ADR-002-repo-fix-auth-and-isolation.md), [sentinel-brief ADR-0002](https://github.com/vpeetla-ai/sentinel-brief/blob/main/docs/adr/0002-runs-auth-and-llm-synthesis.md)
