"""Tests for the MCP tool exposure layer (ADR-0005) — interfaces/mcp/server.py.

These tools call the same module-level singletons interfaces/http/api.py builds, so
these tests verify governed access through MCP, not a separate/duplicated code path.
"""

from __future__ import annotations

import asyncio

import pytest

from aegisai.interfaces.mcp import server as mcp_server
from aegisai.interfaces.mcp.server import (
    check_agent_budget,
    get_kill_switch_status,
    list_registered_agents,
    run_website_build,
)


def test_four_governed_tools_are_registered():
    tools = asyncio.run(mcp_server.mcp.list_tools())
    names = {t.name for t in tools}
    assert names == {
        "list_registered_agents",
        "check_agent_budget",
        "get_kill_switch_status",
        "run_website_build",
    }


def test_list_registered_agents_reflects_real_registry():
    result = list_registered_agents()
    agent_ids = {agent["agent_id"] for agent in result["agents"]}
    assert "agent-requirements-analyst" in agent_ids
    assert result["summary"]["total_agents"] == len(result["agents"])


def test_check_agent_budget_unknown_agent_returns_error():
    result = check_agent_budget("agent-does-not-exist")
    assert "error" in result


def test_check_agent_budget_breach_matches_real_cost_vs_budget():
    agent = mcp_server.agent_registry_service.get_agent("agent-requirements-analyst")
    result = check_agent_budget("agent-requirements-analyst")
    expected_breach = agent.budget_usd is not None and agent.monthly_cost_usd > agent.budget_usd
    assert result["breached"] == expected_breach


def test_get_kill_switch_status_reflects_real_posture():
    result = get_kill_switch_status()
    assert result["product_module"] == "Incident Response"
    assert result["active_rule_count"] == len(mcp_server.kill_switch_service.active_rules())


def test_run_website_build_requires_principal_when_auth_enforced(monkeypatch):
    monkeypatch.setenv("AEGISAI_ENFORCE_AUTH", "true")
    with pytest.raises(ValueError, match="principal_id is required"):
        run_website_build(principal_id="", tenant_id="bank-demo")


def test_run_website_build_executes_the_real_governed_orchestrator():
    result = run_website_build(
        principal_id="mcp-test-client",
        tenant_id="bank-demo",
        requirement="Build a small internal tools dashboard.",
    )
    assert result["status"] in {"completed", "blocked_by_kill_switch"}
    assert result["run_id"].startswith("web-")
