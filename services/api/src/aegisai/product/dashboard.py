from __future__ import annotations

from typing import Protocol

from .agent_registry import AgentRegistryService
from .finops import FinOpsService
from .gateway_metrics import GatewayMetricsService
from .kill_switch import KillSwitchService


class _MetricsStore(Protocol):
    def count_audit_events(
        self,
        tenant_id: str,
        *,
        event_type: str | None = None,
        event_type_prefix: str | None = None,
    ) -> int: ...

    def count(self, table: str) -> int: ...


class DashboardService:
    """Executive Main Dashboard — Rubrik/Guild-style at-a-glance control plane."""

    def __init__(
        self,
        store: _MetricsStore,
        agent_registry: AgentRegistryService,
        gateway_metrics: GatewayMetricsService,
        finops: FinOpsService,
        kill_switch: KillSwitchService,
    ) -> None:
        self._store = store
        self._registry = agent_registry
        self._gateway = gateway_metrics
        self._finops = finops
        self._kill_switch = kill_switch

    def summary(self, tenant_id: str = "bank-demo") -> dict[str, object]:
        registry = self._registry.summary()
        gateway = self._gateway.snapshot(tenant_id)
        finops = self._finops.dashboard()
        freezes = int(self._kill_switch.posture()["active_rule_count"])
        if hasattr(self._store, "count_approval_tasks"):
            pending_hitl = self._store.count_approval_tasks(tenant_id, status="pending")  # type: ignore[attr-defined]
        else:
            pending_hitl = self._store.count("approval_tasks")
        open_incidents = int(registry["open_incidents"])

        tiles = [
            {
                "id": "agents",
                "label": "Agents onboarded",
                "value": registry["total_agents"],
                "delta": f"{registry['approved_agents']} approved · {registry['pilot_agents']} pilot",
                "status": "healthy" if registry["total_agents"] > 0 else "warning",
                "module": "agents",
            },
            {
                "id": "token_cost",
                "label": "Monthly token cost",
                "value": f"${finops.get('total_monthly_cost_usd', registry['monthly_cost_usd'])}",
                "delta": f"{finops.get('anomaly_count', 0)} cost anomalies",
                "status": "healthy" if finops.get("anomaly_count", 0) == 0 else "warning",
                "module": "finops",
            },
            {
                "id": "gateway",
                "label": "Gateway coverage",
                "value": f"{gateway['gateway_coverage_pct']}%",
                "delta": f"Target {gateway['pilot_target_pct']}%",
                "status": "healthy" if float(gateway["gateway_coverage_pct"]) >= 80 else "warning",
                "module": "gateway",
            },
            {
                "id": "hitl",
                "label": "HITL queue",
                "value": pending_hitl,
                "delta": f"{self._store.count('governance_decisions')} decisions logged",
                "status": "healthy" if pending_hitl == 0 else "attention",
                "module": "hitl",
            },
            {
                "id": "risk",
                "label": "High-risk agents",
                "value": registry["high_or_critical_risk"],
                "delta": f"{open_incidents} open incidents",
                "status": "healthy" if registry["high_or_critical_risk"] <= 2 else "attention",
                "module": "governance",
            },
            {
                "id": "freezes",
                "label": "Active freezes",
                "value": freezes,
                "delta": "Kill-switch scopes engaged" if freezes else "No active freezes",
                "status": "attention" if freezes else "healthy",
                "module": "incidents",
            },
            {
                "id": "executions",
                "label": "Broker executions",
                "value": gateway["broker_executions"],
                "delta": f"{gateway['executions_with_token']} token-bound",
                "status": "healthy",
                "module": "governance",
            },
            {
                "id": "orchestrators",
                "label": "Managed orchestrators",
                "value": 3,
                "delta": "Content · Stock · Website Build",
                "status": "healthy",
                "module": "orchestrators",
            },
        ]

        posture_score = max(
            0,
            100
            - int(registry["high_or_critical_risk"]) * 6
            - open_incidents * 10
            - freezes * 8
            - pending_hitl * 4,
        )

        return {
            "product_module": "Main Dashboard",
            "headline": "Agent Governance Control Plane",
            "tenant_id": tenant_id,
            "posture_score": posture_score,
            "tiles": tiles,
            "quick_actions": [
                {"id": "gateway", "label": "AI Gateway", "module": "gateway"},
                {"id": "onboard", "label": "Onboard agent", "module": "onboard"},
                {"id": "policy", "label": "Policy studio", "module": "governance"},
                {"id": "orchestrators", "label": "View orchestrators", "module": "orchestrators"},
            ],
        }
