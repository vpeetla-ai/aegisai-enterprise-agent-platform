from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True)
class KillSwitchRule:
    rule_id: str
    scope_type: str
    scope_value: str
    reason: str
    created_by: str
    active: bool
    created_at: str


class KillSwitchService:
    """In-memory emergency stop control for agents, tools, tenants, and workflows."""

    def __init__(self) -> None:
        self._rules: dict[str, KillSwitchRule] = {}

    def activate(
        self,
        scope_type: str,
        scope_value: str,
        reason: str,
        created_by: str,
    ) -> KillSwitchRule:
        if scope_type not in {"agent", "tool", "tenant", "workflow"}:
            raise ValueError("scope_type must be agent, tool, tenant, or workflow")
        rule = KillSwitchRule(
            rule_id=f"kill-{uuid4()}",
            scope_type=scope_type,
            scope_value=scope_value,
            reason=reason,
            created_by=created_by,
            active=True,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._rules[rule.rule_id] = rule
        return rule

    def deactivate(self, rule_id: str) -> KillSwitchRule | None:
        rule = self._rules.get(rule_id)
        if rule is None:
            return None
        updated = KillSwitchRule(
            rule_id=rule.rule_id,
            scope_type=rule.scope_type,
            scope_value=rule.scope_value,
            reason=rule.reason,
            created_by=rule.created_by,
            active=False,
            created_at=rule.created_at,
        )
        self._rules[rule_id] = updated
        return updated

    def active_rules(self) -> tuple[KillSwitchRule, ...]:
        return tuple(rule for rule in self._rules.values() if rule.active)

    def is_blocked(
        self,
        tenant_id: str,
        tool_name: str | None = None,
        agent_id: str | None = None,
        workflow_type: str | None = None,
    ) -> KillSwitchRule | None:
        checks = {
            "tenant": tenant_id,
            "tool": tool_name,
            "agent": agent_id,
            "workflow": workflow_type,
        }
        for rule in self.active_rules():
            if checks.get(rule.scope_type) == rule.scope_value:
                return rule
        return None

    def posture(self) -> dict[str, object]:
        active = self.active_rules()
        return {
            "product_module": "Incident Response",
            "active_rule_count": len(active),
            "rules": [self._payload(rule) for rule in self._rules.values()],
        }

    def incident_timeline(self) -> dict[str, object]:
        active = self.active_rules()
        if not active:
            demo_events = [
                {
                    "event": "anomaly.detected",
                    "time": "T+00m",
                    "detail": "Payment connector anomaly detected for high-value refund workflow.",
                },
                {
                    "event": "kill_switch.ready",
                    "time": "T+01m",
                    "detail": "AegisAI can freeze agent, tool, tenant, or workflow scope.",
                },
                {
                    "event": "blocked_calls.observable",
                    "time": "T+02m",
                    "detail": "Gateway metrics and audit packets show every blocked call.",
                },
                {
                    "event": "unfreeze.requires_approval",
                    "time": "T+review",
                    "detail": "Security owner must document remediation before reactivation.",
                },
            ]
        else:
            demo_events = [
                {
                    "event": "kill_switch.activated",
                    "time": rule.created_at,
                    "detail": f"{rule.scope_type}:{rule.scope_value} frozen by {rule.created_by}.",
                }
                for rule in active
            ]
        return {
            "product_module": "Incident Timeline",
            "headline": "Freeze, investigate, remediate, and unfreeze agent runtime scope.",
            "active_incidents": len(active),
            "events": demo_events,
            "operating_procedure": [
                "Freeze the narrowest agent/tool/tenant/workflow scope possible.",
                "Notify owner, security, risk, and operations approver.",
                "Review blocked calls, audit packets, policy version, and connector health.",
                "Run red-team and golden eval regressions before unfreezing.",
                "Require documented remediation and approval to unfreeze.",
            ],
        }

    @staticmethod
    def _payload(rule: KillSwitchRule) -> dict[str, object]:
        return {
            "rule_id": rule.rule_id,
            "scope_type": rule.scope_type,
            "scope_value": rule.scope_value,
            "reason": rule.reason,
            "created_by": rule.created_by,
            "active": rule.active,
            "created_at": rule.created_at,
        }
