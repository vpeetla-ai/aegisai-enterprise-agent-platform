from __future__ import annotations

from dataclasses import dataclass

from aegisai.domain import DataClassification

from .agent_registry import AgentRegistryService, RegisteredAgent
from .identity_rbac import IdentityRBACService
from .kill_switch import KillSwitchService
from .policy_simulator import PolicySimulationInput, PolicySimulatorService


@dataclass(frozen=True)
class AgentOnboardingInput:
    agent_id: str
    name: str
    owner: str
    business_domain: str
    risk_tier: str
    autonomy_level: int
    tools: tuple[str, ...]
    data_classes: tuple[str, ...]
    eval_suite_attached: bool
    policy_attached: bool
    observability_enabled: bool
    kill_switch_enabled: bool


@dataclass(frozen=True)
class GatewayToolRequest:
    tenant_id: str
    agent_id: str
    principal_id: str
    tool_name: str
    action_type: str
    target_system: str
    amount_usd: float
    data_classification: DataClassification
    reversible: bool
    customer_impact: bool
    grounding_score: float
    safety_score: float
    policy_compliance_score: float


class PlatformControlPlaneService:
    """Product layer for enterprise agent governance posture and runtime controls."""

    def __init__(
        self,
        agent_registry: AgentRegistryService,
        identity_service: IdentityRBACService,
        kill_switch_service: KillSwitchService,
        policy_simulator: PolicySimulatorService,
    ) -> None:
        self.agent_registry = agent_registry
        self.identity_service = identity_service
        self.kill_switch_service = kill_switch_service
        self.policy_simulator = policy_simulator

    def risk_posture(self) -> dict[str, object]:
        summary = self.agent_registry.summary()
        agent_count = int(summary["total_agents"])
        high_risk = int(summary["high_or_critical_risk"])
        incidents = int(summary["open_incidents"])
        active_freezes = int(self.kill_switch_service.posture()["active_rule_count"])
        posture_score = max(0, 100 - (high_risk * 8) - (incidents * 12) - (active_freezes * 10))
        return {
            "product_module": "Command",
            "headline": "Enterprise-wide agent governance posture",
            "posture_score": posture_score,
            "board_metrics": [
                {"label": "Registered agents", "value": agent_count, "meaning": "Known agent inventory"},
                {"label": "High or critical risk", "value": high_risk, "meaning": "Agents needing stronger controls"},
                {
                    "label": "Monthly AI cost",
                    "value": f"${summary['monthly_cost_usd']}",
                    "meaning": "Known recurring agent spend",
                },
                {"label": "Open incidents", "value": incidents, "meaning": "Active governance exceptions"},
                {"label": "Active freezes", "value": active_freezes, "meaning": "Agents/tools/workflows paused"},
            ],
            "executive_summary": (
                "AegisAI is the system of control for agent ownership, tool authority, risk, "
                "approval, evaluation, observability, audit, and incident response."
            ),
            "recommended_actions": [
                "Onboard all production and shadow agents into the registry.",
                "Route high-risk side-effecting tool calls through the governance gateway.",
                "Attach golden eval suites before promoting prompt, model, retrieval, or tool changes.",
                "Enable kill switches for every high-risk tool and tenant workflow.",
            ],
        }

    def onboarding_plan(self, payload: AgentOnboardingInput) -> dict[str, object]:
        controls = [
            ("Owner assigned", bool(payload.owner), "Required so every agent has business accountability."),
            ("Policy attached", payload.policy_attached, "Required before the agent can act on enterprise data."),
            ("Eval suite attached", payload.eval_suite_attached, "Required before model/prompt/retrieval promotion."),
            ("Observability enabled", payload.observability_enabled, "Required for trace, cost, latency, and drift review."),
            ("Kill switch enabled", payload.kill_switch_enabled, "Required for incident response and freeze controls."),
            ("Tool scopes declared", bool(payload.tools), "Required for tool-sprawl governance."),
            ("Data classes declared", bool(payload.data_classes), "Required for privacy and compliance routing."),
        ]
        passed = sum(1 for _, ok, _ in controls if ok)
        readiness_score = round((passed / len(controls)) * 100)
        missing = [label for label, ok, _ in controls if not ok]
        launch_decision = self._launch_decision(readiness_score, payload.risk_tier)
        return {
            "product_module": "Onboard",
            "agent_id": payload.agent_id,
            "name": payload.name,
            "owner": payload.owner,
            "business_domain": payload.business_domain,
            "risk_tier": payload.risk_tier,
            "autonomy_level": payload.autonomy_level,
            "readiness_score": readiness_score,
            "launch_decision": launch_decision,
            "missing_controls": missing,
            "required_approver": "AI risk council" if payload.risk_tier in {"high", "critical"} else "AI platform owner",
            "control_checklist": [
                {"control": label, "passed": ok, "why_it_matters": detail}
                for label, ok, detail in controls
            ],
        }

    def readiness_score(self, agent_id: str) -> dict[str, object]:
        agent = next(
            (registered for registered in self.agent_registry.list_agents() if registered.agent_id == agent_id),
            None,
        )
        if agent is None:
            return {
                "product_module": "Readiness",
                "agent_id": agent_id,
                "readiness_score": 0,
                "launch_decision": "not_registered",
                "missing_controls": ["Agent must be registered before readiness can be assessed."],
                "controls": [],
            }
        return self._registered_agent_readiness(agent)

    def gateway_decision(self, request: GatewayToolRequest) -> dict[str, object]:
        kill_rule = self.kill_switch_service.is_blocked(
            request.tenant_id,
            agent_id=request.agent_id,
            tool_name=request.tool_name,
        )
        if kill_rule:
            return {
                "product_module": "Governance Gateway",
                "gateway_decision": "frozen",
                "tool_name": request.tool_name,
                "agent_id": request.agent_id,
                "business_explanation": "The tool or agent is frozen by an active incident kill switch.",
                "enforcement_steps": ["stop_execution", "record_audit_event", "notify_incident_owner"],
                "kill_switch": self.kill_switch_service._payload(kill_rule),
            }

        authorization = self.identity_service.authorize_tool(
            principal_id=request.principal_id,
            tenant_id=request.tenant_id,
            tool_name=request.tool_name,
        )
        if not authorization.allowed:
            return {
                "product_module": "Governance Gateway",
                "gateway_decision": "deny",
                "tool_name": request.tool_name,
                "agent_id": request.agent_id,
                "business_explanation": authorization.reason,
                "enforcement_steps": ["deny_tool_call", "record_audit_event", "notify_agent_owner"],
                "authorization": {
                    "allowed": authorization.allowed,
                    "reason": authorization.reason,
                    "required": authorization.required,
                },
            }

        simulation = self.policy_simulator.simulate(
            PolicySimulationInput(
                tenant_id=request.tenant_id,
                action_type=request.action_type,
                target_system=request.target_system,
                amount_usd=request.amount_usd,
                data_classification=request.data_classification,
                reversible=request.reversible,
                customer_impact=request.customer_impact,
                model_confidence=0.86,
                grounding_score=request.grounding_score,
                safety_score=request.safety_score,
                policy_compliance_score=request.policy_compliance_score,
            )
        )
        gateway_decision = {
            "auto_approve": "allow",
            "approve": "allow",
            "review": "approval_required",
            "escalate": "approval_required",
            "block": "block",
        }.get(str(simulation["decision"]), "approval_required")
        deploy_tools = {
            "deploy.vercel_release",
            "deploy.render_release",
            "github.create_pull_request",
        }
        if request.tool_name in deploy_tools or request.action_type.startswith("deploy_"):
            gateway_decision = "approval_required"
            simulation = {
                **simulation,
                "decision": "human_approval",
                "explanation": (
                    "Production deploy tools always require human approval before execution."
                ),
            }
        steps = ["authorize_identity", "score_risk", "evaluate_policy"]
        if gateway_decision == "allow":
            steps.extend(["issue_execution_token", "record_audit_event"])
        elif gateway_decision == "approval_required":
            steps.extend(["create_review_task", "pause_tool_call", "record_audit_event"])
        else:
            steps.extend(["block_tool_call", "record_audit_event"])
        return {
            "product_module": "Governance Gateway",
            "gateway_decision": gateway_decision,
            "tool_name": request.tool_name,
            "agent_id": request.agent_id,
            "business_explanation": simulation["explanation"],
            "policy_result": simulation,
            "authorization": {
                "allowed": authorization.allowed,
                "reason": authorization.reason,
                "required": authorization.required,
            },
            "enforcement_steps": steps,
        }

    def integration_posture(self) -> dict[str, object]:
        return {
            "product_module": "Integrations",
            "integration_strategy": "Govern any agent, not only AegisAI-built agents.",
            "agent_frameworks": [
                {
                    "name": "LangGraph",
                    "mode": "native reference workload",
                    "value": "Proves supervised multi-agent orchestration, shared context, RAG, evals, and HITL.",
                },
                {
                    "name": "OpenAI Agents / API",
                    "mode": "gateway and trace adapter",
                    "value": "Route tool calls through policy, RBAC, eval, approval, and audit controls.",
                },
                {
                    "name": "AWS Bedrock Agents",
                    "mode": "enterprise cloud adapter",
                    "value": "Use Bedrock for managed agents while AegisAI owns governance evidence.",
                },
                {
                    "name": "Copilot Studio / Agentforce",
                    "mode": "bring-your-own-agent registry",
                    "value": "Register business agents and monitor ownership, risk, tools, and cost.",
                },
            ],
            "enterprise_connectors": [
                "Slack / Microsoft Teams approvals",
                "ServiceNow / Jira incidents",
                "Datadog / OpenTelemetry metrics",
                "Langfuse / LangSmith traces",
                "S3 / GRC audit archive",
                "Postgres pgvector / OpenSearch retrieval",
            ],
        }

    def gateway_story(self) -> dict[str, object]:
        return {
            "product_module": "Governance Gateway",
            "headline": "Stop unsafe agent actions before they hit production systems.",
            "category": "Agent Governance Gateway",
            "buyer_promise": (
                "AegisAI intercepts side-effecting agent tool calls, scores risk, checks identity "
                "and policy, pauses for HITL when needed, issues scoped execution tokens, and "
                "signs the evidence packet."
            ),
            "flow": [
                {"step": "Agent requests tool", "control": "Normalize tool call and agent identity."},
                {"step": "Gateway intercepts", "control": "Evaluate tenant, principal, tool scope, and kill switches."},
                {"step": "Policy and eval gates", "control": "Risk score, evidence quality, and compliance checks."},
                {"step": "HITL or auto-decision", "control": "Approve, block, freeze, or issue scoped execution token."},
                {"step": "Broker executes safely", "control": "Idempotent action with rollback metadata."},
                {"step": "Assurance packet", "control": "Signed trace, decision, reviewer, cost, and control evidence."},
            ],
            "supported_runtimes": [
                "LangGraph",
                "OpenAI Agents SDK",
                "AWS Bedrock Agents",
                "MCP servers",
                "Copilot Studio / Agentforce",
                "Custom Python or TypeScript agents",
            ],
        }

    def developer_quickstart(self) -> dict[str, object]:
        return {
            "product_module": "Developer Integration",
            "headline": "Integrate a governed agent in 15 minutes.",
            "steps": [
                "Register the agent and owner in the inventory.",
                "Attach tool scopes, data classes, and a policy pack.",
                "Run readiness, golden eval, and red-team gates.",
                "Send side-effecting tool calls to /api/gateway/tool-request.",
                "Use the execution token only when the gateway returns allow.",
                "Export a signed audit packet for every regulated case.",
            ],
            "python": (
                "decision = aegis.gateway.tool_request(agent_id='agent-refund', "
                "tool_name='payments.issue_refund', amount_usd=2500)\n"
                "if decision.gateway_decision == 'allow':\n"
                "    payments.issue_refund(token=decision.execution_token)"
            ),
            "typescript": (
                "const decision = await aegis.gateway.toolRequest({ agentId, toolName, amountUsd });\n"
                "if (decision.gatewayDecision === 'allow') await tool.execute(decision.executionToken);"
            ),
            "production_requirements": [
                "Postgres with tenant isolation for system-of-record state.",
                "OIDC principal identity and scoped execution tokens.",
                "OPA or managed policy engine for enterprise policy packs.",
                "OpenTelemetry/Langfuse/LangSmith trace export as adapters, not source of truth.",
            ],
        }

    def gateway_sdk_packages(self) -> dict[str, object]:
        return {
            "product_module": "Gateway SDKs",
            "headline": "Make AegisAI installable from any agent runtime.",
            "packages": [
                {
                    "name": "aegisai-gateway-python",
                    "runtime": "Python",
                    "status": "reference_contract",
                    "install": "uv add aegisai-gateway-python",
                    "adapter": "LangGraph middleware and OpenAI Agents SDK tool wrapper",
                },
                {
                    "name": "@aegisai/gateway",
                    "runtime": "TypeScript",
                    "status": "reference_contract",
                    "install": "npm install @aegisai/gateway",
                    "adapter": "Node/Next.js agent tool wrapper and generic fetch interceptor",
                },
                {
                    "name": "aegisai-mcp-proxy",
                    "runtime": "MCP",
                    "status": "implemented_proxy_contract",
                    "install": "docker run aegisai/mcp-proxy",
                    "adapter": "MCP server gateway with identity, policy, and audit controls",
                },
            ],
            "contract": {
                "request_endpoint": "/api/gateway/tool-request",
                "execution_token_header": "X-AegisAI-Execution-Token",
                "required_fields": [
                    "tenant_id",
                    "agent_id",
                    "principal_id",
                    "tool_name",
                    "action_type",
                    "target_system",
                    "data_classification",
                ],
            },
            "definition_of_done": [
                "SDK wraps every side-effecting tool call.",
                "SDK supports local dry-run and production enforcement modes.",
                "SDK emits OpenTelemetry trace IDs and AegisAI audit IDs.",
                "SDK fails closed when gateway is unavailable for high-risk tools.",
            ],
        }

    def policy_studio_dry_run(self, request: GatewayToolRequest) -> dict[str, object]:
        simulation = self.gateway_decision(request)
        decision = simulation["gateway_decision"]
        return {
            "product_module": "Policy Studio",
            "policy_name": "regulated-customer-ops-v3",
            "draft_rule": (
                "IF tool is side-effecting AND amount_usd >= 1000 AND data_classification "
                "in confidential/restricted THEN require senior approver and signed audit."
            ),
            "dry_run_decision": decision,
            "generated_policy_preview": {
                "engine": "OPA/Rego compatible",
                "version": "policy-2026.05.26-draft",
                "conditions": [
                    "input.tool.side_effecting == true",
                    "input.amount_usd >= 1000",
                    "input.data_classification in {confidential, restricted}",
                ],
                "effect": "require_approval" if decision == "approval_required" else decision,
            },
            "blast_radius": {
                "agents_impacted": ["agent-refund", "agent-data-ops", "agent-it-ops"],
                "tools_impacted": [
                    "payments.issue_refund",
                    "privacy.modify_or_delete_data",
                    "infra.change_production_configuration",
                ],
                "estimated_monthly_intercepts": 860,
                "expected_review_increase_percent": 14,
            },
            "promotion_checklist": [
                "Run against last 30 days of audit packets.",
                "Attach golden eval and red-team regression results.",
                "Obtain AI risk council approval for high-risk workflows.",
                "Promote policy with versioned rollback metadata.",
            ],
            "gateway_result": simulation,
        }

    def historical_policy_replay(self, request: GatewayToolRequest) -> dict[str, object]:
        proposed = self.policy_studio_dry_run(request)
        replay_cases = [
            {
                "case_id": "case-ui-1",
                "historical_decision": "escalate",
                "new_decision": proposed["dry_run_decision"],
                "changed": proposed["dry_run_decision"] != "approval_required",
                "business_impact": "High-value refund remains approval gated.",
            },
            {
                "case_id": "case-ui-2",
                "historical_decision": "block",
                "new_decision": "block",
                "changed": False,
                "business_impact": "Restricted data action remains blocked.",
            },
            {
                "case_id": "case-ui-3",
                "historical_decision": "auto_approve",
                "new_decision": "allow",
                "changed": True,
                "business_impact": "Low-risk fee adjustment can remain automated.",
            },
        ]
        changed = sum(1 for item in replay_cases if item["changed"])
        return {
            "product_module": "Historical Policy Replay",
            "headline": "Preview how a new policy would affect prior agent actions.",
            "policy_name": proposed["policy_name"],
            "lookback_window": "30 days",
            "cases_replayed": len(replay_cases),
            "changed_decisions": changed,
            "review_load_delta_percent": proposed["blast_radius"]["expected_review_increase_percent"],
            "recommendation": (
                "Safe to promote after AI risk council approval."
                if changed <= 1
                else "Hold promotion and review changed decision set."
            ),
            "cases": replay_cases,
        }

    def release_promotion_gate(self, agent_id: str, version: str, requested_by: str) -> dict[str, object]:
        readiness = self.readiness_score(agent_id)
        eval_gate = {
            "golden_eval": "pass",
            "red_team_eval": "pass_with_monitoring",
            "policy_replay": "pass",
            "observability": "pass",
            "rollback_plan": "pass",
        }
        blocking = [
            gate for gate, result in eval_gate.items()
            if result not in {"pass", "pass_with_monitoring"}
        ]
        decision = (
            "promote"
            if readiness["readiness_score"] >= 85 and not blocking
            else "hold"
        )
        return {
            "product_module": "Agent Release Governance",
            "headline": "Promote prompt, model, retrieval, and tool changes only after release gates pass.",
            "agent_id": agent_id,
            "release_version": version,
            "requested_by": requested_by,
            "decision": decision,
            "readiness_score": readiness["readiness_score"],
            "gates": eval_gate,
            "required_approver": "AI risk council" if decision == "promote" else "AI platform owner",
            "promotion_steps": [
                "Attach release diff for prompt/model/retrieval/tool changes.",
                "Run golden eval and red-team eval suites.",
                "Replay candidate policy against historical audit packets.",
                "Verify rollback plan and execution-token compatibility.",
                "Record approval and promote with immutable release metadata.",
            ],
        }

    def deployment_posture(self) -> dict[str, object]:
        return {
            "product_module": "Production Deployment Posture",
            "headline": "Clear local, low-cost cloud, and AWS enterprise deployment tracks.",
            "tracks": [
                {
                    "name": "Local demo",
                    "fit": "Portfolio walkthrough and interviews",
                    "runtime": "Next.js + FastAPI + SQLite + in-memory vector store",
                    "monthly_cost": "$0",
                    "controls": ["demo auth", "signed audit packets", "local policy engine"],
                },
                {
                    "name": "Low-cost cloud",
                    "fit": "Public portfolio demo",
                    "runtime": "Vercel web + Render API + Neon Postgres",
                    "monthly_cost": "$0-$25",
                    "controls": ["Postgres system of record", "hosted API", "demo-mode connectors"],
                },
                {
                    "name": "AWS enterprise",
                    "fit": "Regulated enterprise reference architecture",
                    "runtime": "ECS/App Runner + RDS Postgres + S3 audit vault + Secrets Manager + CloudWatch",
                    "monthly_cost": "$80-$300 for small always-on pilot",
                    "controls": ["VPC", "KMS", "WAF", "OIDC", "RLS", "OpenTelemetry"],
                },
            ],
            "production_line": (
                "Local SQLite is acceptable for demos only; production uses Postgres with tenant "
                "isolation, signed audit retention, managed secrets, and deployment smoke tests."
            ),
        }

    def flagship_demo_flow(self) -> dict[str, object]:
        return {
            "product_module": "Flagship Demo",
            "headline": "One flawless buyer demo: governed refund agent from request to signed audit.",
            "talk_track": (
                "A customer asks for a $2,500 refund. The agent retrieves policy context, AegisAI "
                "intercepts the refund tool, policy requires human approval, a scoped execution "
                "token is issued, the broker executes, and a signed audit packet proves the outcome."
            ),
            "steps": [
                {"step": "Customer request", "buyer_message": "Agents begin with business intent and tenant context."},
                {"step": "RAG evidence", "buyer_message": "The answer is grounded in policy memory before action."},
                {"step": "Gateway intercept", "buyer_message": "Side effects cannot bypass policy and identity checks."},
                {"step": "Policy replay", "buyer_message": "Risk leaders can preview decision changes before rollout."},
                {"step": "Human approval", "buyer_message": "High-risk actions pause for the right approver."},
                {"step": "Execution token", "buyer_message": "Only approved actions receive scoped execution authority."},
                {"step": "Broker execution", "buyer_message": "Enterprise tools are called through controlled connectors."},
                {"step": "Signed audit", "buyer_message": "Compliance gets a tamper-evident evidence packet."},
                {"step": "FinOps ROI", "buyer_message": "Leadership sees cost, minutes saved, and loss prevented."},
            ],
            "success_criteria": [
                "No side-effecting tool executes without gateway decision.",
                "High-risk refund requires reviewer approval.",
                "Execution uses scoped token.",
                "Audit packet verifies successfully.",
                "FinOps dashboard explains business value.",
            ],
        }

    def audit_vault_posture(self) -> dict[str, object]:
        return {
            "product_module": "Assurance Vault",
            "headline": "Board-ready evidence for every regulated agent action.",
            "retention_policy": "7 years for regulated workflows, 13 months for low-risk telemetry.",
            "evidence_types": [
                "Agent identity and owner",
                "Original user request",
                "Tool request and normalized arguments",
                "Risk score and policy decision",
                "Evaluation and retrieval evidence",
                "Reviewer identity and HITL decision",
                "Execution result and rollback metadata",
                "Cost and ROI attribution",
                "Tamper-evident signature block",
            ],
            "compliance_mapping": [
                {"framework": "NIST AI RMF", "controls": ["Govern", "Map", "Measure", "Manage"]},
                {"framework": "SOC 2", "controls": ["Change management", "Logical access", "Monitoring"]},
                {"framework": "EU AI Act style readiness", "controls": ["Human oversight", "Logging", "Risk management"]},
            ],
            "export_formats": ["signed JSON", "PDF", "GRC archive bundle"],
        }

    def regulated_customer_ops_demo(self) -> dict[str, object]:
        return {
            "product_module": "Reference Workload",
            "scenario": "Regulated Customer Operations",
            "story": (
                "A customer-support agent wants to issue a refund, update CRM notes, send a "
                "customer message, and access sensitive account context. AegisAI governs each "
                "side-effecting step before production impact."
            ),
            "business_problem": [
                "Agents can create financial loss through unchecked refunds.",
                "Agents can leak sensitive data through customer communications.",
                "Teams cannot prove why an autonomous action was allowed or blocked.",
            ],
            "governed_steps": [
                {"action": "Search policy memory", "decision": "allow", "why": "Read-only RAG with tenant-scoped memory."},
                {"action": "Issue $2,500 refund", "decision": "approval_required", "why": "High-value customer-impacting payment."},
                {"action": "Update CRM case", "decision": "allow_with_audit", "why": "Low-risk operational update after approval."},
                {"action": "Send customer message", "decision": "evaluate_tone_and_compliance", "why": "Customer-facing language must pass guardrails."},
                {"action": "Export audit packet", "decision": "signed", "why": "Finance and compliance need immutable evidence."},
            ],
            "buyer_value": [
                "Reduces agent sprawl by forcing every agent into the registry.",
                "Reduces tool sprawl by centralizing runtime permissions.",
                "Closes audit gaps with signed evidence packets.",
                "Controls unmanaged cost with workflow-level FinOps.",
            ],
        }

    def _registered_agent_readiness(self, agent: RegisteredAgent) -> dict[str, object]:
        controls = [
            ("Registered owner", True, "Owner and domain are known."),
            ("Tool scopes declared", bool(agent.allowed_tools), "Tool permissions are visible."),
            ("Data classes declared", bool(agent.data_classes), "Data sensitivity is visible."),
            ("Observability attached", True, "Reference workload emits traces and control-plane events."),
            ("Kill switch available", agent.risk_tier in {"high", "critical"} or agent.status == "approved", "Freeze path exists."),
            ("Eval suite attached", agent.status in {"approved", "restricted"}, "Release quality is gated."),
            ("Production approved", agent.status == "approved", "Pilot/restricted agents need signoff."),
        ]
        passed = sum(1 for _, ok, _ in controls if ok)
        readiness_score = round((passed / len(controls)) * 100)
        return {
            "product_module": "Readiness",
            "agent_id": agent.agent_id,
            "name": agent.name,
            "readiness_score": readiness_score,
            "launch_decision": self._launch_decision(readiness_score, agent.risk_tier),
            "missing_controls": [label for label, ok, _ in controls if not ok],
            "controls": [
                {"control": label, "passed": ok, "why_it_matters": detail}
                for label, ok, detail in controls
            ],
        }

    def _launch_decision(self, readiness_score: int, risk_tier: str) -> str:
        if readiness_score < 70:
            return "do_not_launch"
        if risk_tier in {"high", "critical"} and readiness_score < 90:
            return "limited_pilot_only"
        if readiness_score < 90:
            return "launch_with_conditions"
        return "production_ready"
