"""PRODUCTION_STRICT fail-closed when OPA/policy plane is unavailable."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from aegisai.application.guardrails import DecisionEngine
from aegisai.application.guardrails.opa_policy import OpaPolicyEngine
from aegisai.domain import ActionProposal, DataClassification, Decision
from aegisai.interfaces.http.enforcement import policy_plane_status
from aegisai.product import (
    AgentRegistryService,
    GatewayToolRequest,
    IdentityRBACService,
    KillSwitchService,
    PlatformControlPlaneService,
    PolicySimulatorService,
)


class PolicyFailClosedTests(unittest.TestCase):
    def test_strict_irreversible_blocks_when_opa_unavailable(self) -> None:
        with patch.dict("os.environ", {"PRODUCTION_STRICT": "true"}, clear=False):
            with patch.object(OpaPolicyEngine, "available", return_value=False):
                engine = DecisionEngine()
                decision = engine.decide(
                    ActionProposal(
                        proposal_id="p1",
                        tenant_id="bank-demo",
                        agent_id="agent-refund",
                        action_type="issue_refund",
                        target_system="payments",
                        amount_usd=2500,
                        data_classification=DataClassification.CONFIDENTIAL,
                        reversible=False,
                        customer_impact=True,
                    )
                )
        self.assertEqual(decision.decision, Decision.BLOCK)
        self.assertEqual(decision.policy_version, OpaPolicyEngine.POLICY_UNAVAILABLE_VERSION)

    def test_demo_mode_still_uses_builtin_when_opa_unavailable(self) -> None:
        with patch.dict("os.environ", {"PRODUCTION_STRICT": "false"}, clear=False):
            with patch.object(OpaPolicyEngine, "available", return_value=False):
                engine = DecisionEngine()
                decision = engine.decide(
                    ActionProposal(
                        proposal_id="p2",
                        tenant_id="bank-demo",
                        agent_id="agent-intake-triage",
                        action_type="search",
                        target_system="rag",
                        reversible=True,
                        customer_impact=False,
                    )
                )
        self.assertNotEqual(decision.policy_version, OpaPolicyEngine.POLICY_UNAVAILABLE_VERSION)

    def test_gateway_blocks_irreversible_under_strict_without_opa(self) -> None:
        with patch.dict("os.environ", {"PRODUCTION_STRICT": "true"}, clear=False):
            with patch.object(OpaPolicyEngine, "available", return_value=False):
                service = PlatformControlPlaneService(
                    agent_registry=AgentRegistryService(),
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
                        amount_usd=2500,
                        data_classification=DataClassification.CONFIDENTIAL,
                        reversible=False,
                        customer_impact=True,
                        grounding_score=0.9,
                        safety_score=0.95,
                        policy_compliance_score=0.88,
                    )
                )
        self.assertEqual(result["gateway_decision"], "block")
        self.assertEqual(result.get("policy_version"), OpaPolicyEngine.POLICY_UNAVAILABLE_VERSION)
        self.assertIn("policy_unavailable", result["policy_result"]["reason_codes"])

    def test_policy_plane_status_reports_unavailable_under_strict(self) -> None:
        with patch.dict("os.environ", {"PRODUCTION_STRICT": "true"}, clear=False):
            with patch.object(OpaPolicyEngine, "available", return_value=False):
                status = policy_plane_status()
        self.assertEqual(status["mode"], "unavailable")
        self.assertEqual(status["reason"], "policy_unavailable")
        self.assertTrue(status["fail_closed_for_irreversible"])


if __name__ == "__main__":
    unittest.main()
