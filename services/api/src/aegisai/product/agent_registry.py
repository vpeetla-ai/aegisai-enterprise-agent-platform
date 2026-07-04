from __future__ import annotations

from aegisai.infrastructure.persistence.agent_registry_store import (
    AgentRegistryStore,
    InMemoryAgentRegistryStore,
)
from aegisai.domain.models import RegisteredAgent

__all__ = ["AgentRegistryService", "RegisteredAgent"]


class AgentRegistryService:
    """Product-facing inventory of governed enterprise agents."""

    def __init__(self, store: AgentRegistryStore | None = None) -> None:
        self._store: AgentRegistryStore = store or InMemoryAgentRegistryStore()

    def list_agents(self) -> tuple[RegisteredAgent, ...]:
        return self._store.list_agents()

    def get_agent(self, agent_id: str) -> RegisteredAgent | None:
        return self._store.get_agent(agent_id)

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
        return self._store.upsert_agent(agent)

    def update_agent_status(self, agent_id: str, status: str) -> RegisteredAgent | None:
        return self._store.update_status(agent_id, status)

    def record_usage(self, agent_id: str, cost_usd: float) -> RegisteredAgent | None:
        """Write-through real cost from agent-finops into monthly_cost_usd, replacing
        whatever seed value was there — see ADR-011 (agent-finops)."""
        agent = self.get_agent(agent_id)
        if agent is None:
            return None
        return self._store.update_cost(agent_id, agent.monthly_cost_usd + cost_usd)

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
            "budget_usd": agent.budget_usd,
        }

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
