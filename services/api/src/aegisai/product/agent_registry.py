from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisteredAgent:
    agent_id: str
    name: str
    owner: str
    business_domain: str
    risk_tier: str
    autonomy_level: int
    status: str
    model_provider: str
    allowed_tools: tuple[str, ...]
    data_classes: tuple[str, ...]
    last_run_at: str
    monthly_cost_usd: float
    open_incidents: int
    value_metric: str


class AgentRegistryService:
    """Product-facing inventory of governed enterprise agents."""

    def __init__(self) -> None:
        self._agents: dict[str, RegisteredAgent] = {
            agent.agent_id: agent for agent in self._seed_agents()
        }

    def list_agents(self) -> tuple[RegisteredAgent, ...]:
        return tuple(self._agents.values())

    def get_agent(self, agent_id: str) -> RegisteredAgent | None:
        return self._agents.get(agent_id)

    def register_agent(
        self,
        agent_id: str,
        name: str,
        owner: str,
        business_domain: str,
        risk_tier: str,
        autonomy_level: int,
        allowed_tools: tuple[str, ...],
        data_classes: tuple[str, ...],
        status: str = "pilot",
        model_provider: str = "OpenAI/local fallback",
    ) -> RegisteredAgent:
        agent = RegisteredAgent(
            agent_id=agent_id,
            name=name,
            owner=owner,
            business_domain=business_domain,
            risk_tier=risk_tier,
            autonomy_level=autonomy_level,
            status=status,
            model_provider=model_provider,
            allowed_tools=allowed_tools,
            data_classes=data_classes,
            last_run_at="not_run_yet",
            monthly_cost_usd=0.0,
            open_incidents=0,
            value_metric="Pending production value baseline",
        )
        self._agents[agent_id] = agent
        return agent

    def update_agent_status(self, agent_id: str, status: str) -> RegisteredAgent | None:
        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        updated = RegisteredAgent(
            agent_id=agent.agent_id,
            name=agent.name,
            owner=agent.owner,
            business_domain=agent.business_domain,
            risk_tier=agent.risk_tier,
            autonomy_level=agent.autonomy_level,
            status=status,
            model_provider=agent.model_provider,
            allowed_tools=agent.allowed_tools,
            data_classes=agent.data_classes,
            last_run_at=agent.last_run_at,
            monthly_cost_usd=agent.monthly_cost_usd,
            open_incidents=agent.open_incidents,
            value_metric=agent.value_metric,
        )
        self._agents[agent_id] = updated
        return updated

    def lifecycle(self) -> dict[str, object]:
        agents = self.list_agents()
        return {
            "product_module": "Agent Registry Lifecycle",
            "headline": "Register, approve, restrict, revoke, and deprecate agents as governed assets.",
            "allowed_statuses": ["shadow", "pilot", "restricted", "approved", "revoked", "deprecated"],
            "agents": [self.to_payload(agent) for agent in agents],
            "controls": [
                "Owner, domain, tools, data classes, risk tier, and autonomy level are required.",
                "High-risk agents require policy, eval, observability, and kill-switch readiness.",
                "Production promotion must pass release gates and reviewer approval.",
                "Revoked agents cannot receive execution tokens.",
            ],
        }

    @staticmethod
    def to_payload(agent: RegisteredAgent) -> dict[str, object]:
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "owner": agent.owner,
            "business_domain": agent.business_domain,
            "risk_tier": agent.risk_tier,
            "autonomy_level": agent.autonomy_level,
            "status": agent.status,
            "model_provider": agent.model_provider,
            "allowed_tools": list(agent.allowed_tools),
            "data_classes": list(agent.data_classes),
            "last_run_at": agent.last_run_at,
            "monthly_cost_usd": agent.monthly_cost_usd,
            "open_incidents": agent.open_incidents,
            "value_metric": agent.value_metric,
        }

    def _seed_agents(self) -> tuple[RegisteredAgent, ...]:
        return (
            RegisteredAgent(
                agent_id="agent-intake-triage",
                name="Intake & Triage Agent",
                owner="AI Platform",
                business_domain="Customer Operations",
                risk_tier="medium",
                autonomy_level=2,
                status="approved",
                model_provider="OpenAI/local fallback",
                allowed_tools=("rag.search_policy_memory",),
                data_classes=("public", "internal", "confidential"),
                last_run_at="2026-05-25T09:10:00-07:00",
                monthly_cost_usd=42.0,
                open_incidents=0,
                value_metric="Classifies requests in under 2 seconds",
            ),
            RegisteredAgent(
                agent_id="agent-refund",
                name="Refund Agent",
                owner="Finance Operations",
                business_domain="Payments",
                risk_tier="high",
                autonomy_level=3,
                status="approved",
                model_provider="OpenAI/local fallback",
                allowed_tools=("rag.search_policy_memory", "payments.issue_refund"),
                data_classes=("internal", "confidential"),
                last_run_at="2026-05-25T09:08:00-07:00",
                monthly_cost_usd=118.0,
                open_incidents=0,
                value_metric="Reduces refund review cycle time by 38%",
            ),
            RegisteredAgent(
                agent_id="agent-data-ops",
                name="Data Operations Agent",
                owner="Privacy Office",
                business_domain="Privacy Operations",
                risk_tier="critical",
                autonomy_level=2,
                status="restricted",
                model_provider="OpenAI/local fallback",
                allowed_tools=("rag.search_policy_memory", "privacy.modify_or_delete_data"),
                data_classes=("confidential", "restricted"),
                last_run_at="2026-05-25T08:52:00-07:00",
                monthly_cost_usd=74.0,
                open_incidents=0,
                value_metric="Prevents irreversible data actions without compliance approval",
            ),
            RegisteredAgent(
                agent_id="agent-it-ops",
                name="IT Operations Agent",
                owner="SRE",
                business_domain="Infrastructure",
                risk_tier="high",
                autonomy_level=2,
                status="pilot",
                model_provider="OpenAI/local fallback",
                allowed_tools=("rag.search_policy_memory", "infra.change_production_configuration"),
                data_classes=("internal", "confidential"),
                last_run_at="2026-05-25T08:34:00-07:00",
                monthly_cost_usd=96.0,
                open_incidents=1,
                value_metric="Drafts safe change plans with rollback metadata",
            ),
            RegisteredAgent(
                agent_id="agent-requirements-analyst",
                name="Requirements Analyst",
                owner="Website Build Pipeline",
                business_domain="Software Delivery",
                risk_tier="low",
                autonomy_level=2,
                status="approved",
                model_provider="OpenAI/local fallback",
                allowed_tools=("rag.search_policy_memory",),
                data_classes=("internal",),
                last_run_at="not_run_yet",
                monthly_cost_usd=28.0,
                open_incidents=0,
                value_metric="Parses build requirements into acceptance criteria",
            ),
            RegisteredAgent(
                agent_id="agent-ui-design-analyst",
                name="UI Design Analyst",
                owner="Website Build Pipeline",
                business_domain="Software Delivery",
                risk_tier="low",
                autonomy_level=2,
                status="approved",
                model_provider="OpenAI/local fallback",
                allowed_tools=("rag.search_policy_memory", "design.analyze_figma"),
                data_classes=("internal",),
                last_run_at="not_run_yet",
                monthly_cost_usd=32.0,
                open_incidents=0,
                value_metric="Produces design specs without writing code",
            ),
            RegisteredAgent(
                agent_id="agent-fe-builder",
                name="Frontend Engineer",
                owner="Website Build Pipeline",
                business_domain="Software Delivery",
                risk_tier="medium",
                autonomy_level=3,
                status="approved",
                model_provider="OpenAI/local fallback",
                allowed_tools=("rag.search_policy_memory", "deploy.vercel_release"),
                data_classes=("internal",),
                last_run_at="not_run_yet",
                monthly_cost_usd=54.0,
                open_incidents=0,
                value_metric="Implements UI via gateway-governed deploy tools",
            ),
            RegisteredAgent(
                agent_id="agent-be-builder",
                name="Backend Engineer",
                owner="Website Build Pipeline",
                business_domain="Software Delivery",
                risk_tier="medium",
                autonomy_level=3,
                status="approved",
                model_provider="OpenAI/local fallback",
                allowed_tools=("rag.search_policy_memory", "deploy.render_release"),
                data_classes=("internal", "confidential"),
                last_run_at="not_run_yet",
                monthly_cost_usd=58.0,
                open_incidents=0,
                value_metric="Implements APIs with policy-bound side effects",
            ),
            RegisteredAgent(
                agent_id="agent-review-deploy",
                name="Review & Deploy Agent",
                owner="Website Build Pipeline",
                business_domain="Software Delivery",
                risk_tier="high",
                autonomy_level=2,
                status="approved",
                model_provider="OpenAI/local fallback",
                allowed_tools=(
                    "rag.search_policy_memory",
                    "deploy.vercel_release",
                    "deploy.render_release",
                ),
                data_classes=("internal", "confidential"),
                last_run_at="not_run_yet",
                monthly_cost_usd=44.0,
                open_incidents=0,
                value_metric="Code review gate before staging/production deploy",
            ),
            RegisteredAgent(
                agent_id="venkat-ai-platform",
                name="Venkat AI Platform (VAP)",
                owner="AI Platform",
                business_domain="Multi-Agent Orchestration",
                risk_tier="medium",
                autonomy_level=3,
                status="pilot",
                model_provider="OpenRouter",
                allowed_tools=(
                    "rag.search_policy_memory",
                    "notify.slack",
                    "notify.telegram",
                    "notify.whatsapp",
                ),
                data_classes=("internal", "confidential"),
                last_run_at="not_run_yet",
                monthly_cost_usd=62.0,
                open_incidents=0,
                value_metric="Chief orchestration with gateway-governed delivery channels",
            ),
            RegisteredAgent(
                agent_id="enterprise-rag-platform",
                name="Enterprise RAG Platform",
                owner="Knowledge Engineering",
                business_domain="Governed Retrieval",
                risk_tier="medium",
                autonomy_level=2,
                status="pilot",
                model_provider="Extractive/local",
                allowed_tools=(
                    "rag.search_policy_memory",
                    "rag.ingest_document",
                    "rag.high_risk_answer",
                ),
                data_classes=("internal", "confidential", "restricted"),
                last_run_at="not_run_yet",
                monthly_cost_usd=28.0,
                open_incidents=0,
                value_metric="Access-aware retrieval with HITL on ingest and destructive queries",
            ),
            RegisteredAgent(
                agent_id="aegisloop-agentops",
                name="AegisLoop AgentOps Workbench",
                owner="AgentOps",
                business_domain="Mission Fleets",
                risk_tier="medium",
                autonomy_level=2,
                status="pilot",
                model_provider="OpenRouter/Ollama/local",
                allowed_tools=("mission.ship_artifact",),
                data_classes=("internal",),
                last_run_at="not_run_yet",
                monthly_cost_usd=18.0,
                open_incidents=0,
                value_metric="Mission eval gates with human-gated ship path",
            ),
        )

    def summary(self) -> dict[str, object]:
        agents = self.list_agents()
        return {
            "total_agents": len(agents),
            "approved_agents": sum(1 for agent in agents if agent.status == "approved"),
            "restricted_agents": sum(1 for agent in agents if agent.status == "restricted"),
            "pilot_agents": sum(1 for agent in agents if agent.status == "pilot"),
            "monthly_cost_usd": round(sum(agent.monthly_cost_usd for agent in agents), 2),
            "open_incidents": sum(agent.open_incidents for agent in agents),
            "high_or_critical_risk": sum(
                1 for agent in agents if agent.risk_tier in {"high", "critical"}
            ),
        }
