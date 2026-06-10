from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentToolSpec:
    name: str
    owner: str
    side_effecting: bool
    approval_required: bool
    description: str


def enterprise_tool_registry() -> tuple[AgentToolSpec, ...]:
    """Documents the governed tools agents may request through the control plane."""

    return (
        AgentToolSpec(
            name="rag.search_policy_memory",
            owner="evidence_retrieval_agent",
            side_effecting=False,
            approval_required=False,
            description="Search tenant-scoped policy and evidence memory before proposing an action.",
        ),
        AgentToolSpec(
            name="payments.issue_refund",
            owner="refund_agent",
            side_effecting=True,
            approval_required=True,
            description="Issue a customer refund through the execution broker after policy approval.",
        ),
        AgentToolSpec(
            name="privacy.modify_or_delete_data",
            owner="data_operations_agent",
            side_effecting=True,
            approval_required=True,
            description="Modify, export, or delete customer data only after privacy controls pass.",
        ),
        AgentToolSpec(
            name="infra.change_production_configuration",
            owner="it_operations_agent",
            side_effecting=True,
            approval_required=True,
            description="Submit production configuration changes with rollback metadata.",
        ),
    )
