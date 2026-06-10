import unittest

from aegisai.application.orchestration import BusinessRequest, EnterpriseAgentGraph
from aegisai.domain import DataClassification


class EnterpriseAgentGraphTests(unittest.TestCase):
    def test_invokes_rag_agents_and_control_plane(self) -> None:
        graph = EnterpriseAgentGraph()

        state = graph.invoke(
            BusinessRequest(
                request_id="case-graph-1",
                tenant_id="bank-demo",
                user_id="user-1",
                text="Customer requests a refund above 2500",
                amount_usd=2500,
                data_classification=DataClassification.CONFIDENTIAL,
            )
        )

        self.assertIn("rag_result", state)
        self.assertIn("orchestration_result", state)
        self.assertEqual(state["control_plane_status"], "escalate")
        self.assertGreater(len(state["rag_result"].retrieved_documents), 0)
        self.assertEqual(
            state["rag_result"].retrieved_documents[0].source_uri,
            "policy://refund/thresholds",
        )


if __name__ == "__main__":
    unittest.main()
