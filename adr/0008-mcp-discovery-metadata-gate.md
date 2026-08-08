# ADR-0008 — MCP discovery metadata trust gate

**Status:** Accepted  
**Date:** 2026-08-08  
**Repos:** aegisai-enterprise-agent-platform  
**Related:** [ADR-0005](0005-mcp-tool-exposure.md)

## Context

ADR-0005 mediates MCP *invocation* through the governance gateway. Poisoned tool
descriptions can still reach the model at discovery time, before any invoke.

## Decision

- Add `McpMetadataScanner` + `POST /api/mcp/discover`.
- Block (deny) on injection/exfil patterns and manifest digest mismatch.
- Require `owner` + `risk_class` (HITL if missing).
- Only `model_visible_tools` should be returned to the LLM tool list.

## Consequences

- Invoke path unchanged; discovery is an explicit additional gate.
- Demo can POST a poisoned fixture and show deny without side effects.
