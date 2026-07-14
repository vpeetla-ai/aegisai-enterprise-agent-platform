"""AI Content Pipeline — multi-agent orchestrator for enterprise AI thought leadership.

Schedule: 2x per week (Mon/Thu 07:00 UTC) via Render cron or external scheduler.
Agents: Scout → Researcher → Topic Architect → Publisher (Slack).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable
from uuid import uuid4

from aegisai.application.knowledge.llm_gateway import LLMGateway
from aegisai.infrastructure.notifications.delivery import NotificationDeliveryService

GatewayFn = Callable[..., dict[str, object]]
HitlPersistFn = Callable[..., dict[str, Any] | None]

FOCUS_AREAS = (
    "Enterprise AI platforms",
    "agentic AI",
    "multi-agent systems",
    "RAG",
    "LLMOps",
    "AI governance",
    "AI security",
    "model routing",
    "evaluation",
    "operating models",
    "business impact",
)


@dataclass
class PipelineState:
    run_id: str
    tenant_id: str
    started_at: str
    scout_signals: list[dict[str, Any]] = field(default_factory=list)
    research_papers: list[dict[str, Any]] = field(default_factory=list)
    trend_signals: list[str] = field(default_factory=list)
    topics: list[dict[str, Any]] = field(default_factory=list)
    slack_delivery: dict[str, Any] = field(default_factory=dict)
    agent_traces: list[dict[str, Any]] = field(default_factory=list)
    gateway_events: list[dict[str, Any]] = field(default_factory=list)
    hitl_tasks: list[dict[str, Any]] = field(default_factory=list)
    status: str = "running"


class ScoutAgent:
    """Aggregates top AI news and trend signals from configured search APIs."""

    def run(self, state: PipelineState) -> PipelineState:
        state.agent_traces.append({"agent": "scout", "step": "aggregate_signals", "status": "active"})
        # Production: bind to Perplexity, Google Search, or news APIs
        state.scout_signals = [
            {
                "headline": "Enterprise agent governance platforms gain CIO adoption",
                "source": "synthetic-demo",
                "category": "AI governance",
                "url": "https://example.com/agent-governance-trend",
            },
            {
                "headline": "Multi-agent orchestration frameworks consolidate around control planes",
                "source": "synthetic-demo",
                "category": "multi-agent systems",
                "url": "https://example.com/multi-agent-control-plane",
            },
            {
                "headline": "RAG evaluation gates become release requirement for production LLM apps",
                "source": "synthetic-demo",
                "category": "RAG / LLMOps",
                "url": "https://example.com/rag-eval-gates",
            },
        ]
        state.trend_signals = [
            "Agent control planes replacing point-solution observability",
            "HITL + policy-as-code as default enterprise agent pattern",
            "Model routing and cost governance tied to agent registry",
        ]
        state.agent_traces[-1]["status"] = "completed"
        return state


class ResearcherAgent:
    """Finds recent AI research papers aligned to enterprise architecture themes."""

    def run(self, state: PipelineState) -> PipelineState:
        state.agent_traces.append({"agent": "researcher", "step": "fetch_papers", "status": "active"})
        state.research_papers = [
            {
                "title": "Governance Architectures for Multi-Agent Enterprise Systems",
                "venue": "arXiv (demo)",
                "theme": "AI governance",
                "why_it_matters": "Formalizes control-plane boundaries for agent sprawl.",
            },
            {
                "title": "Evaluation Gates for Retrieval-Augmented Production Agents",
                "venue": "arXiv (demo)",
                "theme": "RAG / evaluation",
                "why_it_matters": "Links golden evals to release promotion for agent tools.",
            },
        ]
        state.agent_traces[-1]["status"] = "completed"
        return state


class TopicArchitectAgent:
    """Generates LinkedIn/Substack topic ideas for Principal AI Architect positioning."""

    def __init__(self, llm: LLMGateway | None = None) -> None:
        self._llm = llm or LLMGateway(
            provider=os.getenv("AEGISAI_LLM_PROVIDER", "local"),
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        )

    def run(self, state: PipelineState) -> PipelineState:
        state.agent_traces.append({"agent": "topic_architect", "step": "generate_topics", "status": "active"})
        signals = json.dumps(state.scout_signals[:3], indent=2)
        trends = ", ".join(state.trend_signals)
        system = (
            "You are a Principal AI Architect content strategist. "
            "Generate 3 LinkedIn/Substack topic ideas as JSON array. "
            "Each object: topic, hook, purpose, short_context, enterprise_relevance, "
            "suggested_format (LinkedIn post|Substack essay|carousel), seo_keywords (array)."
        )
        user = f"Signals:\n{signals}\nTrends: {trends}\nFocus: {', '.join(FOCUS_AREAS)}"
        response = self._llm.complete(system, user)
        try:
            state.topics = json.loads(response.content)
        except json.JSONDecodeError:
            state.topics = [
                {
                    "topic": "Why agent control planes beat agent builders for enterprise AI",
                    "hook": "Building agents is easy. Governing them is the product.",
                    "purpose": "Position AegisAI / Principal AI Architect thesis",
                    "short_context": response.content[:400],
                    "enterprise_relevance": "Maps to Rubrik/Guild control-plane category",
                    "suggested_format": "LinkedIn post",
                    "seo_keywords": ["AI governance", "agent control plane", "enterprise AI"],
                }
            ]
        state.agent_traces[-1]["status"] = "completed"
        return state


class PublisherAgent:
    """Delivers topic pipeline to Slack channel — gated by AI Gateway."""

    def __init__(
        self,
        gateway_fn: GatewayFn | None = None,
        hitl_persist_fn: HitlPersistFn | None = None,
    ) -> None:
        self._gateway_fn = gateway_fn
        self._hitl_persist_fn = hitl_persist_fn

    def run(self, state: PipelineState) -> PipelineState:
        state.agent_traces.append({"agent": "publisher", "step": "slack_delivery", "status": "active"})
        blocks = _format_slack_message(state)
        gateway_event: dict[str, Any] = {"tool_name": "notify.slack_publish"}
        if self._gateway_fn is not None:
            decision = self._gateway_fn(
                tenant_id=state.tenant_id,
                agent_id="agent-content-publisher",
                principal_id="ai-content-pipeline",
                tool_name="notify.slack_publish",
                action_type="notify_slack",
                target_system="slack",
                amount_usd=0,
                reversible=True,
                customer_impact=False,
            )
            gateway_event = {
                "tool_name": "notify.slack_publish",
                "gateway_decision": decision.get("gateway_decision"),
                "business_explanation": decision.get("business_explanation"),
            }
            state.gateway_events.append(gateway_event)
            if decision.get("gateway_decision") == "approval_required":
                if self._hitl_persist_fn is not None:
                    task = self._hitl_persist_fn(
                        tenant_id=state.tenant_id,
                        run_id=state.run_id,
                        agent_id="agent-content-publisher",
                        tool_name="notify.slack_publish",
                        action_type="notify_slack",
                        target_system="slack",
                        workflow_type="ai_content_pipeline",
                        gateway_decision="approval_required",
                        business_explanation=str(decision.get("business_explanation") or ""),
                    )
                    if task:
                        state.hitl_tasks.append(task)
                state.slack_delivery = {
                    "channel": os.getenv("SLACK_CONTENT_CHANNEL", "#ai-content-pipeline"),
                    "delivered": False,
                    "pending_hitl": True,
                    "preview": blocks["text"][:500],
                }
                state.agent_traces[-1]["status"] = "pending_hitl"
                state.status = "pending_hitl"
                return state
            if decision.get("gateway_decision") in {"block", "deny", "frozen"}:
                state.slack_delivery = {
                    "delivered": False,
                    "blocked": True,
                    "gateway_decision": decision.get("gateway_decision"),
                    "preview": blocks["text"][:500],
                }
                state.agent_traces[-1]["status"] = "blocked"
                state.status = "blocked"
                return state

        deliveries = NotificationDeliveryService().deliver_markdown(
            blocks["text"],
            slack_webhook_env="SLACK_CONTENT_WEBHOOK_URL",
        )
        delivered = any(d.delivered for d in deliveries)
        state.slack_delivery = {
            "channel": os.getenv("SLACK_CONTENT_CHANNEL", "#ai-content-pipeline"),
            "delivered": delivered,
            "configured": bool(deliveries),
            "preview": blocks["text"][:500],
            "channels": [
                {"channel": d.channel, "delivered": d.delivered, "detail": d.detail}
                for d in deliveries
            ],
        }
        state.agent_traces[-1]["status"] = "completed"
        state.status = "completed"
        return state


def _format_slack_message(state: PipelineState) -> dict[str, Any]:
    lines = [f"*AI Content Pipeline* · `{state.run_id}` · {state.started_at[:10]}"]
    for i, topic in enumerate(state.topics[:3], 1):
        lines.append(f"\n*{i}. {topic.get('topic', 'Topic')}*")
        lines.append(f"Hook: {topic.get('hook', '')}")
        lines.append(f"Format: {topic.get('suggested_format', 'LinkedIn post')}")
    text = "\n".join(lines)
    return {"text": text, "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]}


class AIContentPipelineOrchestrator:
    SCHEDULE = "0 7 * * 1,4"  # Mon & Thu 07:00 UTC
    ORCHESTRATOR_ID = "orchestrator-ai-content-pipeline"

    def __init__(
        self,
        gateway_fn: GatewayFn | None = None,
        hitl_persist_fn: HitlPersistFn | None = None,
    ) -> None:
        self._scout = ScoutAgent()
        self._researcher = ResearcherAgent()
        self._architect = TopicArchitectAgent()
        self._publisher = PublisherAgent(gateway_fn=gateway_fn, hitl_persist_fn=hitl_persist_fn)
        self._runs: list[dict[str, Any]] = []

    def run(self, tenant_id: str = "bank-demo") -> dict[str, Any]:
        state = PipelineState(
            run_id=f"content-{uuid4().hex[:12]}",
            tenant_id=tenant_id,
            started_at=datetime.now(UTC).isoformat(),
        )
        state = self._scout.run(state)
        state = self._researcher.run(state)
        state = self._architect.run(state)
        state = self._publisher.run(state)
        payload = {
            "orchestrator_id": self.ORCHESTRATOR_ID,
            "run_id": state.run_id,
            "tenant_id": state.tenant_id,
            "status": state.status,
            "schedule": self.SCHEDULE,
            "topics": state.topics,
            "trend_signals": state.trend_signals,
            "scout_signals": state.scout_signals,
            "research_papers": state.research_papers,
            "slack_delivery": state.slack_delivery,
            "gateway_events": state.gateway_events,
            "hitl_tasks": state.hitl_tasks,
            "hitl_pending": state.status == "pending_hitl",
            "agent_traces": state.agent_traces,
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self._runs.insert(0, payload)
        return payload

    def list_runs(self, limit: int = 10) -> dict[str, object]:
        return {
            "orchestrator_id": self.ORCHESTRATOR_ID,
            "name": "AI Content Pipeline",
            "schedule": self.SCHEDULE,
            "description": "Scout AI news & research → generate LinkedIn/Substack topics → Slack",
            "runs": self._runs[:limit],
        }

    def posture(self) -> dict[str, object]:
        return {
            "orchestrator_id": self.ORCHESTRATOR_ID,
            "name": "AI Content Pipeline",
            "agents": ["scout", "researcher", "topic_architect", "publisher"],
            "schedule": "Mon & Thu 07:00 UTC (2x/week)",
            "output": "LinkedIn/Substack topic ideas → Slack",
            "governance": "AI Gateway intercept on notify.slack_publish · HITL before delivery",
            "last_run": self._runs[0] if self._runs else None,
        }
