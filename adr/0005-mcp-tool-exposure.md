# ADR-0005: Expose governed capabilities as MCP tools (bidirectional MCP)

## Status

Accepted

## Context

`McpGovernanceProxy` (`application/gateway/mcp_proxy.py`) already gates *outbound* MCP
tool calls — when an AegisAI agent wants to call an external MCP server (filesystem,
github, postgres, ...), the call is routed through policy, HITL, and kill-switch checks
before it reaches that server. That is one half of MCP.

The other half was missing: nothing in this repo *exposed* AegisAI's own governed
capabilities — the agent registry, kill-switch posture, and the Website Build
orchestrator — as MCP tools that an external MCP client (Claude Code, Cursor, Claude
Desktop) could call. Without it, "MCP support" meant only "agents can reach out," not
"this platform can be reached."

## Decision

Add `interfaces/mcp/server.py` — a real MCP server (`mcp.server.fastmcp.FastMCP`)
exposing four tools: `list_registered_agents`, `check_agent_budget`,
`get_kill_switch_status`, `run_website_build`.

The module imports the already-constructed singletons from `interfaces/http/api.py`
(`agent_registry_service`, `kill_switch_service`, `website_build_orchestrator`) rather
than rebuilding them. This means every MCP tool call runs against the exact same
governed object graph an HTTP caller would hit: `run_website_build` calls the same
`WebsiteBuildOrchestrator.run(...)` that already does real FinOps metering via
[agent-finops](https://github.com/vpeetla-ai/agent-finops) and trips the real
kill-switch on a budget breach (ADR-0004). An MCP client gets governed access, not a
parallel, ungoverned path.

Auth follows the same convention as the HTTP layer's `AEGISAI_ENFORCE_AUTH` flag
(`interfaces/http/auth.py`) rather than inventing a second mechanism: when enforcement
is on, `run_website_build` requires a non-empty `principal_id` argument, since MCP tool
calls carry no HTTP session/header to resolve identity from implicitly.

## Consequences

- MCP is now bidirectional: `McpGovernanceProxy` gates what AegisAI agents call out to;
  `interfaces/mcp/server.py` gates what external MCP clients can call in.
- No duplicate business logic — the MCP layer is a thin protocol adapter, so any future
  fix to FinOps metering or kill-switch behavior automatically applies to MCP callers
  too.
- `list_registered_agents` and `get_kill_switch_status` are read-only and unauthenticated
  by design (mirrors `GET /api/agent-registry` and `GET /api/kill-switches`, neither of
  which requires `AuthRequired` today); only `run_website_build` (a mutating,
  cost-incurring action) enforces the principal check.
