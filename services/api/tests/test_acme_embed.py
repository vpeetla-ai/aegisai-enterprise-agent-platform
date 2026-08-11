"""Tests for Acme Support Agent Embed wedge (ADR-032)."""

from __future__ import annotations

import json
import os
import unittest

from fastapi.testclient import TestClient

os.environ.setdefault("AEGISAI_SAML_PANEL_MODE", "true")

from aegisai.interfaces.http.api import app, webhook_engine  # noqa: E402
from aegisai.product.pii_middleware import redact_pii, reset_compliance_log_for_tests  # noqa: E402
from aegisai.product.tenant_ops import TenantOpsService  # noqa: E402
from aegisai.product.webhook_engine import WebhookEngine  # noqa: E402


class AcmeEmbedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        reset_compliance_log_for_tests()

    def test_scim_creates_user(self) -> None:
        response = self.client.post(
            "/scim/v2/Users",
            json={
                "userName": "acme.analyst@example.com",
                "tenantId": "acme",
                "roles": ["workflow_owner", "reviewer"],
                "allowed_tools": ["notify.slack"],
            },
            headers={"X-AegisAI-Tenant": "acme"},
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["userName"], "acme.analyst@example.com")
        listed = self.client.get("/scim/v2/Users")
        self.assertEqual(listed.status_code, 200)
        ids = [r["id"] for r in listed.json()["Resources"]]
        self.assertIn("acme.analyst@example.com", ids)

    def test_saml_panel_acs(self) -> None:
        response = self.client.post(
            "/api/auth/saml/acs",
            data={
                "principal_id": "acme.sso@example.com",
                "tenant_id": "acme",
                "roles": "workflow_owner,reviewer",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["auth_mode"], "saml")
        self.assertEqual(body["tenant_id"], "acme")
        self.assertIn("session_token", body)

    def test_webhook_rejects_bad_signature(self) -> None:
        payload = {"webhook_id": "slack.interaction", "tenant_id": "acme", "payload": {"text": "approve x"}}
        raw = json.dumps(payload).encode()
        response = self.client.post(
            "/api/webhooks/ingest",
            content=raw,
            headers={"Content-Type": "application/json", "X-AegisAI-Signature": "sha256=deadbeef"},
        )
        self.assertEqual(response.status_code, 401)

    def test_webhook_accepts_valid_hmac_and_dlq_replay(self) -> None:
        engine = WebhookEngine(signing_secret="test-secret")
        calls: list[str] = []

        def handler(delivery) -> None:
            if delivery.payload.get("fail"):
                raise RuntimeError("boom")
            calls.append("ok")

        engine.register_handler("slack.interaction", handler)
        payload = {"text": "approve p1", "fail": True}
        raw = json.dumps(payload).encode()
        sig = engine.sign_body(raw)
        delivery = engine.ingest(
            webhook_id="slack.interaction",
            tenant_id="acme",
            payload=payload,
            raw_body=raw,
            signature_header=sig,
            force_fail=True,
        )
        self.assertEqual(delivery.status, "dlq")
        dlq = engine.list_dlq("acme")
        self.assertEqual(len(dlq), 1)
        # Clear failure condition then replay
        delivery.payload["fail"] = False
        replayed = engine.replay(delivery.delivery_id)
        self.assertIn(replayed.status, {"accepted", "replayed"})
        self.assertIn("ok", calls)

    def test_pii_redaction(self) -> None:
        result = redact_pii("Contact jane@acme.com or 415-555-0100")
        self.assertIn("[REDACTED_EMAIL]", result.text)
        self.assertIn("[REDACTED_PHONE]", result.text)

    def test_onboarding_ttfv(self) -> None:
        ops = TenantOpsService()
        ops.start_tenant("acme")
        for step in TenantOpsService.CHECKLIST:
            payload = ops.complete_step("acme", step)
        self.assertIsNotNone(payload["ttfv_seconds"])
        self.assertEqual(payload["completed_steps"], 5)

    def test_auth_posture_lists_saml_scim(self) -> None:
        response = self.client.get("/api/auth/posture")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["saml_acs"], "/api/auth/saml/acs")
        self.assertEqual(body["scim"], "/scim/v2/Users")

    def test_tenant_health(self) -> None:
        self.client.post(
            "/api/tenants/acme/onboarding/start",
            headers={"X-AegisAI-Principal": "control-plane-admin", "X-AegisAI-Roles": "admin"},
        )
        response = self.client.get("/api/tenants/acme/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["tenant_id"], "acme")

    def test_incident_playbook(self) -> None:
        response = self.client.get("/api/incidents/acme/case-drill-1/playbook")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("post_mortem_markdown", body)
        self.assertIn("customer_comms_markdown", body)


if __name__ == "__main__":
    unittest.main()
