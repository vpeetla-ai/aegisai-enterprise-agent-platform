import unittest

from aegisai.application.orchestration import AgentName, BusinessRequest, MultiAgentOrchestrator, WorkflowType
from aegisai.domain import DataClassification, Decision


class MultiAgentOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = MultiAgentOrchestrator()

    def test_refund_request_runs_refund_workflow_and_routes_through_control_plane(self) -> None:
        result = self.orchestrator.run(
            BusinessRequest(
                request_id="case-100",
                tenant_id="bank-demo",
                user_id="user-1",
                text="Customer is requesting a refund for a failed booking",
                amount_usd=2_500,
                data_classification=DataClassification.CONFIDENTIAL,
            )
        )

        self.assertEqual(result.workflow_type, WorkflowType.REFUND)
        self.assertIn(AgentName.PLANNER, result.agents_run)
        self.assertIn(AgentName.REFUND, result.agents_run)
        self.assertEqual(len(result.context.proposed_actions), 1)
        self.assertEqual(result.context.governance_decisions[0].decision, Decision.ESCALATE)

    def test_data_deletion_with_restricted_data_is_blocked_by_control_plane(self) -> None:
        result = self.orchestrator.run(
            BusinessRequest(
                request_id="case-200",
                tenant_id="bank-demo",
                user_id="user-2",
                text="Delete customer data from all systems",
                data_classification=DataClassification.RESTRICTED,
            )
        )

        self.assertEqual(result.workflow_type, WorkflowType.DATA_OPERATION)
        self.assertIn(AgentName.DATA_OPS, result.agents_run)
        self.assertEqual(result.context.governance_decisions[0].decision, Decision.BLOCK)

    def test_low_value_refund_can_auto_approve(self) -> None:
        result = self.orchestrator.run(
            BusinessRequest(
                request_id="case-300",
                tenant_id="bank-demo",
                user_id="user-3",
                text="Refund customer for duplicate small fee",
                amount_usd=25,
                data_classification=DataClassification.INTERNAL,
                customer_impact=False,
            )
        )

        self.assertEqual(result.workflow_type, WorkflowType.REFUND)
        self.assertEqual(result.context.governance_decisions[0].decision, Decision.AUTO_APPROVE)


if __name__ == "__main__":
    unittest.main()
