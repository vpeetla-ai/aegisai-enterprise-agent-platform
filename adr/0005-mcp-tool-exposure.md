# ADR-0005: Expose governed capabilities as MCP tools (bidirectional MCP)

## Status

Accepted

## In one breath (panel)

I'd expose AegisAI as MCP tools that hit the *same* governed singletons as HTTP — not a parallel ungoverned path for Claude Code or Cursor.

## Context

`McpGovernanceProxy` already gates *outbound* MCP: when an AegisAI agent calls filesystem/github/postgres/…, policy + HITL + kill-switch run first. That was half of MCP.

The missing half: nothing exposed our own capabilities (registry, kill-switch posture, Website Build) as inbound MCP tools. "MCP support" meant agents could reach out — not that an external client could reach *in* under governance.

What I refused: a second business stack for MCP that skips FinOps or kill-switch.

## Decision

Add `interfaces/mcp/server.py` (`FastMCP`) with four tools: `list_registered_agents`, `check_agent_budget`, `get_kill_switch_status`, `run_website_build`.

Import the same singletons the HTTP API uses. `run_website_build` calls the same orchestrator that meters via agent-finops and trips kill-switch (ADR-0004).

Auth follows `AEGISAI_ENFORCE_AUTH` — when on, mutating `run_website_build` requires a non-empty `principal_id` (MCP has no HTTP session to infer from).

**Demo vs Strict:** read-only tools stay open (mirrors today's HTTP GETs). Mutating run enforces principal only when enforcement is on.

## Consequences

- MCP is bidirectional: proxy out, server in
- No duplicate business logic — protocol adapter only
- Read-only tools unauthenticated by design today; only the cost-incurring run is gated under enforcement
