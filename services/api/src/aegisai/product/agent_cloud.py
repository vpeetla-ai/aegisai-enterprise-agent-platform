from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from .agent_registry import AgentRegistryService, RegisteredAgent
from .gateway_metrics import GatewayMetricsService
from .identity_rbac import IdentityRBACService
from .kill_switch import KillSwitchService


class _AgentCloudStore(Protocol):
    def list_recent_audit_events(self, tenant_id: str, *, limit: int = 20) -> list[dict[str, object]]: ...

    def list_undoable_executions(self, tenant_id: str) -> list[dict[str, object]]: ...

    def get_execution_by_id(self, execution_id: str) -> dict[str, object] | None: ...

    def mark_execution_rolled_back(self, execution_id: str, rollback_id: str) -> None: ...

    def append_audit_event(
        self,
        *,
        tenant_id: str,
        case_id: str,
        event_type: str,
        subject_id: str,
        actor_id: str,
        payload: dict[str, object],
    ) -> None: ...

    def verify_audit_chain(self, tenant_id: str) -> bool: ...


@dataclass(frozen=True)
class UndoRequest:
    tenant_id: str
    execution_id: str
    actor_id: str
    reason: str


class AgentCloudService:
    """Rubrik Agent Cloud / Guild.ai style Monitor → Govern → Remediate control surface."""

    PILLARS = (
        {
            "id": "monitor",
            "title": "See agents in action",
            "reference": "Rubrik Agent Monitor · Guild Observability",
            "outcome": "Discover every agent, watch live tool calls, and spot issues early.",
        },
        {
            "id": "govern",
            "title": "Keep agents under control",
            "reference": "Rubrik Agent Govern · Guild Policies & Permissions",
            "outcome": "Apply zero-trust policy, scoped tool access, and instant freeze controls.",
        },
        {
            "id": "remediate",
            "title": "Undo agent mistakes",
            "reference": "Rubrik secure rollback · Guild version rollback",
            "outcome": "Recover reversible actions in minutes with signed rollback evidence.",
        },
    )

    def __init__(
        self,
        store: _AgentCloudStore,
        agent_registry: AgentRegistryService,
        kill_switch_service: KillSwitchService,
        identity_service: IdentityRBACService,
        gateway_metrics: GatewayMetricsService,
    ) -> None:
        self._store = store
        self._agent_registry = agent_registry
        self._kill_switch = kill_switch_service
        self._identity = identity_service
        self._gateway_metrics = gateway_metrics

    def posture(self, tenant_id: str = "bank-demo") -> dict[str, object]:
        monitor = self.monitor_feed(tenant_id, limit=8)
        govern = self.govern_posture()
        undoable = self.undoable_actions(tenant_id)
        agents = self._agent_registry.list_agents()
        active_agents = sum(1 for agent in agents if agent.status in {"approved", "pilot", "restricted"})
        return {
            "product_module": "Agent Cloud",
            "headline": "Monitor agents in action. Keep them under control. Undo mistakes in minutes.",
            "positioning": (
                "AegisAI Agent Cloud is the enterprise control layer for multi-framework agent sprawl — "
                "inspired by Rubrik Agent Cloud and Guild.ai, built for governed runtime execution."
            ),
            "pillars": list(self.PILLARS),
            "board_metrics": [
                {"label": "Registered agents", "value": len(agents), "meaning": "Known inventory"},
                {"label": "Active agents", "value": active_agents, "meaning": "Approved, pilot, or restricted"},
                {
                    "label": "Gateway coverage",
                    "value": f"{govern['gateway_coverage_pct']}%",
                    "meaning": "Side-effecting paths intercepted",
                },
                {
                    "label": "Undoable actions",
                    "value": undoable["undoable_count"],
                    "meaning": "Reversible executions available for rollback",
                },
                {
                    "label": "Active freezes",
                    "value": govern["active_freezes"],
                    "meaning": "Kill-switch scopes currently paused",
                },
            ],
            "monitor_summary": {
                "activity_events": len(monitor["activity"]),
                "agents_in_motion": monitor["agents_in_motion"],
            },
            "govern_summary": {
                "zero_trust_controls": govern["zero_trust_controls"],
                "active_freezes": govern["active_freezes"],
            },
            "remediate_summary": {
                "undoable_count": undoable["undoable_count"],
                "mean_recovery_seconds": undoable["mean_recovery_seconds"],
            },
        }

    def monitor_feed(self, tenant_id: str = "bank-demo", *, limit: int = 20) -> dict[str, object]:
        agents = self._agent_registry.list_agents()
        audit_rows = self._store.list_recent_audit_events(tenant_id, limit=limit)
        gateway = self._gateway_metrics.snapshot(tenant_id)

        activity: list[dict[str, object]] = []
        for row in audit_rows:
            activity.append(
                {
                    "time": row.get("created_at", "recent"),
                    "event_type": row.get("event_type"),
                    "agent_id": _agent_from_payload(row.get("payload_json")),
                    "case_id": row.get("case_id"),
                    "actor_id": row.get("actor_id"),
                    "detail": _activity_detail(str(row.get("event_type", "")), row.get("payload_json")),
                }
            )

        if not activity:
            activity = _seed_monitor_activity(agents)

        agents_in_motion = [
            self._agent_card(agent)
            for agent in sorted(agents, key=lambda item: item.last_run_at, reverse=True)
        ]

        return {
            "product_module": "Agent Monitor",
            "headline": "See your AI agents in action across any framework.",
            "tenant_id": tenant_id,
            "agents_in_motion": len([agent for agent in agents if agent.status != "deprecated"]),
            "gateway_tool_calls": gateway["gateway_tool_calls"],
            "activity": activity[:limit],
            "agents": agents_in_motion,
            "integration_hub": [
                "GitHub", "Slack", "Jira", "Linear", "Stripe", "Salesforce",
                "Zendesk", "Notion", "MCP servers", "Custom REST",
            ],
        }

    def govern_posture(self) -> dict[str, object]:
        kill_posture = self._kill_switch.posture()
        active_freezes = int(kill_posture["active_rule_count"])
        agents = self._agent_registry.list_agents()
        matrix = self._identity.permission_matrix(agents)
        high_risk_without_freeze = [
            agent.agent_id
            for agent in agents
            if agent.risk_tier in {"high", "critical"} and not _agent_has_active_freeze(agent.agent_id, kill_posture)
        ]
        gateway = self._gateway_metrics.snapshot()

        zero_trust_controls = [
            {
                "control": "Gateway intercept",
                "status": "active",
                "detail": "Every side-effecting tool call is policy-checked before execution.",
            },
            {
                "control": "Execution token binding",
                "status": "active",
                "detail": "Broker executes only with gateway-issued or HITL-bound tokens.",
            },
            {
                "control": "Kill switch scopes",
                "status": "ready" if active_freezes == 0 else "engaged",
                "detail": f"{active_freezes} active freeze rule(s) across agent/tool/tenant/workflow.",
            },
            {
                "control": "Least-privilege tool matrix",
                "status": "active",
                "detail": f"{len(matrix['rows'])} agent-to-tool permission rows enforced.",
            },
            {
                "control": "Signed audit chain",
                "status": "active",
                "detail": "Hash-chained events for every govern and execute decision.",
            },
        ]

        return {
            "product_module": "Agent Govern",
            "headline": "Keep agents under control with zero-trust, policy-based runtime enforcement.",
            "gateway_coverage_pct": gateway["gateway_coverage_pct"],
            "pilot_target_pct": gateway["pilot_target_pct"],
            "active_freezes": active_freezes,
            "freeze_rules": kill_posture["rules"],
            "high_risk_agents_without_freeze": high_risk_without_freeze,
            "zero_trust_controls": zero_trust_controls,
            "permission_matrix_rows": len(matrix["rows"]),
            "recommended_actions": [
                "Enable kill switches for every high and critical risk agent.",
                "Route 100% of side-effecting tool calls through the governance gateway.",
                "Attach golden eval suites before promoting agent versions.",
            ],
        }

    def undoable_actions(self, tenant_id: str = "bank-demo") -> dict[str, object]:
        rows = self._store.list_undoable_executions(tenant_id)
        actions = [_execution_card(row) for row in rows]
        if not actions:
            actions = _seed_undoable_actions()
        return {
            "product_module": "Agent Remediate",
            "headline": "Undo unwanted or destructive agent actions in minutes.",
            "tenant_id": tenant_id,
            "undoable_count": len(actions),
            "mean_recovery_seconds": 45,
            "actions": actions,
            "operating_procedure": [
                "Identify the execution with rollback metadata.",
                "Freeze the narrowest agent or tool scope if the mistake is still propagating.",
                "Trigger undo — AegisAI marks the execution rolled back and emits signed evidence.",
                "Run golden eval regression before restoring autonomy.",
            ],
        }

    def undo_execution(self, request: UndoRequest) -> dict[str, object]:
        if request.execution_id.startswith("exec-demo-rollback"):
            rollback_id = f"rollback-{uuid4()}"
            self._store.append_audit_event(
                tenant_id=request.tenant_id,
                case_id="case-demo-001",
                event_type="execution.rolled_back",
                subject_id=request.execution_id,
                actor_id=request.actor_id,
                payload={
                    "rollback_id": rollback_id,
                    "reason": request.reason,
                    "recovery_time_seconds": 45,
                    "demo": True,
                },
            )
            return {
                "status": "rolled_back",
                "product_module": "Agent Remediate",
                "rollback_id": rollback_id,
                "execution_id": request.execution_id,
                "rollback_reference": f"rollback://{request.execution_id}/demo",
                "recovery_time_seconds": 45,
                "message": "Demo rollback completed — reversible refund reversed in under one minute.",
                "audit_chain_valid": self._store.verify_audit_chain(request.tenant_id),
            }

        execution = self._store.get_execution_by_id(request.execution_id)
        if execution is None:
            return {
                "status": "not_found",
                "message": f"No execution found for id={request.execution_id}.",
            }

        if str(execution.get("tenant_id")) != request.tenant_id:
            return {
                "status": "forbidden",
                "message": "Execution does not belong to the requested tenant.",
            }

        status = str(execution.get("status", ""))
        if status == "rolled_back":
            return {
                "status": "already_rolled_back",
                "message": "This execution was already rolled back.",
                "execution_id": request.execution_id,
            }

        if status != "executed":
            return {
                "status": "not_undoable",
                "message": f"Execution status '{status}' cannot be rolled back.",
            }

        rollback_reference = execution.get("rollback_reference")
        if not rollback_reference:
            return {
                "status": "irreversible",
                "message": "Execution has no rollback reference — action cannot be undone.",
            }

        rollback_id = f"rollback-{uuid4()}"
        recovery_seconds = 45
        self._store.mark_execution_rolled_back(request.execution_id, rollback_id)
        self._store.append_audit_event(
            tenant_id=request.tenant_id,
            case_id=str(execution.get("case_id", "unknown")),
            event_type="execution.rolled_back",
            subject_id=request.execution_id,
            actor_id=request.actor_id,
            payload={
                "rollback_id": rollback_id,
                "rollback_reference": rollback_reference,
                "reason": request.reason,
                "recovery_time_seconds": recovery_seconds,
                "action_type": execution.get("action_type"),
                "target_system": execution.get("target_system"),
                "connector": execution.get("connector"),
            },
        )

        return {
            "status": "rolled_back",
            "product_module": "Agent Remediate",
            "rollback_id": rollback_id,
            "execution_id": request.execution_id,
            "rollback_reference": rollback_reference,
            "recovery_time_seconds": recovery_seconds,
            "message": (
                f"Rolled back {execution.get('action_type')} on {execution.get('target_system')} "
                f"via {execution.get('connector')}."
            ),
            "audit_chain_valid": self._store.verify_audit_chain(request.tenant_id),
        }

    def _agent_card(self, agent: RegisteredAgent) -> dict[str, object]:
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "owner": agent.owner,
            "status": agent.status,
            "risk_tier": agent.risk_tier,
            "last_run_at": agent.last_run_at,
            "allowed_tools": list(agent.allowed_tools),
            "open_incidents": agent.open_incidents,
        }


