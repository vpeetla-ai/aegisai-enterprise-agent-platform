import unittest

from aegisai.application.guardrails import DecisionEngine
from aegisai.domain import ActionProposal, DataClassification, Decision, RiskLevel


class DecisionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()

    def test_low_risk_action_auto_approves_when_evaluation_passes(self) -> None:
        proposal = ActionProposal(
            proposal_id="p-low",
            tenant_id="tenant",
            agent_id="support-agent",
            action_type="send_internal_summary",
            target_system="crm",
            data_classification=DataClassification.INTERNAL,
            model_confidence=0.95,
        )

        decision = self.engine.decide(proposal)

        self.assertEqual(decision.decision, Decision.AUTO_APPROVE)
        self.assertEqual(decision.risk.level, RiskLevel.LOW)
        self.assertTrue(decision.evaluation.passed)

    def test_medium_risk_action_requires_human_approval(self) -> None:
        proposal = ActionProposal(
            proposal_id="p-medium",
            tenant_id="tenant",
            agent_id="refund-agent",
            action_type="issue_refund",
            target_system="payments",
            amount_usd=1_500,
            customer_impact=True,
        )

        decision = self.engine.decide(proposal)

        self.assertEqual(decision.decision, Decision.HUMAN_APPROVAL)
        self.assertEqual(decision.approval_role, "workflow_owner")

    def test_high_risk_action_escalates(self) -> None:
        proposal = ActionProposal(
            proposal_id="p-high",
            tenant_id="tenant",
            agent_id="ops-agent",
            action_type="change_access_policy",
            target_system="iam",
            data_classification=DataClassification.RESTRICTED,
            reversible=False,
        )

        decision = self.engine.decide(proposal)

        self.assertEqual(decision.decision, Decision.ESCALATE)
        self.assertEqual(decision.approval_role, "senior_domain_approver")

    def test_critical_or_unsafe_high_risk_action_blocks(self) -> None:
        proposal = ActionProposal(
            proposal_id="p-block",
            tenant_id="tenant",
            agent_id="payments-agent",
            action_type="wire_transfer",
            target_system="payments",
            amount_usd=50_000,
            data_classification=DataClassification.RESTRICTED,
            reversible=False,
            customer_impact=True,
            model_confidence=0.62,
            evaluation_scores={"grounding": 0.55, "safety": 0.70},
        )

        decision = self.engine.decide(proposal)

        self.assertEqual(decision.decision, Decision.BLOCK)
        self.assertFalse(decision.evaluation.passed)


if __name__ == "__main__":
    unittest.main()
