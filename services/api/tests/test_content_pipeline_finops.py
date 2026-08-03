"""AI Content Pipeline FinOps metering (extends ADR-0004 to cron LLM agent)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent_finops_client import FinOpsClient, UsageResult

from aegisai.application.knowledge.llm_gateway import LLMResponse
from aegisai.application.orchestration.ai_content_pipeline import (
    TopicArchitectAgent,
    PipelineState,
)


def test_topic_architect_meters_and_halts_on_breach():
    llm = MagicMock()
    llm.complete.return_value = LLMResponse(
        provider="local",
        model="deterministic-policy-model",
        content='[{"topic":"t","hook":"h","purpose":"p","short_context":"c","enterprise_relevance":"e","suggested_format":"LinkedIn post","seo_keywords":["a"]}]',
        confidence=0.9,
        prompt_tokens=10,
        completion_tokens=20,
    )
    finops = MagicMock(spec=FinOpsClient)
    finops.record_usage.return_value = UsageResult(
        cost_usd=1.0,
        total_cost_usd=20.0,
        budget_usd=15.0,
        breached=True,
    )
    kill = MagicMock()
    registry = MagicMock()

    agent = TopicArchitectAgent(
        llm=llm,
        finops_client=finops,
        agent_registry=registry,
        kill_switch_service=kill,
    )
    state = PipelineState(
        run_id="content-test",
        tenant_id="bank-demo",
        started_at="2026-08-02T00:00:00+00:00",
        scout_signals=[{"headline": "x"}],
        trend_signals=["y"],
    )
    out = agent.run(state)
    assert out.status == "blocked_by_kill_switch"
    finops.record_usage.assert_called_once()
    kill.activate.assert_called_once()
    registry.record_usage.assert_called_once()


def test_topic_architect_continues_when_budget_ok():
    llm = MagicMock()
    llm.complete.return_value = LLMResponse(
        provider="local",
        model="deterministic-policy-model",
        content='[{"topic":"ok","hook":"h","purpose":"p","short_context":"c","enterprise_relevance":"e","suggested_format":"LinkedIn post","seo_keywords":["a"]}]',
        confidence=0.9,
        prompt_tokens=5,
        completion_tokens=5,
    )
    finops = MagicMock(spec=FinOpsClient)
    finops.record_usage.return_value = UsageResult(
        cost_usd=0.01,
        total_cost_usd=0.01,
        budget_usd=15.0,
        breached=False,
    )
    agent = TopicArchitectAgent(llm=llm, finops_client=finops)
    state = PipelineState(
        run_id="content-test-2",
        tenant_id="bank-demo",
        started_at="2026-08-02T00:00:00+00:00",
        scout_signals=[{"headline": "x"}],
        trend_signals=["y"],
    )
    out = agent.run(state)
    assert out.status == "running"
    assert out.topics and out.topics[0]["topic"] == "ok"