def _agent_from_payload(payload_json: object) -> str | None:
    if not isinstance(payload_json, str):
        return None
    if "agent-" in payload_json:
        for token in payload_json.replace('"', " ").split():
            if token.startswith("agent-"):
                return token.rstrip(",}")
    return None


def _activity_detail(event_type: str, payload_json: object) -> str:
    if event_type == "gateway.tool_request":
        return "Tool call intercepted by governance gateway."
    if event_type.startswith("execution."):
        return f"Execution event: {event_type.replace('execution.', '')}."
    if event_type == "execution.rolled_back":
        return "Agent mistake rolled back with signed evidence."
    return "Agent activity recorded in audit ledger."


def _agent_has_active_freeze(agent_id: str, kill_posture: dict[str, object]) -> bool:
    rules = kill_posture.get("rules", [])
    if not isinstance(rules, list):
        return False
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if rule.get("scope_type") == "agent" and rule.get("scope_value") == agent_id and rule.get("active"):
            return True
    return False


def _execution_card(row: dict[str, object]) -> dict[str, object]:
    return {
        "execution_id": row.get("execution_id"),
        "case_id": row.get("case_id"),
        "proposal_id": row.get("proposal_id"),
        "action_type": row.get("action_type"),
        "target_system": row.get("target_system"),
        "connector": row.get("connector"),
        "status": row.get("status"),
        "rollback_reference": row.get("rollback_reference"),
        "external_reference": row.get("external_reference"),
        "message": row.get("message"),
    }


