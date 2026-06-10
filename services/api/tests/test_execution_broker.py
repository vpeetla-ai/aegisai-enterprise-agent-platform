import unittest

from aegisai.application.execution import ApprovedActionExecutionBroker
from aegisai.application.execution.broker import ExecutionReadiness
from aegisai.domain import Decision, ExecutionCommand


class ExecutionBrokerTests(unittest.TestCase):
    def test_requires_approval_before_side_effecting_execution(self) -> None:
        broker = ApprovedActionExecutionBroker()

        result = broker.execute(
            ExecutionCommand(
                tenant_id="bank-demo",
                case_id="case-1",
                proposal_id="case-1:refund",
                actor_id="execution-broker",
                idempotency_key="bank-demo:case-1:refund:execute",
            ),
            ExecutionReadiness(
                action_type="issue_refund",
                target_system="payments",
                amount_usd=2500.0,
                reversible=True,
                decision=Decision.ESCALATE.value,
                approval_status="pending",
            ),
        )

        self.assertEqual(result.status.value, "requires_approval")
        self.assertIsNone(result.external_reference)

    def test_executes_after_human_approval(self) -> None:
        broker = ApprovedActionExecutionBroker()

        result = broker.execute(
            ExecutionCommand(
                tenant_id="bank-demo",
                case_id="case-1",
                proposal_id="case-1:refund",
                actor_id="execution-broker",
                idempotency_key="bank-demo:case-1:refund:execute",
            ),
            ExecutionReadiness(
                action_type="issue_refund",
                target_system="payments",
                amount_usd=2500.0,
                reversible=True,
                decision=Decision.ESCALATE.value,
                approval_status="approved",
            ),
        )

        self.assertEqual(result.status.value, "executed")
        self.assertEqual(result.connector, "payments_refund_connector")
        self.assertIsNotNone(result.rollback_reference)


if __name__ == "__main__":
    unittest.main()
