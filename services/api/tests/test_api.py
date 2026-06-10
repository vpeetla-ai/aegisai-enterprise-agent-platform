import unittest

try:
    from fastapi.testclient import TestClient
    from aegisai.api import app
except ModuleNotFoundError:  # pragma: no cover - dependency not installed in minimal mode
    TestClient = None
    app = None


@unittest.skipIf(TestClient is None, "FastAPI dependencies are not installed")
class FastAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_root_endpoint_guides_local_development(self) -> None:
        response = self.client.get("/")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["service"], "aegisai-api")
        self.assertEqual(payload["docs"], "/docs")
        self.assertIn("POST /api/agents/run", payload["primary_endpoints"])
        self.assertIn("GET /api/agent-registry", payload["primary_endpoints"])
        self.assertIn("POST /api/gateway/tool-request", payload["primary_endpoints"])

    def test_agent_run_endpoint_executes_rag_graph_and_control_plane(self) -> None:
        response = self.client.post(
            "/api/agents/run",
            json={
                "request_id": "case-api-test-1",
                "tenant_id": "bank-demo",
                "user_id": "user-1",
                "text": "Customer requests a refund above 2500",
                "amount_usd": 2500,
                "data_classification": "confidential",
                "customer_impact": True,
            },
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["decision"], "escalate")
        self.assertGreater(payload["agent_trace_count"], 0)
        self.assertGreater(len(payload["retrieved_context"]), 0)
        self.assertGreater(len(payload["tools_available"]), 0)
        self.assertEqual({item["name"] for item in payload["observability"]}, {"Langfuse", "LangSmith"})

    def test_data_deletion_use_case_returns_blocked_decision(self) -> None:
        response = self.client.post(
            "/api/agents/run",
            json={
                "request_id": "case-api-test-data-delete",
                "tenant_id": "bank-demo",
                "user_id": "user-1",
                "text": "Employee requests deletion of all customer profile data after an account closure",
                "amount_usd": 0,
                "data_classification": "restricted",
                "customer_impact": True,
            },
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["workflow_type"], "data_operation")
        self.assertEqual(payload["decision"], "block")
        self.assertEqual(payload["risk_level"], "critical")

    def test_gateway_returns_execution_token_on_allow(self) -> None:
        response = self.client.post(
            "/api/gateway/tool-request",
            json={
                "tenant_id": "bank-demo",
                "agent_id": "agent-refund",
                "principal_id": "execution-broker",
                "tool_name": "payments.issue_refund",
                "action_type": "issue_refund",
                "target_system": "payments",
                "amount_usd": 25,
                "data_classification": "internal",
                "customer_impact": False,
            },
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        if payload.get("gateway_decision") == "allow":
            self.assertIsNotNone(payload.get("execution_token"))

    def test_connector_catalog_endpoint(self) -> None:
        response = self.client.get("/api/connectors/catalog")
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(payload["total"], 5)
        providers = {item["provider"] for item in payload["connectors"]}
        self.assertIn("stripe", providers)
        self.assertIn("salesforce", providers)
        self.assertIn("mcp", providers)

    def test_mcp_tool_call_routes_through_gateway(self) -> None:
        response = self.client.post(
            "/api/mcp/tool-call",
            json={
                "mcp_server": "github",
                "tool_name": "create_issue",
                "action_type": "create_issue",
                "target_system": "mcp",
                "amount_usd": 0,
            },
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["product_module"], "MCP Proxy")
        self.assertIn(payload["gateway_decision"], {"allow", "approval_required", "block", "deny"})

    def test_finops_dashboard_endpoint(self) -> None:
        response = self.client.get("/api/finops/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["product_module"], "FinOps")

    def test_red_team_eval_endpoint(self) -> None:
        response = self.client.post("/api/evaluations/red-team/run")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["product_module"], "RedTeam")

    def test_observability_status_endpoint_reports_exporter_posture(self) -> None:
        response = self.client.get("/api/observability/status")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn("AegisAI control-plane", payload["source_of_truth"])
        self.assertEqual({item["name"] for item in payload["exporters"]}, {"Langfuse", "LangSmith"})

    def test_reviewer_action_endpoint_records_audit_event(self) -> None:
        self.client.post(
            "/api/agents/run",
            json={
                "request_id": "case-api-test-2",
                "tenant_id": "bank-demo",
                "user_id": "user-1",
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
                "case_id": "case-api-test-2",
                "proposal_id": "case-api-test-2:refund",
                "reviewer_id": "approver-7",
                "action": "approve",
                "reason": "Evidence is sufficient.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["audit_chain_valid"])

    def test_execution_endpoint_requires_approval_then_executes_after_review(self) -> None:
        self.client.post(
            "/api/agents/run",
            json={
                "request_id": "case-api-exec-1",
                "tenant_id": "bank-demo",
                "user_id": "user-1",
                "text": "Customer requests a refund above 2500",
                "amount_usd": 2500,
                "data_classification": "confidential",
                "customer_impact": True,
            },
        )

        before_approval = self.client.post(
            "/api/execution/execute",
            json={
                "tenant_id": "bank-demo",
                "case_id": "case-api-exec-1",
                "proposal_id": "case-api-exec-1:refund",
                "actor_id": "execution-broker",
            },
        )
        self.assertEqual(before_approval.status_code, 200)
        self.assertEqual(before_approval.json()["status"], "requires_approval")

        self.client.post(
            "/api/control-plane/reviewer-action",
            json={
                "tenant_id": "bank-demo",
                "case_id": "case-api-exec-1",
                "proposal_id": "case-api-exec-1:refund",
                "reviewer_id": "approver-7",
                "action": "approve",
                "reason": "Evidence is sufficient.",
            },
        )
        after_approval = self.client.post(
            "/api/execution/execute",
            json={
                "tenant_id": "bank-demo",
                "case_id": "case-api-exec-1",
                "proposal_id": "case-api-exec-1:refund",
                "actor_id": "execution-broker",
            },
        )

        payload = after_approval.json()
        self.assertEqual(after_approval.status_code, 200)
        self.assertEqual(payload["status"], "executed")
        self.assertEqual(payload["connector"], "payments_refund_connector")
        self.assertTrue(payload["audit_chain_valid"])

    def test_agent_registry_endpoint_returns_product_inventory(self) -> None:
        response = self.client.get("/api/agent-registry")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["product_module"], "Discover")
        self.assertGreaterEqual(payload["summary"]["total_agents"], 4)
        self.assertTrue(any(agent["risk_tier"] == "critical" for agent in payload["agents"]))

    def test_policy_simulator_endpoint_explains_decision(self) -> None:
        response = self.client.post(
            "/api/policy/simulate",
            json={
                "tenant_id": "bank-demo",
                "action_type": "issue_refund",
                "target_system": "payments",
                "amount_usd": 2500,
                "data_classification": "confidential",
                "reversible": True,
                "customer_impact": True,
                "model_confidence": 0.86,
                "grounding_score": 0.9,
                "safety_score": 0.95,
                "policy_compliance_score": 0.88,
            },
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["decision"], "escalate")
        self.assertEqual(payload["approval_role"], "senior_domain_approver")

    def test_platform_posture_endpoint_returns_executive_control_plane(self) -> None:
        response = self.client.get("/api/platform/posture")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["product_module"], "Command")
        self.assertGreaterEqual(len(payload["board_metrics"]), 4)
        self.assertIn("recommended_actions", payload)

    def test_agent_onboarding_endpoint_scores_missing_controls(self) -> None:
        response = self.client.post(
            "/api/platform/onboard-agent",
            json={
                "agent_id": "agent-salesforce-case-assistant",
                "name": "Salesforce Case Assistant",
                "owner": "Customer Operations",
                "business_domain": "Customer Support",
                "risk_tier": "high",
                "autonomy_level": 3,
                "tools": ["crm.update_case", "rag.search_policy_memory"],
                "data_classes": ["internal", "confidential"],
                "eval_suite_attached": True,
                "policy_attached": True,
                "observability_enabled": True,
                "kill_switch_enabled": False,
            },
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["product_module"], "Onboard")
        self.assertEqual(payload["launch_decision"], "limited_pilot_only")
        self.assertIn("Kill switch enabled", payload["missing_controls"])

    def test_agent_readiness_endpoint_scores_registered_agent(self) -> None:
        response = self.client.get("/api/platform/readiness/agent-refund")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["product_module"], "Readiness")
        self.assertEqual(payload["launch_decision"], "production_ready")

    def test_gateway_tool_request_endpoint_enforces_policy_before_execution(self) -> None:
        response = self.client.post(
            "/api/gateway/tool-request",
            json={
                "tenant_id": "bank-demo",
                "agent_id": "agent-refund",
                "principal_id": "execution-broker",
                "tool_name": "payments.issue_refund",
                "action_type": "issue_refund",
                "target_system": "payments",
                "amount_usd": 2500,
                "data_classification": "confidential",
                "reversible": True,
                "customer_impact": True,
                "grounding_score": 0.9,
                "safety_score": 0.95,
                "policy_compliance_score": 0.88,
            },
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["product_module"], "Governance Gateway")
        self.assertEqual(payload["gateway_decision"], "approval_required")
        self.assertIn("pause_tool_call", payload["enforcement_steps"])

    def test_integrations_endpoint_positions_bring_your_own_agent(self) -> None:
        response = self.client.get("/api/platform/integrations")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["product_module"], "Integrations")
        self.assertTrue(any(item["name"] == "AWS Bedrock Agents" for item in payload["agent_frameworks"]))

    def test_identity_posture_endpoint_returns_principals(self) -> None:
        response = self.client.get("/api/identity/posture")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["product_module"], "Identity")
        self.assertGreaterEqual(payload["principal_count"], 3)

    def test_kill_switch_endpoint_blocks_execution(self) -> None:
        self.client.post(
            "/api/agents/run",
            json={
                "request_id": "case-api-kill-1",
                "tenant_id": "bank-demo",
                "user_id": "user-1",
                "text": "Customer requests a refund above 2500",
                "amount_usd": 2500,
                "data_classification": "confidential",
                "customer_impact": True,
            },
        )
        self.client.post(
            "/api/kill-switches",
            json={
                "scope_type": "tool",
                "scope_value": "payments.issue_refund",
                "reason": "Payment connector incident.",
                "created_by": "security-admin",
            },
        )

        response = self.client.post(
            "/api/execution/execute",
            json={
                "tenant_id": "bank-demo",
                "case_id": "case-api-kill-1",
                "proposal_id": "case-api-kill-1:refund",
                "actor_id": "execution-broker",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "blocked_by_kill_switch")

    def test_golden_eval_endpoint_returns_release_gate(self) -> None:
        response = self.client.post("/api/evaluations/golden/run")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["gate"], "pass")
        self.assertGreaterEqual(payload["total_cases"], 4)

    def test_signed_audit_packet_and_verify(self) -> None:
        self.client.post(
            "/api/agents/run",
            json={
                "request_id": "case-api-signed-audit",
                "tenant_id": "bank-demo",
                "user_id": "user-1",
                "text": "Customer requests a refund above 2500",
                "amount_usd": 2500,
                "data_classification": "confidential",
                "customer_impact": True,
            },
        )
        signed = self.client.get("/api/audit-packets/bank-demo/case-api-signed-audit/signed.json")
        self.assertEqual(signed.status_code, 200)
        payload = signed.json()
        self.assertIn("signature", payload)
        verify = self.client.post(
            "/api/audit-packets/verify",
            json={"signed_packet": payload},
        )
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.json()["verification"]["valid"])

    def test_auth_posture_endpoint(self) -> None:
        response = self.client.get("/api/auth/posture")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["product_module"], "Secure")

    def test_audit_packet_json_and_pdf_endpoints_export_case_evidence(self) -> None:
        self.client.post(
            "/api/agents/run",
            json={
                "request_id": "case-api-audit-1",
                "tenant_id": "bank-demo",
                "user_id": "user-1",
                "text": "Customer requests a refund above 2500",
                "amount_usd": 2500,
                "data_classification": "confidential",
                "customer_impact": True,
            },
        )

        json_response = self.client.get("/api/audit-packets/bank-demo/case-api-audit-1.json")
        pdf_response = self.client.get("/api/audit-packets/bank-demo/case-api-audit-1.pdf")

        self.assertEqual(json_response.status_code, 200)
        self.assertEqual(json_response.json()["case"]["case_id"], "case-api-audit-1")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
