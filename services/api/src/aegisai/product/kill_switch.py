from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4


class KillSwitchStore(Protocol):
    def list_kill_switch_rules(self) -> list[dict[str, Any]]: ...

    def upsert_kill_switch_rule(self, rule: dict[str, Any]) -> None: ...

    def deactivate_kill_switch_rule(self, rule_id: str) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class KillSwitchRule:
    rule_id: str
    scope_type: str
    scope_value: str
    reason: str
    created_by: str
    active: bool
    created_at: str
    tenant_id: str = "bank-demo"
    deactivated_at: str | None = None


class KillSwitchService:
    """Emergency stop control for agents, tools, tenants, and workflows.

    Persists to the control-plane store when provided; otherwise in-memory only.
    """

    def __init__(self, store: KillSwitchStore | None = None) -> None:
        self._store = store
        self._rules: dict[str, KillSwitchRule] = {}
        if store is not None:
            self._load_from_store()

    def _load_from_store(self) -> None:
        assert self._store is not None
        for row in self._store.list_kill_switch_rules():
            rule = self._from_row(row)
            self._rules[rule.rule_id] = rule

    @staticmethod
    def _from_row(row: dict[str, Any]) -> KillSwitchRule:
        active = row.get("active")
        if isinstance(active, int):
            active = bool(active)
        return KillSwitchRule(
            rule_id=str(row["rule_id"]),
            tenant_id=str(row.get("tenant_id", "bank-demo")),
            scope_type=str(row["scope_type"]),
            scope_value=str(row["scope_value"]),
            reason=str(row["reason"]),
            created_by=str(row["created_by"]),
            active=bool(active),
            created_at=str(row["created_at"]),
            deactivated_at=str(row["deactivated_at"]) if row.get("deactivated_at") else None,
        )

    def _persist(self, rule: KillSwitchRule) -> None:
        if self._store is None:
            return
        self._store.upsert_kill_switch_rule(
            {
                "rule_id": rule.rule_id,
                "tenant_id": rule.tenant_id,
                "scope_type": rule.scope_type,
                "scope_value": rule.scope_value,
                "reason": rule.reason,
                "created_by": rule.created_by,
                "active": rule.active,
                "created_at": rule.created_at,
                "deactivated_at": rule.deactivated_at,
            }
        )

    def activate(
        self,
        scope_type: str,
        scope_value: str,
        reason: str,
        created_by: str,
        tenant_id: str = "bank-demo",
    ) -> KillSwitchRule:
        if scope_type not in {"agent", "tool", "tenant", "workflow"}:
            raise ValueError("scope_type must be agent, tool, tenant, or workflow")
        rule = KillSwitchRule(
            rule_id=f"kill-{uuid4()}",
            tenant_id=tenant_id,
            scope_type=scope_type,
            scope_value=scope_value,
            reason=reason,
            created_by=created_by,
            active=True,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._rules[rule.rule_id] = rule
        self._persist(rule)
        return rule

    def deactivate(self, rule_id: str) -> KillSwitchRule | None:
        if self._store is not None:
            row = self._store.deactivate_kill_switch_rule(rule_id)
            if row is None and rule_id not in self._rules:
                return None
            if row is not None:
                updated = self._from_row(row)
                self._rules[rule_id] = updated
                return updated
        rule = self._rules.get(rule_id)
        if rule is None:
            return None
        updated = KillSwitchRule(
            rule_id=rule.rule_id,
            tenant_id=rule.tenant_id,
            scope_type=rule.scope_type,
            scope_value=rule.scope_value,
            reason=rule.reason,
            created_by=rule.created_by,
            active=False,
            created_at=rule.created_at,
            deactivated_at=datetime.now(UTC).isoformat(),
        )
        self._rules[rule_id] = updated
        self._persist(updated)
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
            "persisted": self._store is not None,
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
            "tenant_id": rule.tenant_id,
            "scope_type": rule.scope_type,
            "scope_value": rule.scope_value,
            "reason": rule.reason,
            "created_by": rule.created_by,
            "active": rule.active,
            "created_at": rule.created_at,
            "deactivated_at": rule.deactivated_at,
        }
