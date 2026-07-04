"""Tests for real usage metering + budget-breach kill-switch wiring in the
Website Build orchestrator — see ADR-011 (agent-finops) and this repo's
adr/0004 (once added). agent-finops's own budget math is tested in that
repo; these tests cover this repo's reaction to a breach signal."""

from __future__ import annotations

from unittest.mock import patch

from agent_finops_client import FinOpsClient, UsageResult

from aegisai.application.knowledge.llm_gateway import LLMResponse
from aegisai.application.orchestration.website_build_pipeline import (
    WebsiteBuildLangGraph,
    WebsiteBuildOrchestrator,
)
from aegisai.product.agent_registry import AgentRegistryService
from aegisai.product.kill_switch import KillSwitchService


class FakeLLM:
    """Deterministic stand-in for LLMGateway — always returns real-looking usage."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(
            provider="openai",
            model="gpt-4.1-mini",
            content="{}",
            confidence=0.9,
            prompt_tokens=1000,
            completion_tokens=200,
        )


def _build(registry: AgentRegistryService, kill_switch: KillSwitchService, breached: bool):
    graph = WebsiteBuildLangGraph(
        llm=FakeLLM(),
        gateway_fn=None,
        finops_client=FinOpsClient(base_url="https://agent-finops.example", api_key=None),
        agent_registry=registry,
        kill_switch_service=kill_switch,
    )
    patcher = patch.object(
        FinOpsClient,
        "record_usage",
        return_value=UsageResult(cost_usd=15.0, total_cost_usd=15.0, budget_usd=10.0, breached=breached),
    )
    return graph, patcher


def test_real_usage_writes_through_to_registry():
    registry = AgentRegistryService()
    kill_switch = KillSwitchService()
    graph, patcher = _build(registry, kill_switch, breached=False)
    before = registry.get_agent("agent-requirements-analyst").monthly_cost_usd
    with patcher:
        graph._requirements_node({"run_id": "r1", "tenant_id": "t1", "requirement": "test", "agent_traces": []})
    after = registry.get_agent("agent-requirements-analyst").monthly_cost_usd
    assert after == before + 15.0


def test_budget_breach_activates_kill_switch():
    registry = AgentRegistryService()
    kill_switch = KillSwitchService()
    graph, patcher = _build(registry, kill_switch, breached=True)
    with patcher:
        result = graph._requirements_node(
            {"run_id": "r1", "tenant_id": "t1", "requirement": "test", "agent_traces": []}
        )
    assert result["status"] == "blocked_by_kill_switch"
    assert kill_switch.is_blocked("bank-demo", agent_id="agent-requirements-analyst") is not None


def test_no_breach_leaves_agent_unblocked():
    registry = AgentRegistryService()
    kill_switch = KillSwitchService()
    graph, patcher = _build(registry, kill_switch, breached=False)
    with patcher:
        result = graph._requirements_node(
            {"run_id": "r1", "tenant_id": "t1", "requirement": "test", "agent_traces": []}
        )
    assert result.get("status") != "blocked_by_kill_switch"
    assert kill_switch.is_blocked("bank-demo", agent_id="agent-requirements-analyst") is None


def test_orchestrator_run_halts_on_breach_and_skips_later_nodes():
    """Exercises whichever path invoke() actually takes (compiled LangGraph when
    the package is installed, sequential fallback otherwise) — both must halt."""
    registry = AgentRegistryService()
    kill_switch = KillSwitchService()
    graph, patcher = _build(registry, kill_switch, breached=True)
    orchestrator = WebsiteBuildOrchestrator.__new__(WebsiteBuildOrchestrator)
    orchestrator._graph = graph
    orchestrator._observability = None
    orchestrator._runs = []
    with patcher:
        result = orchestrator.run(tenant_id="bank-demo", requirement="Build a thing")
    assert result["status"] == "blocked_by_kill_switch"
    # requirements_node is where the breach fires (first node) — later nodes never ran.
    assert result["ui_spec"] == {}
    assert result["be_artifacts"] == {}
