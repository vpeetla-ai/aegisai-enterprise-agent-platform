from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from aegisai.product.audit_export import AuditPacketExporter
from aegisai.product.agent_registry import AgentRegistryService


class IncidentEvidencePackBuilder:
    """Assembles a panel-falsifiable incident evidence pack from audit + passport."""

    def __init__(
        self,
        exporter: AuditPacketExporter,
        agent_registry: AgentRegistryService | None = None,
    ) -> None:
        self.exporter = exporter
        self.agent_registry = agent_registry

    def build(
        self,
        *,
        tenant_id: str,
        case_id: str,
        case_snapshot: dict[str, object],
        actor_id: str | None = None,
        gateway_decision: str | None = None,
        tool_name: str | None = None,
        tool_args: dict[str, object] | None = None,
        policy_version: str | None = None,
        cost_usd: float | None = None,
        agent_id: str | None = None,
    ) -> dict[str, object]:
        signed = self.exporter.build_signed_packet(case_snapshot)
        agent_id_resolved = agent_id or _first_agent_id(case_snapshot)
        passport = None
        if self.agent_registry and agent_id_resolved:
            agent = self.agent_registry.get_agent(agent_id_resolved)
            if agent is not None:
                passport = self.agent_registry.to_payload(agent).get("passport")

        args_hash = None
        if tool_name is not None:
            blob = json.dumps(
                {"tool": tool_name, "args": tool_args or {}},
                sort_keys=True,
                separators=(",", ":"),
            )
            args_hash = hashlib.sha256(blob.encode()).hexdigest()

        resolved_policy = (
            policy_version
            or _policy_version_from_snapshot(case_snapshot)
            or _policy_version_from_signed(signed)
        )

        return {
            "packet_type": "aegisai.incident_evidence_pack",
            "generated_at": datetime.now(UTC).isoformat(),
            "tenant_id": tenant_id,
            "case_id": case_id,
            "actor_id": actor_id,
            "agent_id": agent_id_resolved,
            "agent_passport": passport,
            "policy_version": resolved_policy,
            "gateway_decision": gateway_decision,
            "tool_name": tool_name,
            "tool_args_hash": args_hash,
            "cost_usd": cost_usd,
            "audit_packet": signed,
            "signature": signed.get("signature"),
        }


def _first_agent_id(snapshot: dict[str, object]) -> str | None:
    traces = snapshot.get("agent_traces")
    if isinstance(traces, list) and traces:
        first = traces[0]
        if isinstance(first, dict):
            name = first.get("agent_name") or first.get("agent_id")
            return str(name) if name else None
    case = snapshot.get("case")
    if isinstance(case, dict) and case.get("agent_id"):
        return str(case["agent_id"])
    return None


def _policy_version_from_snapshot(snapshot: dict[str, object]) -> str | None:
    decisions = snapshot.get("governance_decisions")
    if isinstance(decisions, list):
        for item in decisions:
            if isinstance(item, dict) and item.get("policy_version"):
                return str(item["policy_version"])
    return None


def _policy_version_from_signed(signed: dict[str, object]) -> str | None:
    decisions = signed.get("governance_decisions")
    if isinstance(decisions, list) and decisions:
        first = decisions[0]
        if isinstance(first, dict) and first.get("policy_version"):
            return str(first["policy_version"])
    return None
