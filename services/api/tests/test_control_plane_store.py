import unittest

from aegisai.application.orchestration import BusinessRequest, MultiAgentOrchestrator
from aegisai.domain import DataClassification, ExecutionResult, ExecutionStatus
from aegisai.infrastructure.persistence import SQLiteControlPlaneStore


class ControlPlaneStoreTests(unittest.TestCase):
    def test_persists_orchestration_and_verifies_audit_chain(self) -> None:
        orchestrator = MultiAgentOrchestrator()
        result = orchestrator.run(
            BusinessRequest(
                request_id="case-store-1",
                tenant_id="bank-demo",
                user_id="user-1",
                text="Customer requests a refund for a failed booking",
                amount_usd=2_500,
                data_classification=DataClassification.CONFIDENTIAL,
            )
        )
        store = SQLiteControlPlaneStore()

        store.save_orchestration(result)

        self.assertEqual(store.count("cases"), 1)
        self.assertEqual(store.count("action_proposals"), 1)
        self.assertEqual(store.count("governance_decisions"), 1)
        self.assertEqual(store.count("approval_tasks"), 1)
        self.assertEqual(store.count("action_executions"), 0)
        self.assertGreaterEqual(store.count("agent_traces"), 7)
        self.assertEqual(store.count("audit_events"), 1)
        self.assertTrue(store.verify_audit_chain("bank-demo"))

    def test_records_reviewer_action_and_appends_audit_event(self) -> None:
        orchestrator = MultiAgentOrchestrator()
        result = orchestrator.run(
            BusinessRequest(
                request_id="case-approve-1",
                tenant_id="bank-demo",
                user_id="user-1",
                text="Customer requests a refund for a failed booking",
                amount_usd=2_500,
                data_classification=DataClassification.CONFIDENTIAL,
            )
        )
        store = SQLiteControlPlaneStore()
        store.save_orchestration(result)

        store.record_reviewer_action(
            tenant_id="bank-demo",
            case_id="case-approve-1",
            proposal_id="case-approve-1:refund",
            reviewer_id="approver-7",
            action="approve",
            reason="Evidence and policy checks are sufficient.",
        )

        self.assertEqual(store.count("audit_events"), 2)
        self.assertTrue(store.verify_audit_chain("bank-demo"))

    def test_records_execution_result_and_appends_audit_event(self) -> None:
        orchestrator = MultiAgentOrchestrator()
        result = orchestrator.run(
            BusinessRequest(
                request_id="case-exec-1",
                tenant_id="bank-demo",
                user_id="user-1",
                text="Customer requests a refund for a failed booking",
                amount_usd=2_500,
                data_classification=DataClassification.CONFIDENTIAL,
            )
        )
        store = SQLiteControlPlaneStore()
        store.save_orchestration(result)
        store.record_reviewer_action(
            tenant_id="bank-demo",
            case_id="case-exec-1",
            proposal_id="case-exec-1:refund",
            reviewer_id="approver-7",
            action="approve",
            reason="Ready to execute.",
        )

        readiness = store.get_execution_readiness("bank-demo", "case-exec-1:refund")
        self.assertIsNotNone(readiness)
        self.assertEqual(readiness.approval_status, "approved")

        store.record_execution_result(
            ExecutionResult(
                execution_id="exec-test-1",
                tenant_id="bank-demo",
                case_id="case-exec-1",
                proposal_id="case-exec-1:refund",
                status=ExecutionStatus.EXECUTED,
                target_system="payments",
                action_type="issue_refund",
                connector="payments_refund_connector",
                idempotency_key="bank-demo:case-exec-1:refund:execute",
                external_reference="payments://executions/test",
                rollback_reference="rollback://case-exec-1:refund/key",
                message="Approved action executed.",
            ),
            actor_id="execution-broker",
        )

        self.assertEqual(store.count("action_executions"), 1)
        self.assertEqual(store.count("audit_events"), 3)
        self.assertTrue(store.verify_audit_chain("bank-demo"))

        snapshot = store.case_audit_snapshot("bank-demo", "case-exec-1")
        self.assertEqual(snapshot["case"]["case_id"], "case-exec-1")
        self.assertEqual(len(snapshot["action_executions"]), 1)
        self.assertTrue(snapshot["audit_chain_valid"])


if __name__ == "__main__":
    unittest.main()
