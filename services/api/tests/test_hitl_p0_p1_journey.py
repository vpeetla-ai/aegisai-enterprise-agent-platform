"""P0/P1 journey: gateway HITL → queue → approve; kill switch persist; content notify gate."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from aegisai.interfaces.http.api import app
from aegisai.interfaces.http import api as api_module


class PrincipalP0P1JourneyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.headers = {
            "X-AegisAI-Principal": "control-plane-admin",
            "X-AegisAI-Roles": "reviewer,admin,security",
            "X-AegisAI-Tenant": "bank-demo",
        }

    def test_health_exposes_pilot_profile(self) -> None:
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("pilot_profile", body["enforcement"])
        self.assertIn("production_strict", body["enforcement"])
        self.assertIn("fail_closed_ready", body["enforcement"]["pilot_profile"])

    def test_gateway_deploy_lands_in_hitl_queue_and_approve(self) -> None:
        gw = self.client.post(
            "/api/gateway/tool-request",
            headers=self.headers,
            json={
                "tenant_id": "bank-demo",
                "agent_id": "agent-fe-builder",
                "principal_id": "website-build-pipeline",
                "tool_name": "deploy.vercel_release",
                "action_type": "deploy_frontend",
                "target_system": "vercel",
                "amount_usd": 0,
                "data_classification": "internal",
                "reversible": True,
                "customer_impact": False,
            },
        )
        self.assertEqual(gw.status_code, 200)
        payload = gw.json()
        self.assertEqual(payload["gateway_decision"], "approval_required")
        self.assertIsNotNone(payload.get("hitl_task"))
        proposal_id = payload["hitl_task"]["proposal_id"]
        case_id = payload["hitl_task"]["case_id"]

        queue = self.client.get("/api/hitl/queue?tenant_id=bank-demo&status=pending")
        self.assertEqual(queue.status_code, 200)
        tasks = queue.json()["tasks"]
        self.assertTrue(any(t["proposal_id"] == proposal_id for t in tasks))

        review = self.client.post(
            "/api/control-plane/reviewer-action",
            headers=self.headers,
            json={
                "tenant_id": "bank-demo",
                "case_id": case_id,
                "proposal_id": proposal_id,
                "reviewer_id": "control-plane-admin",
                "action": "approve",
                "reason": "pytest approve",
            },
        )
        self.assertEqual(review.status_code, 200)
        self.assertEqual(review.json()["status"], "recorded")
        self.assertTrue(review.json().get("execution_token"))

        queue_after = self.client.get("/api/hitl/queue?tenant_id=bank-demo&status=pending")
        self.assertFalse(any(t["proposal_id"] == proposal_id for t in queue_after.json()["tasks"]))

    def test_kill_switch_persists_and_deactivates(self) -> None:
        activate = self.client.post(
            "/api/kill-switches",
            headers=self.headers,
            json={
                "scope_type": "tool",
                "scope_value": "deploy.vercel_release",
                "reason": "pytest freeze",
                "created_by": "security-admin",
            },
        )
        self.assertEqual(activate.status_code, 200)
        rule_id = activate.json()["rule"]["rule_id"]
        self.assertGreaterEqual(activate.json()["posture"]["active_rule_count"], 1)

        # Reload service state from store proves persistence API path works
        rows = api_module.control_plane_store.list_kill_switch_rules()
        self.assertTrue(any(r["rule_id"] == rule_id and int(r["active"]) for r in rows))

        deactivate = self.client.post(
            f"/api/kill-switches/{rule_id}/deactivate",
            headers=self.headers,
        )
        self.assertEqual(deactivate.status_code, 200)
        self.assertFalse(deactivate.json()["rule"]["active"])

    def test_content_pipeline_notify_requires_hitl(self) -> None:
        run = self.client.post(
            "/api/orchestrators/ai-content/run",
            headers=self.headers,
        )
        self.assertEqual(run.status_code, 200)
        body = run.json()
        self.assertEqual(body["status"], "pending_hitl")
        self.assertTrue(body.get("hitl_pending"))
        self.assertTrue(body.get("hitl_tasks"))
        queue = self.client.get("/api/hitl/queue?tenant_id=bank-demo&status=pending")
        self.assertGreaterEqual(queue.json()["pending_count"], 1)


if __name__ == "__main__":
    unittest.main()
