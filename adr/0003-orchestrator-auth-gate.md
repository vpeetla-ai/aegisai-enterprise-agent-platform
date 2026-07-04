# ADR 0003: Auth Gate on Cron Orchestrator Endpoints, Corrected Registry Persistence Claim

## Status

Accepted

## Context

A security audit of the gateway request path (part of a broader review across the vpeetla-ai
org) found `POST /api/orchestrators/ai-content/run`, `POST /api/orchestrators/stock-research/run`,
and `POST /api/orchestrators/website-build/run` (`services/api/src/aegisai/interfaces/http/api.py`)
had no `AuthRequired` dependency at all — every other mutating route in the same file
(agent onboarding, lifecycle registration, gateway tool-request, kill-switches, connectors)
already requires it. These three trigger real LLM calls (Gemini/OpenAI) and, for website-build,
Vercel API calls. `render.yaml`'s cron jobs and the free-tier `.github/workflows/orchestrator-cron.yml`
alternative both call them with no credentials, and `apps/web`'s frontend never sends a bearer
token either — so nothing in the current deployment depended on these routes being open.

Separately, this review found the README's implementation-status table understated actual
capability: it listed "Agent registry Postgres persistence: 🟡 In-memory today," but
`services/api/src/aegisai/infrastructure/persistence/factory.py::build_agent_registry_service`
already supports a real `PostgresAgentRegistryStore`, selected via `AEGISAI_DB_BACKEND=postgres`
— SQLite is only the dev-mode default, not a hard limitation. The audit also confirmed the OPA
policy engine's existing "optional, defaults to builtin simulator" status is accurate, and that
it **fails open** (advisory only, never a hard block) when OPA itself is unavailable — worth
stating explicitly rather than leaving implicit.

## Decision

1. Add `auth: AuthRequired` to the three orchestrator run routes, matching the pattern already
   used everywhere else in `api.py`. Since `require_authenticated` only actually rejects a
   request when `AEGISAI_ENFORCE_AUTH=true` (default: `false`), this is a no-op today and only
   takes effect once the operator opts into enforcement — consistent with every other route's
   behavior, not a new auth mechanism.
2. Update both cron callers (`render.yaml`'s two `dockerCommand` entries and
   `.github/workflows/orchestrator-cron.yml`'s two `curl` calls) to send
   `X-AegisAI-Principal: render-cron` / `github-actions-cron` respectively, so enabling
   `AEGISAI_ENFORCE_AUTH` later doesn't silently break scheduled runs.
3. Correct the README's registry-persistence row to `✅` with the real mechanism documented,
   and add an explicit "fails open" note to the OPA row.

## Consequences

### Positive
- The three orchestrator endpoints are no longer uniquely exempt from the auth policy every
  other mutating route already enforces.
- Cron callers keep working today (enforcement is off by default) and won't silently break if
  `AEGISAI_ENFORCE_AUTH` is turned on later.
- README now accurately reflects that Postgres persistence for the agent registry already
  exists — this was undersold, not oversold, but accuracy matters both directions.

### Negative
- `AEGISAI_ENFORCE_AUTH` still defaults to `false`, so these routes remain open on any
  deployment that hasn't explicitly turned enforcement on — this ADR closes the "uniquely
  exempt" inconsistency, not the broader "auth is opt-in" posture, which is a bigger product
  decision (would need OIDC configured for every client, including the demo frontend).
- FinOps's `monthly_cost_usd` remains static seed data
  (`infrastructure/persistence/agent_registry_seeds.py`), not live token/request metering — the
  dashboard reports on configured numbers, not real gateway traffic. Wiring real cost tracking
  into every LLM call site across all orchestrators is a larger follow-up, not addressed here.
- OPA policy violations remain advisory (route to HITL) rather than a hard block — whether
  critical actions should fail-closed by default is a product/architecture decision for a
  future ADR, not assumed here.

### Follow-ups
- ADR-0004 (done): wire real per-call token/cost metering into the FinOps module — see
  [ADR-0004](./0004-real-finops-metering-website-build.md).
- ADR-0005 (proposed): decide whether `AEGISAI_ENFORCE_AUTH=true` should be the default for any
  deployment reachable from the public internet, and update the frontend to send real
  credentials rather than dev headers.
- ADR-0006 (proposed): make OPA policy decisions fail-closed for critical actions.

## References
- `services/api/src/aegisai/interfaces/http/api.py::run_ai_content_pipeline`,
  `run_stock_research`, `run_website_build`
- `services/api/src/aegisai/interfaces/http/auth.py::AuthRequired`, `require_authenticated`
- Same auth-gap pattern found and fixed org-wide: [loop-engine-agent-platform ADR-002](https://github.com/vpeetla-ai/loop-engine-agent-platform/blob/main/docs/ADR-002-repo-fix-auth-and-isolation.md), [sentinel-brief ADR-0002](https://github.com/vpeetla-ai/sentinel-brief/blob/main/docs/adr/0002-runs-auth-and-llm-synthesis.md)
