"""Agent passport expiry + execution token revoke drills."""

from __future__ import annotations

import unittest
from dataclasses import replace

from aegisai.application.execution.tokens import ExecutionTokenService, tool_args_digest
from aegisai.domain import DataClassification
from aegisai.product import (
    AgentRegistryService,
    GatewayToolRequest,
    IdentityRBACService,
    KillSwitchService,
    PlatformControlPlaneService,
    PolicySimulatorService,
)


class PassportAndTokenTests(unittest.TestCase):
    def test_issue_revoke_verify_fails(self) -> None:
        service = ExecutionTokenService(secret="test-secret")
        token = service.issue(
            tenant_id="bank-demo",
            agent_id="agent-refund",
            tool_name="payments.issue_refund",
            gateway_decision="allow",
            tool_digest=tool_args_digest("payments.issue_refund", {"amount": 10}),
        )
        claims = service.verify(token)
        self.assertIsNotNone(claims)
        assert claims is not None
        self.assertTrue(claims.jti)
        self.assertEqual(claims.tool_digest, tool_args_digest("payments.issue_refund", {"amount": 10}))

        revoked = service.revoke(token)
        self.assertTrue(revoked["revoked"])
        self.assertIsNone(service.verify(token))

    def test_expired_passport_blocks_side_effect(self) -> None:
        registry = AgentRegistryService()
        agent = registry.get_agent("agent-refund")
        assert agent is not None
        registry._store.upsert_agent(
            replace(agent, passport_expires_at="2020-01-01T00:00:00+00:00", purpose="refunds")
        )
        service = PlatformControlPlaneService(
            agent_registry=registry,
            identity_service=IdentityRBACService(),
            kill_switch_service=KillSwitchService(),
            policy_simulator=PolicySimulatorService(),
        )
        result = service.gateway_decision(
            GatewayToolRequest(
                tenant_id="bank-demo",
                agent_id="agent-refund",
                principal_id="execution-broker",
                tool_name="payments.issue_refund",
                action_type="issue_refund",
                target_system="payments",
                amount_usd=100,
                data_classification=DataClassification.CONFIDENTIAL,
                reversible=True,
                customer_impact=True,
                grounding_score=0.9,
                safety_score=0.95,
                policy_compliance_score=0.88,
            )
        )
        self.assertEqual(result["gateway_decision"], "deny")
        self.assertTrue(result["registry"]["passport_expired"])

    def test_register_passport_fields_in_payload(self) -> None:
        registry = AgentRegistryService()
        agent = registry.register_agent(
            agent_id="agent-passport-demo",
            name="Passport Demo",
            owner="AI Platform",
            business_domain="Demo",
            risk_tier="low",
            autonomy_level=1,
            allowed_tools=("rag.search_policy_memory",),
            data_classes=("internal",),
            purpose="panel-demo",
            passport_expires_at="2099-01-01T00:00:00+00:00",
            eval_baseline_id="ger-graph-hitl-v1",
        )
        payload = registry.to_payload(agent)
        self.assertEqual(payload["purpose"], "panel-demo")
        self.assertEqual(payload["passport"]["eval_baseline_id"], "ger-graph-hitl-v1")


if __name__ == "__main__":
    unittest.main()
