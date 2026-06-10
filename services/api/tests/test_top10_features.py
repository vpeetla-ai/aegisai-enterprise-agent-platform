import unittest

from aegisai.application.execution.tokens import ExecutionTokenService
from aegisai.product.finops import FinOpsService
from aegisai.product.red_team_evals import RedTeamEvalService
from aegisai.product.agent_registry import AgentRegistryService


class TopTenFeatureTests(unittest.TestCase):
    def test_execution_token_issue_and_verify(self) -> None:
        service = ExecutionTokenService(secret="test-secret")
        token = service.issue(
            tenant_id="bank-demo",
            agent_id="agent-refund",
            tool_name="payments.issue_refund",
            gateway_decision="allow",
        )
        claims = service.verify(token)
        self.assertIsNotNone(claims)
        assert claims is not None
        self.assertEqual(claims.tenant_id, "bank-demo")
        self.assertEqual(claims.tool_name, "payments.issue_refund")

    def test_finops_dashboard_reports_anomalies(self) -> None:
        dashboard = FinOpsService(AgentRegistryService()).dashboard()
        self.assertEqual(dashboard["product_module"], "FinOps")
        self.assertGreater(int(dashboard["agent_count"]), 0)
        self.assertIn("cost_by_agent", dashboard)

    def test_red_team_eval_suite_runs(self) -> None:
        report = RedTeamEvalService().run()
        self.assertEqual(report["product_module"], "RedTeam")
        self.assertGreater(int(report["total_cases"]), 0)


if __name__ == "__main__":
    unittest.main()
