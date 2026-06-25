from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from aegisai.domain import ExecutionCommand

from .stripe_refund import StripeRefundConnector, StripeRefundRequest


@dataclass(frozen=True)
class ConnectorExecutionContext:
    tenant_id: str
    case_id: str
    proposal_id: str
    action_type: str
    target_system: str
    amount_usd: float
    idempotency_key: str
    dry_run: bool


@dataclass(frozen=True)
class ConnectorExecutionResult:
    connector_id: str
    external_reference: str
    message: str
    provider: str


class EnterpriseConnector(Protocol):
    """Any side-effecting system adapter (payments, CRM, ITSM, data, MCP tool, custom HTTP)."""

    connector_id: str
    provider: str
    supported_tools: tuple[str, ...]

    def can_handle(self, tool_name: str, target_system: str, action_type: str) -> bool: ...

    def execute(self, context: ConnectorExecutionContext) -> ConnectorExecutionResult: ...


class GenericEnterpriseConnector:
    """Deterministic connector for any registered target system (portfolio + custom integrations)."""

    def __init__(
        self,
        connector_id: str,
        provider: str,
        target_systems: tuple[str, ...],
        tool_names: tuple[str, ...] = (),
    ) -> None:
        self.connector_id = connector_id
        self.provider = provider
        self._target_systems = target_systems
        self.supported_tools = tool_names

    def can_handle(self, tool_name: str, target_system: str, action_type: str) -> bool:
        if tool_name and tool_name in self.supported_tools:
            return True
        return target_system in self._target_systems

    def execute(self, context: ConnectorExecutionContext) -> ConnectorExecutionResult:
        if context.dry_run:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"{context.target_system}://dry-run/{uuid4()}",
                message="Dry-run only; connector not invoked.",
                provider=self.provider,
            )
        return ConnectorExecutionResult(
            connector_id=self.connector_id,
            external_reference=f"{self.provider}://{context.target_system}/{uuid4()}",
            message=f"Approved action executed via {self.provider} connector.",
            provider=self.provider,
        )


class StripePaymentsConnector:
    """Optional live payments adapter — one of many connectors, not the product."""

    connector_id = "payments_refund_connector"
    provider = "stripe"
    supported_tools = ("payments.issue_refund",)

    def __init__(self, stripe: StripeRefundConnector | None = None) -> None:
        self._stripe = stripe or StripeRefundConnector()

    def can_handle(self, tool_name: str, target_system: str, action_type: str) -> bool:
        return (
            tool_name == "payments.issue_refund"
            or (target_system == "payments" and action_type == "issue_refund")
        )

    def execute(self, context: ConnectorExecutionContext) -> ConnectorExecutionResult:
        if context.dry_run:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"stripe://dry-run/{uuid4()}",
                message="Dry-run only; Stripe not invoked.",
                provider=self.provider,
            )
        refund = self._stripe.issue_refund(
            StripeRefundRequest(
                amount_usd=context.amount_usd,
                currency="usd",
                charge_id=None,
                idempotency_key=context.idempotency_key,
            )
        )
        return ConnectorExecutionResult(
            connector_id=self.connector_id,
            external_reference=f"stripe://refunds/{refund.refund_id}",
            message=f"{refund.message} (mode={refund.mode})",
            provider=self.provider,
        )


class ConnectorRegistry:
    """Routes approved executions to the right enterprise system — payments is just one entry."""

    def __init__(self, connectors: tuple[EnterpriseConnector, ...] | None = None) -> None:
        self._builtin_connectors = connectors or default_connector_registry()
        self._registered_connectors: list[EnterpriseConnector] = []

    def register_connector(self, connector: EnterpriseConnector) -> None:
        self.unregister(connector.connector_id)
        self._registered_connectors.append(connector)

    def unregister(self, connector_id: str) -> bool:
        before = len(self._registered_connectors)
        self._registered_connectors = [
            item for item in self._registered_connectors if item.connector_id != connector_id
        ]
        return len(self._registered_connectors) < before

    def _all_connectors(self) -> tuple[EnterpriseConnector, ...]:
        return self._builtin_connectors + tuple(self._registered_connectors)

    def resolve(
        self,
        tool_name: str,
        target_system: str,
        action_type: str,
    ) -> EnterpriseConnector | None:
        search_order = tuple(reversed(self._registered_connectors)) + self._builtin_connectors
        for connector in search_order:
            if connector.can_handle(tool_name, target_system, action_type):
                return connector
        return None

    def catalog(self) -> tuple[dict[str, object], ...]:
        entries: list[dict[str, object]] = []
        for connector in self._all_connectors():
            entry: dict[str, object] = {
                "connector_id": connector.connector_id,
                "provider": connector.provider,
                "supported_tools": list(connector.supported_tools),
                "kind": "builtin",
            }
            registration = getattr(connector, "registration", None)
            if registration is not None and hasattr(registration, "to_catalog_entry"):
                entry = registration.to_catalog_entry()
            entries.append(entry)
        return tuple(entries)


def default_connector_registry() -> tuple[EnterpriseConnector, ...]:
    return (
        StripePaymentsConnector(),
        GenericEnterpriseConnector(
            connector_id="crm_case_connector",
            provider="salesforce",
            target_systems=("crm", "salesforce"),
            tool_names=("crm.update_case",),
        ),
        GenericEnterpriseConnector(
            connector_id="privacy_data_ops_connector",
            provider="enterprise_data_platform",
            target_systems=("customer_data_platform",),
            tool_names=("privacy.modify_or_delete_data",),
        ),
        GenericEnterpriseConnector(
            connector_id="change_management_connector",
            provider="servicenow",
            target_systems=("infrastructure", "itsm"),
            tool_names=("infra.change_production_configuration",),
        ),
        GenericEnterpriseConnector(
            connector_id="processor_dispute_connector",
            provider="payment_processor",
            target_systems=("payment_processor",),
            tool_names=("payments.open_dispute",),
        ),
        GenericEnterpriseConnector(
            connector_id="mcp_tool_proxy",
            provider="mcp",
            target_systems=("mcp",),
            tool_names=(),
        ),
        GenericEnterpriseConnector(
            connector_id="custom_http_connector",
            provider="custom",
            target_systems=("custom", "webhook"),
            tool_names=(),
        ),
    ) + production_deploy_connectors()


def production_deploy_connectors() -> tuple[EnterpriseConnector, ...]:
    from .deploy import GitHubConnector, RenderDeployConnector, VercelDeployConnector

    return (GitHubConnector(), VercelDeployConnector(), RenderDeployConnector())
