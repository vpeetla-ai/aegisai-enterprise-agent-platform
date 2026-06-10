from __future__ import annotations

from .agent_registry import AgentRegistryService


class FinOpsService:
    """Cost visibility and anomaly signals per agent for executive and platform buyers."""

    def __init__(self, agent_registry: AgentRegistryService) -> None:
        self.agent_registry = agent_registry

    def dashboard(self) -> dict[str, object]:
        agents = self.agent_registry.list_agents()
        total_cost = sum(agent.monthly_cost_usd for agent in agents)
        average_cost = round(total_cost / len(agents), 2) if agents else 0.0
        anomalies = []
        for agent in agents:
            if agent.monthly_cost_usd > max(5000, average_cost * 2.5):
                anomalies.append(
                    {
                        "agent_id": agent.agent_id,
                        "name": agent.name,
                        "monthly_cost_usd": agent.monthly_cost_usd,
                        "severity": "high",
                        "reason": "Cost exceeds 2.5x fleet average or $5k threshold.",
                        "recommended_action": "Review tool usage, model tier, and eval regression.",
                    }
                )
            if agent.open_incidents > 0 and agent.monthly_cost_usd > 1000:
                anomalies.append(
                    {
                        "agent_id": agent.agent_id,
                        "name": agent.name,
                        "monthly_cost_usd": agent.monthly_cost_usd,
                        "severity": "medium",
                        "reason": "Open incidents with elevated spend.",
                        "recommended_action": "Enable kill switch and run red-team eval suite.",
                    }
                )
        return {
            "product_module": "FinOps",
            "total_monthly_cost_usd": total_cost,
            "average_cost_per_agent_usd": average_cost,
            "agent_count": len(agents),
            "anomaly_count": len(anomalies),
            "roi": {
                "estimated_review_minutes_saved": 420,
                "estimated_loss_prevented_usd": 18750,
                "average_cost_per_governed_workflow_usd": 0.18,
                "autonomy_roi_score": 82,
                "business_value_summary": (
                    "AegisAI ties model, token, retrieval, tool, and review cost to governed "
                    "workflow outcomes instead of only reporting raw LLM spend."
                ),
            },
            "cost_by_agent": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "owner": agent.owner,
                    "monthly_cost_usd": agent.monthly_cost_usd,
                    "risk_tier": agent.risk_tier,
                    "value_metric": agent.value_metric,
                }
                for agent in sorted(agents, key=lambda item: item.monthly_cost_usd, reverse=True)
            ],
            "anomalies": anomalies,
            "executive_summary": (
                f"Fleet spend is ${total_cost}/month across {len(agents)} registered agents. "
                f"{len(anomalies)} cost or incident anomalies need review."
            ),
        }
