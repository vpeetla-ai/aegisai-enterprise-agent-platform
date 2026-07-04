"""MCP tool exposure for AegisAI's governed core.

`McpGovernanceProxy` (application/gateway/mcp_proxy.py) already gates *outbound* MCP
tool calls agents make to external servers (filesystem, github, postgres, ...). This
module is the missing other half: it *exposes* AegisAI's own governed capabilities as
MCP tools, so any MCP client (Claude Code, Cursor, Claude Desktop) can call them.

Importing the already-constructed singletons from interfaces.http.api (rather than
rebuilding them here) guarantees every MCP tool call runs against the exact same
governed object graph an HTTP caller would hit — FinOps metering and kill-switch
enforcement inside website_build_orchestrator apply identically either way.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from aegisai.interfaces.http.api import (
    agent_registry_service,
    kill_switch_service,
    website_build_orchestrator,
)

mcp = FastMCP("aegisai-governance")


def _enforce_auth_enabled() -> bool:
    return os.getenv("AEGISAI_ENFORCE_AUTH", "false").lower() == "true"


def _require_principal(principal_id: str) -> None:
    if _enforce_auth_enabled() and not principal_id:
        raise ValueError(
            "principal_id is required when AEGISAI_ENFORCE_AUTH=true — MCP tool calls "
            "carry no HTTP session, so the calling identity must be passed explicitly."
        )


@mcp.tool()
def list_registered_agents() -> dict[str, object]:
    """List every agent in AegisAI's governed registry, with real cost and budget."""
    agents = agent_registry_service.list_agents()
    return {
        "agents": [agent_registry_service.to_payload(agent) for agent in agents],
        "summary": agent_registry_service.summary(),
    }


@mcp.tool()
def check_agent_budget(agent_id: str) -> dict[str, object]:
    """Real budget status for one governed agent: metered cost vs. configured budget."""
    agent = agent_registry_service.get_agent(agent_id)
    if agent is None:
        return {"error": f"No agent registered with id '{agent_id}'."}
    payload = agent_registry_service.to_payload(agent)
    budget = payload.get("budget_usd")
    breached = budget is not None and payload["monthly_cost_usd"] > budget
    return {**payload, "breached": breached}


@mcp.tool()
def get_kill_switch_status() -> dict[str, object]:
    """Real-time kill-switch posture: active rules blocking agents, tools, or workflows."""
    return kill_switch_service.posture()


@mcp.tool()
def run_website_build(
    principal_id: str,
    tenant_id: str = "bank-demo",
    requirement: str | None = None,
) -> dict[str, object]:
    """Run the governed Website Build LangGraph orchestrator.

    Real FinOps metering and kill-switch enforcement apply exactly as they do for
    HTTP callers of POST /api/orchestrators/website-build/run — this tool calls the
    same orchestrator instance, not a parallel path.
    """
    _require_principal(principal_id)
    return website_build_orchestrator.run(tenant_id, requirement=requirement)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
