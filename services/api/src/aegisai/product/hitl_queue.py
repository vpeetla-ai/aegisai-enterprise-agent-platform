"""HITL approval queue — list pending tasks and persist gateway-driven HITL."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import uuid4


class HitlStore(Protocol):
    def list_approval_tasks(
        self, tenant_id: str, *, status: str | None = "pending"
    ) -> list[dict[str, Any]]: ...

    def count_approval_tasks(
        self, tenant_id: str | None = None, *, status: str | None = "pending"
    ) -> int: ...

    def persist_gateway_hitl(self, **kwargs: Any) -> dict[str, Any]: ...


class HitlQueueService:
    def __init__(self, store: HitlStore) -> None:
        self._store = store

    def queue(self, tenant_id: str = "bank-demo", status: str = "pending") -> dict[str, object]:
        tasks = self._store.list_approval_tasks(tenant_id, status=status or None)
        return {
            "product_module": "HITL Queue",
            "headline": "Review agent tool calls before side effects execute.",
            "tenant_id": tenant_id,
            "status_filter": status,
            "total": len(tasks),
            "pending_count": self._store.count_approval_tasks(tenant_id, status="pending"),
            "tasks": tasks,
        }

    def persist_from_gateway_event(
        self,
        *,
        tenant_id: str,
        run_id: str,
        agent_id: str,
        tool_name: str,
        action_type: str,
        target_system: str,
        workflow_type: str,
        gateway_decision: str,
        business_explanation: str = "",
    ) -> dict[str, Any] | None:
        if gateway_decision != "approval_required":
            return None
        proposal_id = f"prop-{uuid4().hex[:12]}"
        case_id = f"case-{run_id}"
        return self._store.persist_gateway_hitl(
            tenant_id=tenant_id,
            case_id=case_id,
            proposal_id=proposal_id,
            agent_id=agent_id,
            action_type=action_type,
            target_system=target_system,
            tool_name=tool_name,
            workflow_type=workflow_type,
            approval_role="workflow_owner",
            business_explanation=business_explanation,
        )


def due_at_iso(hours: int = 24) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()
