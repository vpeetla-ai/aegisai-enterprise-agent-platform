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
        AgentToolSpec(
            name="github.push_files",
            owner="fe_engineer",
            side_effecting=True,
            approval_required=False,
            description="Commit generated frontend artifacts to a feature branch.",
        ),
        AgentToolSpec(
            name="github.create_pull_request",
            owner="review_deploy",
            side_effecting=True,
            approval_required=True,
            description="Open a pull request after code review passes.",
        ),
        AgentToolSpec(
            name="deploy.vercel_release",
            owner="fe_engineer",
            side_effecting=True,
            approval_required=True,
            description="Trigger a Vercel production deployment (HITL required).",
        ),
        AgentToolSpec(
            name="deploy.render_release",
            owner="be_engineer",
            side_effecting=True,
            approval_required=True,
            description="Trigger a Render service deployment (HITL required).",
        ),
        AgentToolSpec(
            name="design.analyze_figma",
            owner="ui_design_analyst",
            side_effecting=False,
            approval_required=False,
            description="Analyze Figma frames and export design tokens.",
        ),
        AgentToolSpec(
            name="notify.slack",
            owner="venkat-ai-platform",
            side_effecting=True,
            approval_required=False,
            description="Deliver agent report to Slack via incoming webhook.",
        ),
        AgentToolSpec(
            name="notify.telegram",
            owner="venkat-ai-platform",
            side_effecting=True,
            approval_required=False,
            description="Deliver agent report to Telegram chat.",
        ),
        AgentToolSpec(
            name="notify.whatsapp",
            owner="venkat-ai-platform",
            side_effecting=True,
            approval_required=True,
            description="Deliver agent report via Twilio WhatsApp (customer channel).",
        ),
    )
