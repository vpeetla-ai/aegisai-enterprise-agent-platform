from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from aegisai.application.execution.connectors import ConnectorExecutionContext, ConnectorRegistry
from aegisai.domain import Decision, ExecutionCommand, ExecutionResult, ExecutionStatus


@dataclass(frozen=True)
class ExecutionReadiness:
    action_type: str
    target_system: str
    amount_usd: float
    reversible: bool
    decision: str
    approval_status: str | None


class ApprovedActionExecutionBroker:
    """Executes only approved actions via pluggable enterprise connectors (any system, not Stripe-only)."""

    def __init__(self, connector_registry: ConnectorRegistry | None = None) -> None:
        self.connector_registry = connector_registry or ConnectorRegistry()

    def execute(
        self,
        command: ExecutionCommand,
        readiness: ExecutionReadiness | None,
        tool_name: str | None = None,
    ) -> ExecutionResult:
        if readiness is None:
            return self._non_executed(
                command,
                status=ExecutionStatus.FAILED,
                target_system="unknown",
                action_type="unknown",
                message="No persisted action proposal exists for this tenant and proposal_id.",
            )

        if readiness.decision == Decision.BLOCK.value:
            return self._non_executed(
                command,
                status=ExecutionStatus.BLOCKED,
                target_system=readiness.target_system,
                action_type=readiness.action_type,
                message="Execution blocked by policy decision.",
            )

        approved_by_policy = readiness.decision == Decision.AUTO_APPROVE.value
        approved_by_human = readiness.approval_status == "approved"
        if not (approved_by_policy or approved_by_human):
            return self._non_executed(
                command,
                status=ExecutionStatus.REQUIRES_APPROVAL,
                target_system=readiness.target_system,
                action_type=readiness.action_type,
                message="Execution requires an approved HITL task or auto-approval decision.",
            )

        resolved_tool = tool_name or _default_tool_name(readiness.action_type, readiness.target_system)
        connector = self.connector_registry.resolve(
            resolved_tool,
            readiness.target_system,
            readiness.action_type,
        )
        if connector is None:
            return self._non_executed(
                command,
                status=ExecutionStatus.FAILED,
                target_system=readiness.target_system,
                action_type=readiness.action_type,
                message=(
                    f"No connector registered for tool={resolved_tool}, "
                    f"system={readiness.target_system}, action={readiness.action_type}."
                ),
            )

        outcome = connector.execute(
            ConnectorExecutionContext(
                tenant_id=command.tenant_id,
                case_id=command.case_id,
                proposal_id=command.proposal_id,
                action_type=readiness.action_type,
                target_system=readiness.target_system,
                amount_usd=readiness.amount_usd,
                idempotency_key=command.idempotency_key,
                dry_run=command.dry_run,
            )
        )
        rollback_reference = (
            f"rollback://{command.proposal_id}/{command.idempotency_key}"
            if readiness.reversible
            else None
        )
        return ExecutionResult(
            execution_id=f"exec-{uuid4()}",
            tenant_id=command.tenant_id,
            case_id=command.case_id,
            proposal_id=command.proposal_id,
            status=ExecutionStatus.EXECUTED,
            target_system=readiness.target_system,
            action_type=readiness.action_type,
            connector=outcome.connector_id,
            idempotency_key=command.idempotency_key,
            external_reference=outcome.external_reference,
            rollback_reference=rollback_reference,
            message=outcome.message,
        )

    def _non_executed(
        self,
        command: ExecutionCommand,
        status: ExecutionStatus,
        target_system: str,
        action_type: str,
        message: str,
    ) -> ExecutionResult:
        return ExecutionResult(
            execution_id=f"exec-{uuid4()}",
            tenant_id=command.tenant_id,
            case_id=command.case_id,
            proposal_id=command.proposal_id,
            status=status,
            target_system=target_system,
            action_type=action_type,
            connector="none",
            idempotency_key=command.idempotency_key,
            external_reference=None,
            rollback_reference=None,
            message=message,
        )


def _default_tool_name(action_type: str, target_system: str) -> str:
    if target_system == "payments" and action_type == "issue_refund":
        return "payments.issue_refund"
    if target_system == "customer_data_platform":
        return "privacy.modify_or_delete_data"
    if target_system == "infrastructure":
        return "infra.change_production_configuration"
    return f"{target_system}.{action_type}"
