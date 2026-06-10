from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from aegisai.product.platform_control_plane import GatewayToolRequest, PlatformControlPlaneService


@dataclass(frozen=True)
class McpToolCallRequest:
    tenant_id: str
    agent_id: str
    principal_id: str
    mcp_server: str
    tool_name: str
    arguments: dict[str, object]
    action_type: str
    target_system: str
    amount_usd: float = 0.0
    data_classification: str = "internal"
    reversible: bool = True
    customer_impact: bool = False
    grounding_score: float = 0.9
    safety_score: float = 0.95
    policy_compliance_score: float = 0.88


class McpGovernanceProxy:
    """Routes MCP tool invocations through the same governance gateway as first-class tools."""

    def __init__(self, control_plane: PlatformControlPlaneService) -> None:
        self.control_plane = control_plane

    def posture(self) -> dict[str, object]:
        return {
            "product_module": "MCP Proxy",
            "protocol": "Model Context Protocol (MCP)",
            "strategy": (
                "Agents call MCP tools through AegisAI so policy, HITL, kill switches, "
                "and audit apply before any side effect reaches an MCP server."
            ),
            "flow": [
                "agent.mcp_tool_call",
                "aegisai.mcp_proxy",
                "governance_gateway",
                "execution_token_or_hitl",
                "mcp_server.invoke (only if allowed)",
            ],
            "supported_servers": [
                "filesystem",
                "github",
                "postgres",
                "slack",
                "custom_enterprise_mcp",
            ],
        }

    def invoke(
        self,
        request: McpToolCallRequest,
        execution_token_service: object,
    ) -> dict[str, object]:
        canonical_tool = f"mcp.{request.mcp_server}.{request.tool_name}"
        gateway = self.control_plane.gateway_decision(
            GatewayToolRequest(
                tenant_id=request.tenant_id,
                agent_id=request.agent_id,
                principal_id=request.principal_id,
                tool_name=canonical_tool,
                action_type=request.action_type,
                target_system=request.target_system if request.target_system != "mcp" else "mcp",
                amount_usd=request.amount_usd,
                data_classification=_classification(request.data_classification),
                reversible=request.reversible,
                customer_impact=request.customer_impact,
                grounding_score=request.grounding_score,
                safety_score=request.safety_score,
                policy_compliance_score=request.policy_compliance_score,
            )
        )
        token = None
        if gateway.get("gateway_decision") == "allow":
            token = execution_token_service.issue(
                tenant_id=request.tenant_id,
                agent_id=request.agent_id,
                tool_name=canonical_tool,
                gateway_decision="allow",
                proposal_id=None,
            )
        mcp_reference = None
        mcp_message = "MCP invocation paused pending governance decision."
        if gateway.get("gateway_decision") == "allow" and token:
            mcp_reference = f"mcp://{request.mcp_server}/{request.tool_name}/{uuid4()}"
            mcp_message = (
                f"MCP tool '{request.tool_name}' on server '{request.mcp_server}' "
                "authorized; forward invocation with execution token."
            )
        elif gateway.get("gateway_decision") == "approval_required":
            mcp_message = "MCP tool call held for human approval before server invocation."
        elif gateway.get("gateway_decision") in {"block", "deny", "frozen"}:
            mcp_message = "MCP tool call blocked by governance policy or kill switch."

        return {
            "product_module": "MCP Proxy",
            "mcp_server": request.mcp_server,
            "tool_name": request.tool_name,
            "canonical_tool_name": canonical_tool,
            "arguments_preview": {key: request.arguments[key] for key in list(request.arguments)[:5]},
            "gateway_decision": gateway.get("gateway_decision"),
            "execution_token": token,
            "mcp_invocation_status": _mcp_status(gateway.get("gateway_decision")),
            "mcp_external_reference": mcp_reference,
            "message": mcp_message,
            "gateway": gateway,
        }


def _classification(value: str) -> object:
    from aegisai.domain import DataClassification

    try:
        return DataClassification(value)
    except ValueError:
        return DataClassification.INTERNAL


def _mcp_status(gateway_decision: object) -> str:
    mapping = {
        "allow": "authorized",
        "approval_required": "paused_for_hitl",
        "block": "blocked",
        "deny": "denied",
        "frozen": "frozen",
    }
    return mapping.get(str(gateway_decision), "unknown")
