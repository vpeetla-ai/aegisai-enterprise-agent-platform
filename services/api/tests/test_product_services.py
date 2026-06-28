import unittest

from aegisai.domain import DataClassification
from aegisai.product import (
    AgentOnboardingInput,
    AgentRegistryService,
    AuditPacketExporter,
    GatewayToolRequest,
    GoldenEvalService,
    IdentityRBACService,
    KillSwitchService,
    PlatformControlPlaneService,
    PolicySimulationInput,
    PolicySimulatorService,
)


class ProductServiceTests(unittest.TestCase):
    def test_agent_registry_summarizes_governed_agents(self) -> None:
        service = AgentRegistryService()

        summary = service.summary()
        agents = service.list_agents()

        self.assertEqual(summary["total_agents"], len(agents))
        self.assertGreaterEqual(summary["high_or_critical_risk"], 1)
        self.assertTrue(any("payments.issue_refund" in agent.allowed_tools for agent in agents))

    def test_policy_simulator_explains_high_value_refund(self) -> None:
        service = PolicySimulatorService()

        result = service.simulate(
            PolicySimulationInput(
                tenant_id="bank-demo",
                action_type="issue_refund",
                target_system="payments",
                amount_usd=2500,
                data_classification=DataClassification.CONFIDENTIAL,
                reversible=True,
                customer_impact=True,
                model_confidence=0.86,
                grounding_score=0.9,
                safety_score=0.95,
                policy_compliance_score=0.88,
            )
        )

        self.assertEqual(result["decision"], "escalate")
        self.assertEqual(result["risk_level"], "high")
        self.assertIn("escalation", result["explanation"])

    def test_identity_rbac_authorizes_reviewer_and_tool(self) -> None:
        service = IdentityRBACService()

        reviewer = service.authorize_reviewer("approver-7", "bank-demo", "senior_domain_approver")
        tool = service.authorize_tool("execution-broker", "bank-demo", "payments.issue_refund")
        denied = service.authorize_tool("approver-7", "bank-demo", "privacy.modify_or_delete_data")

        self.assertTrue(reviewer.allowed)
        self.assertTrue(tool.allowed)
        self.assertFalse(denied.allowed)

    def test_kill_switch_blocks_matching_tool(self) -> None:
        service = KillSwitchService()
        rule = service.activate(
            scope_type="tool",
            scope_value="payments.issue_refund",
            reason="Incident response.",
            created_by="security-admin",
        )

        self.assertEqual(
            service.is_blocked("bank-demo", tool_name="payments.issue_refund"),
            rule,
        )
        self.assertIsNone(service.is_blocked("bank-demo", tool_name="privacy.modify_or_delete_data"))

    def test_golden_eval_center_returns_release_gate(self) -> None:
        result = GoldenEvalService().run()

        self.assertEqual(result["gate"], "pass")
        self.assertEqual(result["passed_cases"], result["total_cases"])

    def test_audit_packet_exporter_returns_json_and_pdf_bytes(self) -> None:
        exporter = AuditPacketExporter()
        packet = exporter.build_packet(
            {
                "case": {"case_id": "case-1"},
                "agent_traces": [],
                "action_proposals": [],
                "governance_decisions": [],
                "approval_tasks": [],
                "action_executions": [],
                "audit_events": [],
                "audit_chain_valid": True,
            }
        )

        self.assertIn(b"case-1", exporter.json_bytes(packet))
        self.assertTrue(exporter.pdf_bytes(packet).startswith(b"%PDF"))

    def test_platform_posture_and_onboarding_explain_launch_risk(self) -> None:
        service = PlatformControlPlaneService(
            agent_registry=AgentRegistryService(),
            identity_service=IdentityRBACService(),
            kill_switch_service=KillSwitchService(),
            policy_simulator=PolicySimulatorService(),
        )

        posture = service.risk_posture()
        onboarding = service.onboarding_plan(
            AgentOnboardingInput(
                agent_id="agent-salesforce-case-assistant",
                name="Salesforce Case Assistant",
                owner="Customer Operations",
                business_domain="Customer Support",
                risk_tier="high",
                autonomy_level=3,
                tools=("crm.update_case",),
                data_classes=("internal", "confidential"),
                eval_suite_attached=True,
                policy_attached=True,
                observability_enabled=True,
                kill_switch_enabled=False,
            )
        )

        self.assertEqual(posture["product_module"], "Command")
        self.assertGreater(posture["posture_score"], 0)
        self.assertEqual(onboarding["launch_decision"], "limited_pilot_only")
        self.assertIn("Kill switch enabled", onboarding["missing_controls"])

    def test_gateway_requires_approval_for_high_risk_tool_request(self) -> None:
        service = PlatformControlPlaneService(
            agent_registry=AgentRegistryService(),
            identity_service=IdentityRBACService(),
            kill_switch_service=KillSwitchService(),
            policy_simulator=PolicySimulatorService(),
        )

        result = service.gateway_decision(
            GatewayToolRequest(
                tenant_id="bank-demo",
                agent_id="agent-refund",
                principal_id="execution-broker",
                tool_name="payments.issue_refund",
                action_type="issue_refund",
                target_system="payments",
                amount_usd=2500,
                data_classification=DataClassification.CONFIDENTIAL,
                reversible=True,
                customer_impact=True,
                grounding_score=0.9,
                safety_score=0.95,
                policy_compliance_score=0.88,
            )
        )

        self.assertEqual(result["gateway_decision"], "approval_required")
        self.assertIn("pause_tool_call", result["enforcement_steps"])

    def test_vap_notify_allowed_for_registered_pilot_agent(self) -> None:
        service = PlatformControlPlaneService(
            agent_registry=AgentRegistryService(),
            identity_service=IdentityRBACService(),
            kill_switch_service=KillSwitchService(),
            policy_simulator=PolicySimulatorService(),
        )
        result = service.gateway_decision(
            GatewayToolRequest(
                tenant_id="bank-demo",
                agent_id="venkat-ai-platform",
                principal_id="vap-orchestrator",
                tool_name="notify.slack",
                action_type="deliver_notification",
                target_system="slack",
                amount_usd=0,
                data_classification=DataClassification.INTERNAL,
                reversible=True,
                customer_impact=False,
                grounding_score=0.9,
                safety_score=0.95,
                policy_compliance_score=0.9,
            )
        )
        self.assertIn(result["gateway_decision"], {"allow", "approval_required"})

    def test_enterprise_rag_high_risk_requires_approval(self) -> None:
        service = PlatformControlPlaneService(
            agent_registry=AgentRegistryService(),
            identity_service=IdentityRBACService(),
            kill_switch_service=KillSwitchService(),
            policy_simulator=PolicySimulatorService(),
        )
        result = service.gateway_decision(
            GatewayToolRequest(
                tenant_id="bank-demo",
                agent_id="enterprise-rag-platform",
                principal_id="enterprise-rag-principal",
                tool_name="rag.high_risk_answer",
                action_type="deliver_answer",
                target_system="enterprise_rag",
                amount_usd=0,
                data_classification=DataClassification.INTERNAL,
                reversible=True,
                customer_impact=False,
                grounding_score=0.9,
                safety_score=0.55,
                policy_compliance_score=0.85,
            )
        )
        self.assertEqual(result["gateway_decision"], "approval_required")
        self.assertIn("pause_tool_call", result["enforcement_steps"])

    def test_revoked_agent_denied_at_gateway(self) -> None:
        registry = AgentRegistryService()
        registry.update_agent_status("venkat-ai-platform", "revoked")
        service = PlatformControlPlaneService(
            agent_registry=registry,
            identity_service=IdentityRBACService(),
            kill_switch_service=KillSwitchService(),
            policy_simulator=PolicySimulatorService(),
        )
        result = service.gateway_decision(
            GatewayToolRequest(
                tenant_id="bank-demo",
                agent_id="venkat-ai-platform",
                principal_id="vap-orchestrator",
                tool_name="notify.slack",
                action_type="deliver_notification",
                target_system="slack",
                amount_usd=0,
                data_classification=DataClassification.INTERNAL,
                reversible=True,
                customer_impact=False,
                grounding_score=0.9,
                safety_score=0.95,
                policy_compliance_score=0.9,
            )
        )
        self.assertEqual(result["gateway_decision"], "deny")

    def test_top_tier_product_surfaces_explain_gateway_policy_and_audit(self) -> None:
        registry = AgentRegistryService()
        identity = IdentityRBACService()
        service = PlatformControlPlaneService(
            agent_registry=registry,
            identity_service=identity,
            kill_switch_service=KillSwitchService(),
            policy_simulator=PolicySimulatorService(),
        )
        request = GatewayToolRequest(
            tenant_id="bank-demo",
            agent_id="agent-refund",
            principal_id="execution-broker",
            tool_name="payments.issue_refund",
            action_type="issue_refund",
            target_system="payments",
            amount_usd=2500,
            data_classification=DataClassification.CONFIDENTIAL,
            reversible=True,
            customer_impact=True,
            grounding_score=0.9,
            safety_score=0.95,
            policy_compliance_score=0.88,
        )

        gateway_story = service.gateway_story()
        quickstart = service.developer_quickstart()
        policy_studio = service.policy_studio_dry_run(request)
        audit_vault = service.audit_vault_posture()
        demo = service.regulated_customer_ops_demo()
        graph = identity.graph(registry.list_agents())

        self.assertEqual(gateway_story["category"], "Agent Governance Gateway")
        self.assertIn("/api/gateway/tool-request", quickstart["steps"][3])
        self.assertEqual(policy_studio["product_module"], "Policy Studio")
        self.assertGreater(policy_studio["blast_radius"]["estimated_monthly_intercepts"], 0)
        self.assertEqual(audit_vault["product_module"], "Assurance Vault")
        self.assertEqual(demo["scenario"], "Regulated Customer Operations")
        self.assertGreater(len(graph["nodes"]), 5)

    def test_top_one_percent_surfaces_define_adoption_release_and_incident_maturity(self) -> None:
        registry = AgentRegistryService()
        identity = IdentityRBACService()
        kill_switch = KillSwitchService()
        service = PlatformControlPlaneService(
            agent_registry=registry,
            identity_service=identity,
            kill_switch_service=kill_switch,
            policy_simulator=PolicySimulatorService(),
        )
        request = GatewayToolRequest(
            tenant_id="bank-demo",
            agent_id="agent-refund",
            principal_id="execution-broker",
            tool_name="payments.issue_refund",
            action_type="issue_refund",
            target_system="payments",
            amount_usd=2500,
            data_classification=DataClassification.CONFIDENTIAL,
            reversible=True,
            customer_impact=True,
            grounding_score=0.9,
            safety_score=0.95,
            policy_compliance_score=0.88,
        )

        registry.register_agent(
            agent_id="agent-claims-copilot",
            name="Claims Copilot",
            owner="Customer Operations",
            business_domain="Claims",
            risk_tier="high",
            autonomy_level=2,
            allowed_tools=("rag.search_policy_memory",),
            data_classes=("internal", "confidential"),
        )
        lifecycle = registry.lifecycle()
        matrix = identity.permission_matrix(registry.list_agents())
        replay = service.historical_policy_replay(request)
        release_gate = service.release_promotion_gate("agent-refund", "refund-agent-v2", "ai-platform-lead")
        sdk = service.gateway_sdk_packages()
        deployment = service.deployment_posture()
        demo_flow = service.flagship_demo_flow()
        incident = kill_switch.incident_timeline()

        self.assertTrue(any(agent["agent_id"] == "agent-claims-copilot" for agent in lifecycle["agents"]))
        self.assertEqual(matrix["product_module"], "Permission Matrix")
        self.assertGreaterEqual(replay["cases_replayed"], 3)
        self.assertEqual(release_gate["decision"], "promote")
        self.assertIn("aegisai-gateway-python", {package["name"] for package in sdk["packages"]})
        self.assertEqual(deployment["tracks"][2]["name"], "AWS enterprise")
        self.assertEqual(demo_flow["product_module"], "Flagship Demo")
        self.assertEqual(incident["product_module"], "Incident Timeline")


if __name__ == "__main__":
    unittest.main()
