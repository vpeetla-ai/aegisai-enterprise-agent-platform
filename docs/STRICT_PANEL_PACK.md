# Strict AegisAI panel pack (Wave 1.5)

**Demo API:** public Render free tier (cold starts; Demo defaults)  
**Strict API (preferred interim):** local `./scripts/run_strict_local.sh`  
**ADRs:** [0007-fail-closed-policy-plane](../adr/0007-fail-closed-policy-plane.md) · [0008-mcp-discovery-metadata-gate](../adr/0008-mcp-discovery-metadata-gate.md)

## Why dual process

`PRODUCTION_STRICT` is process environment. One process cannot be Demo and Strict safely.

## Option A — Local Strict (no cloud bill)

```bash
cd aegisai-enterprise-agent-platform
./scripts/run_strict_local.sh
# other terminal:
./scripts/probe_strict_panel.sh
```

Expect:

| Probe | Pass signal |
|-------|-------------|
| `/health` | `enforcement.production_strict=true`, `policy_plane.fail_closed_for_irreversible=true` |
| MCP discover poison | `denied` includes `evil_exfil` / decision deny |
| Evidence pack | `packet_type=aegisai.incident_evidence_pack` |

Optional OPA CLI: install `opa` and keep `AEGISAI_POLICY_ENGINE=opa` so `policy_plane.mode=opa`. Without OPA, Strict still **denies** irreversible tools with `policy_unavailable` (fail-closed).

## Option B — Paid always-on (owner)

Upgrade the Render API to Starter (or equivalent) and set:

```bash
PRODUCTION_STRICT=true
AEGISAI_REQUIRE_EXECUTION_TOKEN=true
AEGISAI_ENFORCE_AUTH=true
AEGISAI_POLICY_ENGINE=opa
```

Do **not** flip the public marketing demo to Strict without a twin service.

## Five-minute panel script

1. `GET /health` → show Strict flags + `policy_plane`.
2. Irreversible tool via `POST /api/gateway/tool-request` with `reversible=false` when OPA is down → `block` / `policy_unavailable`.
3. `POST /api/mcp/discover` with poisoned description → blocked from model.
4. `GET /api/evidence-packs/bank-demo/case-panel-redacted` → passport + signature.
5. `POST /api/execution-tokens/revoke` after a token issue → verify fails.

## Portfolio links

- Golden path P0 probes: [GOLDEN_PATH.md](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/GOLDEN_PATH.md)
- Sample pack: [`docs/samples/incident-evidence-pack.json`](./samples/incident-evidence-pack.json)
