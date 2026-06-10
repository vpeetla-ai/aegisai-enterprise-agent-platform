from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class GatewayToolRequest:
    tenant_id: str
    agent_id: str
    principal_id: str
    tool_name: str
    action_type: str
    target_system: str
    amount_usd: float = 0.0
    data_classification: str = "internal"
    reversible: bool = True
    customer_impact: bool = False
    grounding_score: float = 0.9
    safety_score: float = 0.95
    policy_compliance_score: float = 0.88


@dataclass(frozen=True)
class GatewayToolResult:
    gateway_decision: str
    execution_token: str | None
    raw: dict[str, Any]

    @property
    def allowed(self) -> bool:
        return self.gateway_decision == "allow" and self.execution_token is not None

    @property
    def requires_approval(self) -> bool:
        return self.gateway_decision == "approval_required"


class GatewayClient:
    """Wrap side-effecting tool calls with AegisAI governance gateway enforcement."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout_seconds: float = 30.0,
        auth_bearer: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.auth_bearer = auth_bearer

    def request_tool(self, request: GatewayToolRequest) -> GatewayToolResult:
        headers = {"Content-Type": "application/json"}
        if self.auth_bearer:
            headers["Authorization"] = f"Bearer {self.auth_bearer}"
        payload = {
            "tenant_id": request.tenant_id,
            "agent_id": request.agent_id,
            "principal_id": request.principal_id,
            "tool_name": request.tool_name,
            "action_type": request.action_type,
            "target_system": request.target_system,
            "amount_usd": request.amount_usd,
            "data_classification": request.data_classification,
            "reversible": request.reversible,
            "customer_impact": request.customer_impact,
            "grounding_score": request.grounding_score,
            "safety_score": request.safety_score,
            "policy_compliance_score": request.policy_compliance_score,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/api/gateway/tool-request", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return GatewayToolResult(
            gateway_decision=str(data.get("gateway_decision", "block")),
            execution_token=data.get("execution_token"),
            raw=data,
        )

    def execute_with_token(
        self,
        *,
        execution_token: str,
        tenant_id: str,
        case_id: str,
        proposal_id: str,
        actor_id: str = "execution-broker",
        idempotency_key: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-AegisAI-Execution-Token": execution_token,
        }
        if self.auth_bearer:
            headers["Authorization"] = f"Bearer {self.auth_bearer}"
        body = {
            "tenant_id": tenant_id,
            "case_id": case_id,
            "proposal_id": proposal_id,
            "actor_id": actor_id,
            "idempotency_key": idempotency_key,
            "dry_run": dry_run,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/api/execution/execute", json=body, headers=headers)
            response.raise_for_status()
            return response.json()
