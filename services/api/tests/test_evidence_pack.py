"""Incident evidence pack builder tests."""

from __future__ import annotations

import unittest

from aegisai.product.agent_registry import AgentRegistryService
from aegisai.product.audit_export import AuditPacketExporter
from aegisai.product.audit_signing import AuditPacketSigner
from aegisai.product.evidence_pack import IncidentEvidencePackBuilder


class EvidencePackTests(unittest.TestCase):
    def test_pack_includes_passport_policy_and_signature(self) -> None:
        builder = IncidentEvidencePackBuilder(
            exporter=AuditPacketExporter(signer=AuditPacketSigner()),
            agent_registry=AgentRegistryService(),
        )
        pack = builder.build(
            tenant_id="bank-demo",
            case_id="case-demo-1",
            case_snapshot={
                "case": {"case_id": "case-demo-1", "agent_id": "agent-refund"},
                "agent_traces": [{"agent_name": "agent-refund", "step_name": "refund"}],
                "action_proposals": [],
                "governance_decisions": [
                    {"decision": "human_approval", "policy_version": "policy-2026.05"}
                ],
                "approval_tasks": [],
                "action_executions": [],
                "audit_events": [],
                "audit_chain_valid": True,
            },
            actor_id="reviewer-1",
            gateway_decision="approval_required",
            tool_name="payments.issue_refund",
            tool_args={"amount_usd": 2500},
            policy_version="policy-2026.05",
            agent_id="agent-refund",
            cost_usd=0.12,
        )
        self.assertEqual(pack["packet_type"], "aegisai.incident_evidence_pack")
        self.assertEqual(pack["policy_version"], "policy-2026.05")
        self.assertIsNotNone(pack["agent_passport"])
        self.assertEqual(pack["agent_passport"]["owner"], "Finance Operations")
        self.assertIsNotNone(pack["tool_args_hash"])
        self.assertIsInstance(pack.get("signature"), dict)
        self.assertIn("content_digest", pack["signature"])


if __name__ == "__main__":
    unittest.main()