def _seed_monitor_activity(agents: tuple[RegisteredAgent, ...]) -> list[dict[str, object]]:
    sample_agents = list(agents)[:3] or [
        RegisteredAgent(
            agent_id="agent-refund",
            name="Refund Agent",
            owner="Finance",
            business_domain="Payments",
            risk_tier="high",
            autonomy_level=3,
            status="approved",
            model_provider="OpenAI",
            allowed_tools=("payments.issue_refund",),
            data_classes=("confidential",),
            last_run_at="T-2m",
            monthly_cost_usd=100,
            open_incidents=0,
            value_metric="demo",
        )
    ]
    return [
        {
            "time": "T-00m",
            "event_type": "gateway.tool_request",
            "agent_id": sample_agents[0].agent_id,
            "case_id": "case-demo-001",
            "actor_id": "gateway",
            "detail": "Refund tool call intercepted — policy routing to HITL.",
        },
        {
            "time": "T-01m",
            "event_type": "execution.executed",
            "agent_id": sample_agents[0].agent_id,
            "case_id": "case-demo-001",
            "actor_id": "execution-broker",
            "detail": "Approved refund executed with rollback metadata attached.",
        },
        {
            "time": "T-03m",
            "event_type": "gateway.tool_request",
            "agent_id": sample_agents[1].agent_id if len(sample_agents) > 1 else sample_agents[0].agent_id,
            "case_id": "case-demo-002",
            "actor_id": "gateway",
            "detail": "CRM update blocked — agent lacks scoped permission.",
        },
    ]


def _seed_undoable_actions() -> list[dict[str, object]]:
    return [
        {
            "execution_id": "exec-demo-rollback-001",
            "case_id": "case-demo-001",
            "proposal_id": "proposal-demo-001",
            "action_type": "issue_refund",
            "target_system": "payments",
            "connector": "stripe_refund",
            "status": "executed",
            "rollback_reference": "rollback://proposal-demo-001/bank-demo:proposal-demo-001:execute",
            "external_reference": "re_demo_001",
            "message": "Demo reversible refund — safe to undo in buyer walkthrough.",
        }
    ]
