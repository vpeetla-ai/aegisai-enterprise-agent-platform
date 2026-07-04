# ADR 0004: Real Usage Metering + Budget Enforcement for Website Build Agents

## Status

Accepted

## Context

ADR-0003 flagged as a follow-up that FinOps's `monthly_cost_usd` was static seed data
(`infrastructure/persistence/agent_registry_seeds.py`), never real token/request metering, and
that `LLMGateway`'s `LLMResponse` discarded the real `usage`/`usageMetadata` field its own OpenAI
and Gemini responses already carry. Rather than build metering logic inside this repo, the org
built a standalone service — [`agent-finops`](https://github.com/vpeetla-ai/agent-finops), see
[org ADR-011](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/adr/ADR-011-agent-finops-standalone-service.md)
— matching this org's pattern of single-purpose repos rather than embedded per-repo logic. This
ADR covers wiring this repo as agent-finops's first real consumer.

## Decision

1. `LLMGateway.LLMResponse` now carries real `prompt_tokens`/`completion_tokens`, parsed from
   OpenAI's `data["usage"]` and Gemini's `data["usageMetadata"]` (both already present in the
   provider response, previously discarded). `local`/unconfigured paths keep the default `0` —
   honest, since no real call was made.
2. `RegisteredAgent` gained `budget_usd: float | None`. `AgentRegistryStore` (both
   `InMemoryAgentRegistryStore` and `PostgresAgentRegistryStore`) gained `update_cost`, mirroring
   the existing `update_status` pattern exactly. `AgentRegistryService.record_usage(agent_id,
   cost_usd)` adds real cost to `monthly_cost_usd` — a write-through cache from agent-finops's own
   ledger, not a second source of truth.
3. **Vertical slice: `WebsiteBuildOrchestrator`'s 5 LangGraph nodes**, chosen because 4 of them
   call an LLM and already map 1:1 to existing registry entries (`agent-requirements-analyst`,
   `agent-ui-design-analyst`, `agent-fe-builder`, `agent-be-builder` — `review_deploy` has no LLM
   call, nothing to meter). After each node's `LLMGateway.complete()` call,
   `WebsiteBuildLangGraph._meter_llm_call` calls `agent_finops_client.FinOpsClient.record_usage(...)`,
   writes the real cost through to the local registry, and — if breached —
   calls the existing, real `KillSwitchService.activate("agent", agent_id, ...)`.
4. **The graph now halts on a breach** instead of continuing regardless: `_build_graph` replaced
   unconditional `add_edge` calls with `add_conditional_edges`, routing to `END` once
   `state["status"] == "blocked_by_kill_switch"`; the `_sequential` fallback checks the same
   condition between nodes. `fe_impl`/`be_impl` additionally skip their GitHub push / deploy
   gateway calls when their own node's call breaches — no side effect fires after the budget
   trips mid-node.
5. Given no `AGENTFINOPS_API_URL` is set, `FinOpsClient` computes cost locally and never reports
   a breach (no persisted ledger to check against) — the existing default demo behavior is
   unaffected until an operator points this at a real `agent-finops` deployment.

## Consequences

### Positive
- FinOps's numbers for these 4 agents are now real, not seed data — the first genuine fix of the
  gap ADR-0003 flagged.
- The kill-switch — already real, already working — now has a real trigger condition instead of
  only being reachable via the manual `/api/kill-switches` endpoint.
- 4 new tests prove the reaction to a breach signal: cost write-through, kill-switch activation,
  no-breach leaves the agent unblocked, and a full orchestrator run halts before later nodes run
  (their artifacts stay empty).

### Negative
- Only `WebsiteBuildOrchestrator` is wired — `ai_content_pipeline` and `stock_research`
  orchestrators' agents don't have matching registry entries yet, so their FinOps numbers remain
  seed data until a fast-follow adds them.
- Requires `AGENTFINOPS_API_URL`/`AGENTFINOPS_API_KEY` actually set for breach detection to mean
  anything — unset, this ADR's enforcement path is present but dormant, same caveat as every
  other opt-in gate built this session.

### Follow-ups
- Wire `ai_content_pipeline` and `stock_research` orchestrators once they have registry-backed
  agent identities to attribute cost to.
- ADR-0005 (proposed, carried from ADR-0003): decide whether `AEGISAI_ENFORCE_AUTH=true` should
  be the production default.
- ADR-0006 (proposed, carried from ADR-0003): OPA fail-closed for critical actions.

## References
- `services/api/src/aegisai/application/knowledge/llm_gateway.py::LLMResponse`
- `services/api/src/aegisai/application/orchestration/website_build_pipeline.py::WebsiteBuildLangGraph._meter_llm_call`
- `services/api/src/aegisai/product/agent_registry.py::AgentRegistryService.record_usage`
- `services/api/tests/test_website_build_finops.py`
- [agent-finops](https://github.com/vpeetla-ai/agent-finops)
