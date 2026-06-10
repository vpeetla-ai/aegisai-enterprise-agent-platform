import os
import unittest
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
    from aegisai.api import app
except ModuleNotFoundError:  # pragma: no cover
    TestClient = None
    app = None


@unittest.skipIf(TestClient is None, "FastAPI dependencies are not installed")
class GatewayEnforcementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_governance_metrics_endpoint(self) -> None:
        self.client.post(
            "/api/gateway/tool-request",
            json={
                "tenant_id": "bank-demo",
                "tool_name": "payments.issue_refund",
                "target_system": "payments",
                "amount_usd": 100,
            },
        )
        response = self.client.get("/api/governance/metrics?tenant_id=bank-demo")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["pilot_target_pct"], 100.0)
        self.assertGreaterEqual(payload["gateway_tool_calls"], 1)

    @patch.dict(os.environ, {"AEGISAI_REQUIRE_EXECUTION_TOKEN": "true"}, clear=False)
    def test_execution_requires_token_when_enforced(self) -> None:
        self.client.post(
            "/api/agents/run",
            json={
                "request_id": "case-token-enforce-1",
                "tenant_id": "bank-demo",
                "text": "Customer requests a refund above 2500",
                "amount_usd": 2500,
                "data_classification": "confidential",
                "customer_impact": True,
            },
        )
        self.client.post(
            "/api/control-plane/reviewer-action",
            json={
                "tenant_id": "bank-demo",
                "case_id": "case-token-enforce-1",
                "proposal_id": "case-token-enforce-1:refund",
                "action": "approve",
            },
        )
        denied = self.client.post(
            "/api/execution/execute",
            json={
                "tenant_id": "bank-demo",
                "case_id": "case-token-enforce-1",
                "proposal_id": "case-token-enforce-1:refund",
            },
        )
        self.assertEqual(denied.json()["status"], "denied")
        self.assertIn("token", denied.json()["message"].lower())

    def test_reviewer_approve_returns_execution_token(self) -> None:
        self.client.post(
            "/api/agents/run",
            json={
                "request_id": "case-token-issue-1",
                "tenant_id": "bank-demo",
                "text": "Customer requests a refund above 2500",
                "amount_usd": 2500,
                "data_classification": "confidential",
                "customer_impact": True,
            },
        )
        response = self.client.post(
            "/api/control-plane/reviewer-action",
            json={
                "tenant_id": "bank-demo",
                "case_id": "case-token-issue-1",
                "proposal_id": "case-token-issue-1:refund",
                "action": "approve",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json().get("execution_token"))
