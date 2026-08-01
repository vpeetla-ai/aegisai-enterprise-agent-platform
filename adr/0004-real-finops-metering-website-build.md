# ADR 0004: Real Usage Metering + Budget Enforcement for Website Build Agents

## Status

Accepted

## In one breath (panel)

I'd meter real provider tokens into a shared FinOps ledger and halt the graph on budget breach — a seeded cost dashboard is demo theater, not FinOps.

## Context

ADR-0003 called out the scar: FinOps `monthly_cost_usd` was static seed data, and `LLMGateway` discarded the `usage` / `usageMetadata` the providers already returned. Fixing pricing math *inside* AegisAI would have duplicated what every other LLM-calling repo also needs.

What I refused: another per-repo fake FinOps module. The org built [`agent-finops`](https://github.com/vpeetla-ai/agent-finops) as the ledger; this ADR wires AegisAI as the first real consumer.

## Decision

1. `LLMResponse` carries real `prompt_tokens` / `completion_tokens` from OpenAI/Gemini. Local/unconfigured paths stay `0` — honest: no call, no tokens.
2. Registry gets `budget_usd` + `record_usage` write-through from agent-finops — cache, not a second source of truth.
3. **Vertical slice:** Website Build's four LLM-calling LangGraph nodes meter after each `complete()`, and a breach trips the real `KillSwitchService`.
4. The graph **halts** on breach (`conditional_edges` / sequential checks) — no later nodes, no GitHub push / deploy after a mid-node trip.
5. Without `AGENTFINOPS_API_URL`, the client computes locally and never reports breach — Demo stays Demo until an operator points at a real ledger.

**Implemented vs Planned:** Website Build metering ✅. `ai_content_pipeline` / `stock_research` agents still seed until wired.

## Consequences

### Positive

- FinOps numbers for those four agents are real
- Kill-switch has a real trigger, not only a manual API
- Tests cover write-through, activation, no-breach, and full-run halt

### Negative

- Other orchestrators not wired yet
- Breach detection is dormant until FinOps URL/key are set — same honesty as every other opt-in gate

### Follow-ups

- Wire remaining orchestrators once they have registry-backed agent IDs
- Auth-default and OPA fail-closed remain separate product calls (from ADR-0003)

## References

- `services/api/src/aegisai/application/knowledge/llm_gateway.py::LLMResponse`
- `services/api/src/aegisai/application/orchestration/website_build_pipeline.py::WebsiteBuildLangGraph._meter_llm_call`
- `services/api/src/aegisai/product/agent_registry.py::AgentRegistryService.record_usage`
- `services/api/tests/test_website_build_finops.py`
- [agent-finops](https://github.com/vpeetla-ai/agent-finops)
