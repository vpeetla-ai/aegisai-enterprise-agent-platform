from __future__ import annotations

import logging
import os
import time
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from aegisai.application.execution import ApprovedActionExecutionBroker
from aegisai.application.execution.connectors.http_connector import HttpConnectorManager
from aegisai.application.execution.tokens import ExecutionTokenService
from aegisai.application.gateway import McpGovernanceProxy, McpToolCallRequest
from aegisai.application.guardrails.opa_policy import OpaPolicyEngine
from aegisai.application.knowledge import SQLiteVectorMemoryStore
from aegisai.application.orchestration import (
    AIContentPipelineOrchestrator,
    BusinessRequest,
    EnterpriseAgentGraph,
    StockResearchOrchestrator,
    WebsiteBuildOrchestrator,
)
from aegisai.application.tools import enterprise_tool_registry
from aegisai.domain import DataClassification, ExecutionCommand, ExecutionResult
from aegisai.infrastructure.persistence import build_control_plane_store
from aegisai.infrastructure.persistence.factory import build_agent_registry_service
from aegisai.interfaces.http.auth import AuthRequired, ReviewerAuthRequired, auth_posture
from aegisai.interfaces.http.enforcement import pilot_mode, require_execution_token
from aegisai.product.gateway_metrics import GatewayMetricsService
from aegisai.product.audit_signing import AuditPacketSigner
from aegisai.observability import build_default_observability_service
from aegisai.observability.models import ExporterStatus
from aegisai.product import (
    AgentCloudService,
    AgentOnboardingInput,
    AgentRegistryService,
    AuditPacketExporter,
    DashboardService,
    FinOpsService,
    GatewayToolRequest,
    GoldenEvalService,
    IdentityRBACService,
    KillSwitchService,
    PlatformControlPlaneService,
    PolicySimulationInput,
    PolicySimulatorService,
    RedTeamEvalService,
    SlackApprovalService,
    UndoRequest,
)


class AgentRunRequest(BaseModel):
    request_id: str = Field(default="case-api-001")
    tenant_id: str = Field(default="bank-demo")
    user_id: str = Field(default="portfolio-user")
    text: str = Field(default="Customer requests a refund for a failed booking")
    amount_usd: float = Field(default=2500)
    data_classification: DataClassification = Field(default=DataClassification.CONFIDENTIAL)
    customer_impact: bool = Field(default=True)


class RAGSearchRequest(BaseModel):
    tenant_id: str = Field(default="bank-demo")
    namespace: str = Field(default="refund_policy")
    query: str = Field(default="refund above 2500 approval threshold")


class ReviewerActionRequest(BaseModel):
    tenant_id: str = Field(default="bank-demo")
    case_id: str
    proposal_id: str
    reviewer_id: str = Field(default="approver-7")
    action: str = Field(pattern="^(approve|reject|request_info|escalate)$")
    reason: str = Field(default="Reviewer decision from control-plane UI.")


class ExecuteActionRequest(BaseModel):
    tenant_id: str = Field(default="bank-demo")
    case_id: str
    proposal_id: str
    actor_id: str = Field(default="execution-broker")
    idempotency_key: str | None = Field(default=None)
    dry_run: bool = Field(default=False)


class PolicySimulationRequest(BaseModel):
    tenant_id: str = Field(default="bank-demo")
    action_type: str = Field(default="issue_refund")
    target_system: str = Field(default="payments")
    amount_usd: float = Field(default=2500)
    data_classification: DataClassification = Field(default=DataClassification.CONFIDENTIAL)
    reversible: bool = Field(default=True)
    customer_impact: bool = Field(default=True)
    model_confidence: float = Field(default=0.86, ge=0, le=1)
    grounding_score: float = Field(default=0.9, ge=0, le=1)
    safety_score: float = Field(default=0.95, ge=0, le=1)
    policy_compliance_score: float = Field(default=0.88, ge=0, le=1)


class KillSwitchRequest(BaseModel):
    scope_type: str = Field(pattern="^(agent|tool|tenant|workflow)$")
    scope_value: str
    reason: str = Field(default="Emergency governance control from product UI.")
    created_by: str = Field(default="security-admin")


class AgentUndoRequest(BaseModel):
    tenant_id: str = Field(default="bank-demo")
    execution_id: str
    reason: str = Field(default="Undo unwanted agent action from Agent Cloud console.")
    actor_id: str = Field(default="security-admin")


class AgentOnboardingRequest(BaseModel):
    agent_id: str = Field(default="agent-salesforce-case-assistant")
    name: str = Field(default="Salesforce Case Assistant")
    owner: str = Field(default="Customer Operations")
    business_domain: str = Field(default="Customer Support")
    risk_tier: str = Field(default="high", pattern="^(low|medium|high|critical)$")
    autonomy_level: int = Field(default=3, ge=0, le=5)
    tools: list[str] = Field(default_factory=lambda: ["crm.update_case", "rag.search_policy_memory"])
    data_classes: list[str] = Field(default_factory=lambda: ["internal", "confidential"])
    eval_suite_attached: bool = Field(default=True)
    policy_attached: bool = Field(default=True)
    observability_enabled: bool = Field(default=True)
    kill_switch_enabled: bool = Field(default=False)


class AgentLifecycleRegisterRequest(BaseModel):
    agent_id: str = Field(default="agent-claims-copilot")
    name: str = Field(default="Claims Copilot")
    owner: str = Field(default="Customer Operations")
    business_domain: str = Field(default="Claims")
    risk_tier: str = Field(default="high", pattern="^(low|medium|high|critical)$")
    autonomy_level: int = Field(default=2, ge=0, le=5)
    status: str = Field(default="pilot", pattern="^(shadow|pilot|restricted|approved|revoked|deprecated)$")
    model_provider: str = Field(default="OpenAI/local fallback")
    allowed_tools: list[str] = Field(default_factory=lambda: ["rag.search_policy_memory"])
    data_classes: list[str] = Field(default_factory=lambda: ["internal", "confidential"])


class AgentLifecycleStatusRequest(BaseModel):
    status: str = Field(pattern="^(shadow|pilot|restricted|approved|revoked|deprecated)$")


class ReleasePromotionRequest(BaseModel):
    agent_id: str = Field(default="agent-refund")
    release_version: str = Field(default="refund-agent-2026.05.26")
    requested_by: str = Field(default="ai-platform-lead")


class SlackApprovalRequest(BaseModel):
    tenant_id: str = Field(default="bank-demo")
    case_id: str
    proposal_id: str
    summary: str = Field(default="High-risk agent action requires approval.")
    risk_level: str = Field(default="high")
    approval_role: str | None = Field(default="workflow_owner")


class SlackInteractionRequest(BaseModel):
    text: str
    reviewer_id: str = Field(default="approver-7")


class AuditPacketVerifyRequest(BaseModel):
    signed_packet: dict[str, object]


class HttpConnectorRegisterRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    connector_id: str | None = Field(default=None, max_length=80)
    base_url: str = Field(min_length=8)
    target_system: str = Field(min_length=2, max_length=64)
    tool_names: list[str] = Field(default_factory=list)
    http_method: str = Field(default="POST")
    execute_path: str = Field(default="/execute")
    health_path: str = Field(default="/health")
    auth_mode: str = Field(default="none", pattern="^(none|bearer|api_key)$")
    auth_header_name: str = Field(default="Authorization")
    auth_secret_env: str | None = Field(default=None)
    auth_value: str | None = Field(default=None, description="Demo-only; not persisted to disk.")
    demo_mode: bool = Field(default=True)


class HttpConnectorTestRequest(BaseModel):
    connector_id: str | None = None
    base_url: str | None = None
    health_path: str = Field(default="/health")
    http_method: str = Field(default="GET")
    auth_mode: str = Field(default="none", pattern="^(none|bearer|api_key)$")
    auth_header_name: str = Field(default="Authorization")
    auth_value: str | None = None
    auth_secret_env: str | None = None
    demo_mode: bool = Field(default=True)


class McpToolCallPayload(BaseModel):
    tenant_id: str = Field(default="bank-demo")
    agent_id: str = Field(default="agent-platform")
    principal_id: str = Field(default="execution-broker")
    mcp_server: str = Field(default="github")
    tool_name: str = Field(default="create_issue")
    arguments: dict[str, object] = Field(default_factory=lambda: {"repo": "aegisai", "title": "Governed MCP call"})
    action_type: str = Field(default="create_issue")
    target_system: str = Field(default="mcp")
    amount_usd: float = Field(default=0)
    data_classification: DataClassification = Field(default=DataClassification.INTERNAL)
    reversible: bool = Field(default=True)
    customer_impact: bool = Field(default=False)


class GatewayToolRequestPayload(BaseModel):
    tenant_id: str = Field(default="bank-demo")
    agent_id: str = Field(default="agent-refund")
    principal_id: str = Field(default="execution-broker")
    tool_name: str = Field(default="payments.issue_refund")
    action_type: str = Field(default="issue_refund")
    target_system: str = Field(default="payments")
    amount_usd: float = Field(default=2500)
    data_classification: DataClassification = Field(default=DataClassification.CONFIDENTIAL)
    reversible: bool = Field(default=True)
    customer_impact: bool = Field(default=True)
    grounding_score: float = Field(default=0.9, ge=0, le=1)
    safety_score: float = Field(default=0.95, ge=0, le=1)
    policy_compliance_score: float = Field(default=0.88, ge=0, le=1)
    proposal_id: str | None = Field(default=None)
    case_id: str | None = Field(default=None)


memory_store = SQLiteVectorMemoryStore(os.getenv("AEGISAI_VECTOR_DB_PATH", ":memory:"))
if memory_store.count() == 0:
    memory_store.seed_enterprise_memory()
agent_graph = EnterpriseAgentGraph(memory_store=memory_store)
control_plane_store = build_control_plane_store()
observability_service = build_default_observability_service()
execution_broker = ApprovedActionExecutionBroker()
http_connector_manager = HttpConnectorManager(execution_broker.connector_registry)
http_connector_manager.bootstrap()
execution_token_service = ExecutionTokenService()
agent_registry_service = build_agent_registry_service()
policy_simulator_service = PolicySimulatorService()
identity_service = IdentityRBACService()
kill_switch_service = KillSwitchService()
golden_eval_service = GoldenEvalService()
red_team_eval_service = RedTeamEvalService()
finops_service = FinOpsService(agent_registry_service)
slack_approval_service = SlackApprovalService()
audit_signer = AuditPacketSigner()
audit_packet_exporter = AuditPacketExporter(signer=audit_signer)
platform_control_plane_service = PlatformControlPlaneService(
    agent_registry=agent_registry_service,
    identity_service=identity_service,
    kill_switch_service=kill_switch_service,
    policy_simulator=policy_simulator_service,
)
mcp_governance_proxy = McpGovernanceProxy(platform_control_plane_service)
gateway_metrics_service = GatewayMetricsService(control_plane_store)
agent_cloud_service = AgentCloudService(
    store=control_plane_store,
    agent_registry=agent_registry_service,
    kill_switch_service=kill_switch_service,
    identity_service=identity_service,
    gateway_metrics=gateway_metrics_service,
)
dashboard_service = DashboardService(
    store=control_plane_store,
    agent_registry=agent_registry_service,
    gateway_metrics=gateway_metrics_service,
    finops=finops_service,
    kill_switch=kill_switch_service,
)
ai_content_orchestrator = AIContentPipelineOrchestrator()
stock_research_orchestrator = StockResearchOrchestrator()


def _website_gateway_decision(**kwargs: object) -> dict[str, object]:
    classification = DataClassification.INTERNAL
    raw = kwargs.get("data_classification", "internal")
    if isinstance(raw, str):
        try:
            classification = DataClassification(raw)
        except ValueError:
            classification = DataClassification.INTERNAL
    request = GatewayToolRequest(
        tenant_id=str(kwargs.get("tenant_id", "bank-demo")),
        agent_id=str(kwargs["agent_id"]),
        principal_id=str(kwargs.get("principal_id", "website-build-pipeline")),
        tool_name=str(kwargs["tool_name"]),
        action_type=str(kwargs["action_type"]),
        target_system=str(kwargs["target_system"]),
        amount_usd=float(kwargs.get("amount_usd", 0)),
        data_classification=classification,
        reversible=bool(kwargs.get("reversible", True)),
        customer_impact=bool(kwargs.get("customer_impact", False)),
        grounding_score=float(kwargs.get("grounding_score", 0.9)),
        safety_score=float(kwargs.get("safety_score", 0.95)),
        policy_compliance_score=float(kwargs.get("policy_compliance_score", 0.92)),
    )
    return platform_control_plane_service.gateway_decision(request)


website_build_orchestrator = WebsiteBuildOrchestrator(
    gateway_fn=_website_gateway_decision,
    observability=observability_service,
)
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "AEGISAI_CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="AegisAI API",
    version="0.1.0",
    description="FastAPI surface for LangGraph multi-agent orchestration, RAG, HITL, and audit.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


@app.middleware("http")
async def security_headers_and_request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.exception(
            "unhandled_request_exception",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "elapsed_ms": elapsed_ms,
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_server_error",
                    "message": "Unexpected server error.",
                    "request_id": request_id,
                }
            },
            headers={"X-Request-Id": request_id},
        )

    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "message": "Request validation failed.",
                "details": exc.errors(),
                "request_id": request_id,
            }
        },
        headers={"X-Request-Id": request_id},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "message": str(exc.detail),
                "request_id": request_id,
            }
        },
        headers={"X-Request-Id": request_id},
    )


@app.get("/health")
def health() -> dict[str, object]:
    persistence = (
        control_plane_store.persistence_backend()
        if hasattr(control_plane_store, "persistence_backend")
        else {"mode": "sqlite"}
    )
    return {
        "status": "ok",
        "service": "aegisai-api",
        "memory_documents": memory_store.count(),
        "audit_chain_valid": control_plane_store.verify_audit_chain("bank-demo"),
        "persistence": persistence,
        "policy_engine": "opa" if OpaPolicyEngine.available() else "builtin",
        "slack_approvals": slack_approval_service.configured,
        "connector_registry": execution_broker.connector_registry.catalog(),
        "connector_count": len(execution_broker.connector_registry.catalog()),
        "audit_signing": audit_signer.posture(),
        "auth": auth_posture(),
        "enforcement": {
            "require_execution_token": require_execution_token(),
            "pilot_mode": pilot_mode(),
            "recommended_persistence": "postgres" if pilot_mode() else "sqlite",
        },
    }


@app.get("/")
def root() -> dict[str, object]:
    return {
        "service": "aegisai-api",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "primary_endpoints": [
            "POST /api/agents/run",
            "POST /api/rag/search",
            "POST /api/control-plane/reviewer-action",
            "POST /api/execution/execute",
            "GET /api/agent-registry",
            "GET /api/agent-registry/lifecycle",
            "POST /api/agent-registry/lifecycle",
            "PATCH /api/agent-registry/lifecycle/{agent_id}/status",
            "GET /api/platform/posture",
            "GET /api/platform/gateway-story",
            "GET /api/platform/developer-quickstart",
            "GET /api/platform/gateway-sdks",
            "GET /api/platform/deployment-posture",
            "GET /api/demo/flagship-flow",
            "POST /api/platform/onboard-agent",
            "GET /api/platform/readiness/{agent_id}",
            "POST /api/gateway/tool-request",
            "GET /api/platform/integrations",
            "POST /api/policy/simulate",
            "POST /api/policy/studio/dry-run",
            "POST /api/policy/replay",
            "POST /api/release-gates/promote",
            "GET /api/product/regulatory-customer-ops-demo",
            "GET /api/audit-packets/{tenant_id}/{case_id}.json",
            "GET /api/audit-packets/{tenant_id}/{case_id}/signed.json",
            "GET /api/audit-packets/{tenant_id}/{case_id}.pdf",
            "GET /api/audit-vault/posture",
            "POST /api/audit-packets/verify",
            "GET /api/auth/posture",
            "GET /api/audit-signing/posture",
            "GET /api/identity/posture",
            "GET /api/identity/graph",
            "GET /api/identity/permission-matrix",
            "GET /api/kill-switches",
            "GET /api/incidents/timeline",
            "POST /api/kill-switches",
            "POST /api/evaluations/golden/run",
            "POST /api/evaluations/red-team/run",
            "GET /api/governance/metrics",
            "GET /api/connectors/catalog",
            "GET /api/connectors/http",
            "POST /api/connectors/http",
            "POST /api/connectors/http/test",
            "DELETE /api/connectors/http/{connector_id}",
            "GET /api/mcp/posture",
            "POST /api/mcp/tool-call",
            "GET /api/finops/dashboard",
            "POST /api/hitl/slack/approval-task",
            "POST /api/hitl/slack/interaction",
            "GET /api/hitl/slack/posture",
            "GET /api/control-plane/metrics",
            "GET /api/observability/status",
        ],
    }


@app.post("/api/agents/run")
def run_agents(payload: AgentRunRequest, auth: AuthRequired) -> dict[str, object]:
    request = BusinessRequest(
        request_id=payload.request_id,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
        text=payload.text,
        amount_usd=payload.amount_usd,
        data_classification=payload.data_classification,
        customer_impact=payload.customer_impact,
    )
    state = agent_graph.invoke(request)
    result = state["orchestration_result"]
    rag_result = state["rag_result"]
    control_plane_store.save_orchestration(result)
    export_statuses = observability_service.export_agent_run(result, rag_result)
    decision = result.context.governance_decisions[0] if result.context.governance_decisions else None
    proposal = result.context.proposed_actions[0] if result.context.proposed_actions else None
    return {
        "request_id": result.request_id,
        "workflow_type": result.workflow_type.value,
        "agents_run": [agent.value for agent in result.agents_run],
        "decision": decision.decision.value if decision else "no_action_proposed",
        "risk_score": decision.risk.score if decision else 0,
        "risk_level": decision.risk.level.value if decision else "none",
        "approval_role": decision.approval_role if decision else None,
        "agent_trace_count": len(result.context.agent_traces),
        "proposal_id": proposal.proposal_id if proposal else None,
        "retrieved_context": [
            {
                "source_uri": document.source_uri,
                "namespace": document.namespace,
                "score": round(score, 4),
                "content": document.content,
            }
            for document, score in zip(rag_result.retrieved_documents, rag_result.scores)
        ],
        "llm": {
            "provider": rag_result.answer.provider,
            "model": rag_result.answer.model,
            "confidence": rag_result.answer.confidence,
            "content": rag_result.answer.content,
        },
        "tools_available": [
            {
                "name": tool.name,
                "owner": tool.owner,
                "side_effecting": tool.side_effecting,
                "approval_required": tool.approval_required,
                "description": tool.description,
            }
            for tool in enterprise_tool_registry()
        ],
        "observability": [_status_payload(status) for status in export_statuses],
    }


@app.post("/api/rag/search")
def search_rag(payload: RAGSearchRequest, auth: AuthRequired) -> dict[str, object]:
    results = memory_store.search(payload.tenant_id, payload.namespace, payload.query)
    return {
        "tenant_id": payload.tenant_id,
        "namespace": payload.namespace,
        "query": payload.query,
        "results": [
            {
                "document_id": document.document_id,
                "source_uri": document.source_uri,
                "score": round(score, 4),
                "content": document.content,
            }
            for document, score in results
        ],
    }


@app.post("/api/control-plane/reviewer-action")
def reviewer_action(
    request: Request,
    payload: ReviewerActionRequest,
    auth: ReviewerAuthRequired,
) -> dict[str, object]:
    reviewer_id = (
        auth.principal_id
        if request.headers.get("X-AegisAI-Principal")
        else payload.reviewer_id
    )
    required_role = control_plane_store.approval_role_for_proposal(payload.tenant_id, payload.proposal_id)
    authorization = identity_service.authorize_reviewer(
        principal_id=reviewer_id,
        tenant_id=payload.tenant_id,
        required_role=required_role,
    )
    if not authorization.allowed:
        return {
            "status": "denied",
            "action": payload.action,
            "authorization": _authorization_payload(authorization),
            "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
        }
    control_plane_store.record_reviewer_action(
        tenant_id=payload.tenant_id,
        case_id=payload.case_id,
        proposal_id=payload.proposal_id,
        reviewer_id=reviewer_id,
        action=payload.action,
        reason=payload.reason,
    )
    execution_token = None
    if payload.action == "approve":
        readiness = control_plane_store.get_execution_readiness(
            payload.tenant_id, payload.proposal_id
        )
        if readiness is not None:
            tool_name = _tool_name(readiness.action_type, readiness.target_system)
            execution_token = execution_token_service.issue(
                tenant_id=payload.tenant_id,
                agent_id="agent-approved",
                tool_name=tool_name,
                gateway_decision="allow",
                proposal_id=payload.proposal_id,
            )
            control_plane_store.append_audit_event(
                tenant_id=payload.tenant_id,
                case_id=payload.case_id,
                event_type="gateway.token_issued",
                subject_id=payload.proposal_id,
                actor_id=reviewer_id,
                payload={"tool_name": tool_name, "source": "reviewer_approve"},
            )
    return {
        "status": "recorded",
        "action": payload.action,
        "reviewer_id": reviewer_id,
        "auth_mode": auth.auth_mode,
        "execution_token": execution_token,
        "authorization": _authorization_payload(authorization),
        "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
    }


@app.post("/api/execution/execute")
def execute_action(
    request: Request,
    payload: ExecuteActionRequest,
    auth: ReviewerAuthRequired,
    execution_token: str | None = Header(default=None, alias="X-AegisAI-Execution-Token"),
) -> dict[str, object]:
    idempotency_key = (
        payload.idempotency_key
        or f"{payload.tenant_id}:{payload.proposal_id}:execute"
    )
    actor_id = (
        auth.principal_id
        if request.headers.get("X-AegisAI-Principal")
        else payload.actor_id
    )
    readiness = control_plane_store.get_execution_readiness(payload.tenant_id, payload.proposal_id)
    tool_name = _tool_name(readiness.action_type, readiness.target_system) if readiness else "unknown"
    token_claims = None

    if require_execution_token() and not payload.dry_run:
        if not execution_token:
            control_plane_store.append_audit_event(
                tenant_id=payload.tenant_id,
                case_id=payload.case_id,
                event_type="execution.denied.no_token",
                subject_id=payload.proposal_id,
                actor_id=actor_id,
                payload={"tool_name": tool_name, "message": "Execution token required."},
            )
            return {
                "execution_id": None,
                "tenant_id": payload.tenant_id,
                "case_id": payload.case_id,
                "proposal_id": payload.proposal_id,
                "status": "denied",
                "message": (
                    "Execution token required. Route tool calls through the governance gateway "
                    "or obtain a token after HITL approval."
                ),
                "require_execution_token": True,
                "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
            }
        token_claims = execution_token_service.verify(execution_token)
        if token_claims is None:
            control_plane_store.append_audit_event(
                tenant_id=payload.tenant_id,
                case_id=payload.case_id,
                event_type="execution.denied.invalid_token",
                subject_id=payload.proposal_id,
                actor_id=actor_id,
                payload={"tool_name": tool_name},
            )
            return {
                "execution_id": None,
                "tenant_id": payload.tenant_id,
                "case_id": payload.case_id,
                "proposal_id": payload.proposal_id,
                "status": "denied",
                "message": "Invalid or expired execution token.",
                "require_execution_token": True,
                "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
            }
        if token_claims.tenant_id != payload.tenant_id:
            return {
                "execution_id": None,
                "tenant_id": payload.tenant_id,
                "case_id": payload.case_id,
                "proposal_id": payload.proposal_id,
                "status": "denied",
                "message": "Execution token tenant mismatch.",
                "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
            }
        if token_claims.proposal_id and token_claims.proposal_id != payload.proposal_id:
            return {
                "execution_id": None,
                "tenant_id": payload.tenant_id,
                "case_id": payload.case_id,
                "proposal_id": payload.proposal_id,
                "status": "denied",
                "message": "Execution token proposal mismatch.",
                "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
            }
        if token_claims.tool_name != tool_name and tool_name != "unknown":
            return {
                "execution_id": None,
                "tenant_id": payload.tenant_id,
                "case_id": payload.case_id,
                "proposal_id": payload.proposal_id,
                "status": "denied",
                "message": f"Execution token tool mismatch (expected {tool_name}).",
                "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
            }
    elif execution_token:
        token_claims = execution_token_service.verify(execution_token)
        if token_claims is None:
            return {
                "execution_id": None,
                "tenant_id": payload.tenant_id,
                "case_id": payload.case_id,
                "proposal_id": payload.proposal_id,
                "status": "denied",
                "message": "Invalid or expired execution token.",
                "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
            }
        if token_claims.tenant_id != payload.tenant_id:
            return {
                "execution_id": None,
                "tenant_id": payload.tenant_id,
                "case_id": payload.case_id,
                "proposal_id": payload.proposal_id,
                "status": "denied",
                "message": "Execution token tenant mismatch.",
                "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
            }
    command = ExecutionCommand(
        tenant_id=payload.tenant_id,
        case_id=payload.case_id,
        proposal_id=payload.proposal_id,
        actor_id=actor_id,
        idempotency_key=idempotency_key,
        dry_run=payload.dry_run,
    )
    kill_rule = kill_switch_service.is_blocked(payload.tenant_id, tool_name=tool_name)
    if kill_rule:
        return {
            "execution_id": None,
            "tenant_id": payload.tenant_id,
            "case_id": payload.case_id,
            "proposal_id": payload.proposal_id,
            "status": "blocked_by_kill_switch",
            "tool_name": tool_name,
            "kill_switch": kill_switch_service._payload(kill_rule),
            "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
        }
    authorization = identity_service.authorize_tool(
        principal_id=actor_id,
        tenant_id=payload.tenant_id,
        tool_name=tool_name,
    )
    if not authorization.allowed:
        return {
            "execution_id": None,
            "tenant_id": payload.tenant_id,
            "case_id": payload.case_id,
            "proposal_id": payload.proposal_id,
            "status": "denied",
            "tool_name": tool_name,
            "authorization": _authorization_payload(authorization),
            "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
        }
    result = execution_broker.execute(command, readiness)
    control_plane_store.record_execution_result(result, actor_id=actor_id)
    if result.status.value == "executed" and token_claims is not None:
        control_plane_store.append_audit_event(
            tenant_id=payload.tenant_id,
            case_id=payload.case_id,
            event_type="execution.token_bound",
            subject_id=payload.proposal_id,
            actor_id=actor_id,
            payload={
                "tool_name": tool_name,
                "execution_id": result.execution_id,
                "connector": result.connector,
            },
        )
    return {
        **_execution_payload(result),
        "tool_name": tool_name,
        "actor_id": actor_id,
        "execution_token_required": require_execution_token(),
        "execution_token_bound": token_claims is not None,
        "authorization": _authorization_payload(authorization),
        "audit_chain_valid": control_plane_store.verify_audit_chain(payload.tenant_id),
    }


@app.get("/api/agent-registry")
def agent_registry() -> dict[str, object]:
    agents = agent_registry_service.list_agents()
    return {
        "product_module": "Discover",
        "summary": agent_registry_service.summary(),
        "agents": [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "owner": agent.owner,
                "business_domain": agent.business_domain,
                "risk_tier": agent.risk_tier,
                "autonomy_level": agent.autonomy_level,
                "status": agent.status,
                "model_provider": agent.model_provider,
                "allowed_tools": list(agent.allowed_tools),
                "data_classes": list(agent.data_classes),
                "last_run_at": agent.last_run_at,
                "monthly_cost_usd": agent.monthly_cost_usd,
                "open_incidents": agent.open_incidents,
                "value_metric": agent.value_metric,
            }
            for agent in agents
        ],
    }


@app.get("/api/agent-registry/lifecycle")
def agent_registry_lifecycle() -> dict[str, object]:
    return agent_registry_service.lifecycle()


@app.post("/api/agent-registry/lifecycle")
def register_agent_lifecycle(payload: AgentLifecycleRegisterRequest, auth: AuthRequired) -> dict[str, object]:
    agent = agent_registry_service.register_agent(
        agent_id=payload.agent_id,
        name=payload.name,
        owner=payload.owner,
        business_domain=payload.business_domain,
        risk_tier=payload.risk_tier,
        autonomy_level=payload.autonomy_level,
        allowed_tools=tuple(payload.allowed_tools),
        data_classes=tuple(payload.data_classes),
        status=payload.status,
        model_provider=payload.model_provider,
    )
    return {
        "status": "registered",
        "registered_by": auth.principal_id,
        "agent": agent_registry_service.to_payload(agent),
        "lifecycle": agent_registry_service.lifecycle(),
    }


@app.patch("/api/agent-registry/lifecycle/{agent_id}/status")
def update_agent_lifecycle_status(
    agent_id: str,
    payload: AgentLifecycleStatusRequest,
    auth: AuthRequired,
) -> dict[str, object]:
    agent = agent_registry_service.update_agent_status(agent_id, payload.status)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {
        "status": "updated",
        "updated_by": auth.principal_id,
        "agent": agent_registry_service.to_payload(agent),
        "lifecycle": agent_registry_service.lifecycle(),
    }


@app.get("/api/platform/posture")
def platform_posture() -> dict[str, object]:
    return platform_control_plane_service.risk_posture()


@app.get("/api/platform/gateway-story")
def gateway_story() -> dict[str, object]:
    return platform_control_plane_service.gateway_story()


@app.get("/api/platform/developer-quickstart")
def developer_quickstart() -> dict[str, object]:
    return platform_control_plane_service.developer_quickstart()


@app.get("/api/platform/gateway-sdks")
def gateway_sdk_packages() -> dict[str, object]:
    return platform_control_plane_service.gateway_sdk_packages()


@app.get("/api/platform/deployment-posture")
def deployment_posture() -> dict[str, object]:
    return platform_control_plane_service.deployment_posture()


@app.get("/api/demo/flagship-flow")
def flagship_demo_flow() -> dict[str, object]:
    return platform_control_plane_service.flagship_demo_flow()


@app.post("/api/platform/onboard-agent")
def onboard_agent(payload: AgentOnboardingRequest, auth: AuthRequired) -> dict[str, object]:
    return platform_control_plane_service.onboarding_plan(
        AgentOnboardingInput(
            agent_id=payload.agent_id,
            name=payload.name,
            owner=payload.owner,
            business_domain=payload.business_domain,
            risk_tier=payload.risk_tier,
            autonomy_level=payload.autonomy_level,
            tools=tuple(payload.tools),
            data_classes=tuple(payload.data_classes),
            eval_suite_attached=payload.eval_suite_attached,
            policy_attached=payload.policy_attached,
            observability_enabled=payload.observability_enabled,
            kill_switch_enabled=payload.kill_switch_enabled,
        )
    )


@app.get("/api/platform/readiness/{agent_id}")
def agent_readiness(agent_id: str) -> dict[str, object]:
    return platform_control_plane_service.readiness_score(agent_id)


@app.post("/api/gateway/tool-request")
def gateway_tool_request(
    request: Request,
    payload: GatewayToolRequestPayload,
    auth: AuthRequired,
) -> dict[str, object]:
    principal_id = (
        auth.principal_id
        if request.headers.get("X-AegisAI-Principal")
        else payload.principal_id
    )
    decision_payload = platform_control_plane_service.gateway_decision(
        GatewayToolRequest(
            tenant_id=payload.tenant_id,
            agent_id=payload.agent_id,
            principal_id=principal_id,
            tool_name=payload.tool_name,
            action_type=payload.action_type,
            target_system=payload.target_system,
            amount_usd=payload.amount_usd,
            data_classification=payload.data_classification,
            reversible=payload.reversible,
            customer_impact=payload.customer_impact,
            grounding_score=payload.grounding_score,
            safety_score=payload.safety_score,
            policy_compliance_score=payload.policy_compliance_score,
        )
    )
    case_id = payload.case_id or payload.proposal_id or f"gateway-{payload.agent_id}"
    control_plane_store.append_audit_event(
        tenant_id=payload.tenant_id,
        case_id=case_id,
        event_type="gateway.tool_request",
        subject_id=payload.tool_name,
        actor_id=principal_id,
        payload={
            "agent_id": payload.agent_id,
            "tool_name": payload.tool_name,
            "target_system": payload.target_system,
            "gateway_decision": decision_payload.get("gateway_decision"),
            "proposal_id": payload.proposal_id,
        },
    )
    token = None
    if decision_payload.get("gateway_decision") == "allow":
        token = execution_token_service.issue(
            tenant_id=payload.tenant_id,
            agent_id=payload.agent_id,
            tool_name=payload.tool_name,
            gateway_decision="allow",
            proposal_id=payload.proposal_id,
        )
    return {
        **decision_payload,
        "execution_token": token,
        "principal_id": principal_id,
        "case_id": case_id,
    }


@app.get("/api/governance/metrics")
def governance_metrics(tenant_id: str = "bank-demo") -> dict[str, object]:
    return gateway_metrics_service.snapshot(tenant_id)


@app.get("/api/platform/integrations")
def platform_integrations() -> dict[str, object]:
    return platform_control_plane_service.integration_posture()


@app.post("/api/policy/simulate")
def simulate_policy(payload: PolicySimulationRequest, auth: AuthRequired) -> dict[str, object]:
    return policy_simulator_service.simulate(
        PolicySimulationInput(
            tenant_id=payload.tenant_id,
            action_type=payload.action_type,
            target_system=payload.target_system,
            amount_usd=payload.amount_usd,
            data_classification=payload.data_classification,
            reversible=payload.reversible,
            customer_impact=payload.customer_impact,
            model_confidence=payload.model_confidence,
            grounding_score=payload.grounding_score,
            safety_score=payload.safety_score,
            policy_compliance_score=payload.policy_compliance_score,
        )
    )


@app.post("/api/policy/studio/dry-run")
def policy_studio_dry_run(payload: GatewayToolRequestPayload, auth: AuthRequired) -> dict[str, object]:
    return platform_control_plane_service.policy_studio_dry_run(
        GatewayToolRequest(
            tenant_id=payload.tenant_id,
            agent_id=payload.agent_id,
            principal_id=auth.principal_id,
            tool_name=payload.tool_name,
            action_type=payload.action_type,
            target_system=payload.target_system,
            amount_usd=payload.amount_usd,
            data_classification=payload.data_classification,
            reversible=payload.reversible,
            customer_impact=payload.customer_impact,
            grounding_score=payload.grounding_score,
            safety_score=payload.safety_score,
            policy_compliance_score=payload.policy_compliance_score,
        )
    )


@app.post("/api/policy/replay")
def historical_policy_replay(payload: GatewayToolRequestPayload, auth: AuthRequired) -> dict[str, object]:
    return platform_control_plane_service.historical_policy_replay(
        GatewayToolRequest(
            tenant_id=payload.tenant_id,
            agent_id=payload.agent_id,
            principal_id=auth.principal_id,
            tool_name=payload.tool_name,
            action_type=payload.action_type,
            target_system=payload.target_system,
            amount_usd=payload.amount_usd,
            data_classification=payload.data_classification,
            reversible=payload.reversible,
            customer_impact=payload.customer_impact,
            grounding_score=payload.grounding_score,
            safety_score=payload.safety_score,
            policy_compliance_score=payload.policy_compliance_score,
        )
    )


@app.post("/api/release-gates/promote")
def release_gate_promotion(payload: ReleasePromotionRequest, auth: AuthRequired) -> dict[str, object]:
    return platform_control_plane_service.release_promotion_gate(
        agent_id=payload.agent_id,
        version=payload.release_version,
        requested_by=auth.principal_id if payload.requested_by == "ai-platform-lead" else payload.requested_by,
    )


@app.get("/api/product/regulatory-customer-ops-demo")
def regulatory_customer_ops_demo() -> dict[str, object]:
    return platform_control_plane_service.regulated_customer_ops_demo()


@app.get("/api/audit-packets/{tenant_id}/{case_id}.json")
def export_audit_packet_json(tenant_id: str, case_id: str) -> Response:
    packet = audit_packet_exporter.build_packet(
        control_plane_store.case_audit_snapshot(tenant_id, case_id)
    )
    return Response(
        content=audit_packet_exporter.json_bytes(packet),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{case_id}-audit-packet.json"'},
    )


@app.get("/api/audit-packets/{tenant_id}/{case_id}/signed.json")
def export_signed_audit_packet_json(tenant_id: str, case_id: str) -> Response:
    packet = audit_packet_exporter.build_signed_packet(
        control_plane_store.case_audit_snapshot(tenant_id, case_id)
    )
    return Response(
        content=audit_packet_exporter.json_bytes(packet),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{case_id}-audit-packet.signed.json"'
        },
    )


@app.get("/api/audit-packets/{tenant_id}/{case_id}.pdf")
def export_audit_packet_pdf(tenant_id: str, case_id: str, signed: bool = False) -> Response:
    snapshot = control_plane_store.case_audit_snapshot(tenant_id, case_id)
    packet = (
        audit_packet_exporter.build_signed_packet(snapshot)
        if signed
        else audit_packet_exporter.build_packet(snapshot)
    )
    suffix = "-signed" if signed else ""
    return Response(
        content=audit_packet_exporter.pdf_bytes(packet),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{case_id}-audit-packet{suffix}.pdf"'
        },
    )


@app.post("/api/audit-packets/verify")
def verify_audit_packet(payload: AuditPacketVerifyRequest, auth: AuthRequired) -> dict[str, object]:
    result = audit_packet_exporter.verify_signed_packet(payload.signed_packet)
    return {
        "product_module": "Assure",
        "verification": result,
        "verified_by": auth.principal_id,
    }


@app.get("/api/audit-signing/posture")
def audit_signing_posture() -> dict[str, object]:
    return audit_signer.posture()


@app.get("/api/audit-vault/posture")
def audit_vault_posture() -> dict[str, object]:
    return platform_control_plane_service.audit_vault_posture()


@app.get("/api/auth/posture")
def authentication_posture() -> dict[str, object]:
    return auth_posture()


@app.get("/api/identity/posture")
def identity_posture() -> dict[str, object]:
    return identity_service.posture()


@app.get("/api/identity/graph")
def identity_graph() -> dict[str, object]:
    return identity_service.graph(agent_registry_service.list_agents())


@app.get("/api/identity/permission-matrix")
def permission_matrix() -> dict[str, object]:
    return identity_service.permission_matrix(agent_registry_service.list_agents())


@app.get("/api/kill-switches")
def kill_switches() -> dict[str, object]:
    return kill_switch_service.posture()


@app.get("/api/incidents/timeline")
def incident_timeline() -> dict[str, object]:
    return kill_switch_service.incident_timeline()


@app.get("/api/dashboard/summary")
def dashboard_summary(tenant_id: str = "bank-demo") -> dict[str, object]:
    return dashboard_service.summary(tenant_id)


@app.get("/api/orchestrators")
def orchestrators_registry() -> dict[str, object]:
    return {
        "orchestrators": [
            ai_content_orchestrator.posture(),
            stock_research_orchestrator.posture(),
            website_build_orchestrator.posture(),
        ]
    }


@app.post("/api/orchestrators/ai-content/run")
def run_ai_content_pipeline(auth: AuthRequired, tenant_id: str = "bank-demo") -> dict[str, object]:
    return ai_content_orchestrator.run(tenant_id)


@app.get("/api/orchestrators/ai-content/runs")
def list_ai_content_runs(limit: int = 10) -> dict[str, object]:
    return ai_content_orchestrator.list_runs(limit)


@app.post("/api/orchestrators/stock-research/run")
def run_stock_research(auth: AuthRequired, tenant_id: str = "bank-demo") -> dict[str, object]:
    return stock_research_orchestrator.run(tenant_id)


@app.get("/api/orchestrators/stock-research/runs")
def list_stock_research_runs(limit: int = 10) -> dict[str, object]:
    return stock_research_orchestrator.list_runs(limit)


@app.post("/api/orchestrators/website-build/run")
def run_website_build(
    auth: AuthRequired,
    tenant_id: str = "bank-demo",
    requirement: str | None = None,
) -> dict[str, object]:
    return website_build_orchestrator.run(tenant_id, requirement=requirement)


@app.get("/api/orchestrators/website-build/runs")
def list_website_build_runs(limit: int = 10) -> dict[str, object]:
    return website_build_orchestrator.list_runs(limit)


@app.get("/api/agent-cloud/posture")
def agent_cloud_posture(tenant_id: str = "bank-demo") -> dict[str, object]:
    return agent_cloud_service.posture(tenant_id)


@app.get("/api/agent-cloud/monitor")
def agent_cloud_monitor(tenant_id: str = "bank-demo", limit: int = 20) -> dict[str, object]:
    return agent_cloud_service.monitor_feed(tenant_id, limit=limit)


@app.get("/api/agent-cloud/govern")
def agent_cloud_govern() -> dict[str, object]:
    return agent_cloud_service.govern_posture()


@app.get("/api/agent-cloud/undoable")
def agent_cloud_undoable(tenant_id: str = "bank-demo") -> dict[str, object]:
    return agent_cloud_service.undoable_actions(tenant_id)


@app.post("/api/agent-cloud/undo")
def agent_cloud_undo(payload: AgentUndoRequest, auth: ReviewerAuthRequired) -> dict[str, object]:
    actor_id = auth.principal_id if payload.actor_id == "security-admin" else payload.actor_id
    return agent_cloud_service.undo_execution(
        UndoRequest(
            tenant_id=payload.tenant_id,
            execution_id=payload.execution_id,
            actor_id=actor_id,
            reason=payload.reason,
        )
    )


@app.post("/api/kill-switches")
def activate_kill_switch(payload: KillSwitchRequest, auth: AuthRequired) -> dict[str, object]:
    rule = kill_switch_service.activate(
        scope_type=payload.scope_type,
        scope_value=payload.scope_value,
        reason=payload.reason,
        created_by=auth.principal_id if payload.created_by == "security-admin" else payload.created_by,
    )
    return {
        "status": "activated",
        "rule": kill_switch_service._payload(rule),
        "posture": kill_switch_service.posture(),
    }


@app.post("/api/evaluations/golden/run")
def run_golden_evals(auth: AuthRequired) -> dict[str, object]:
    return golden_eval_service.run()


@app.post("/api/evaluations/red-team/run")
def run_red_team_evals(auth: AuthRequired) -> dict[str, object]:
    return red_team_eval_service.run()


@app.get("/api/connectors/catalog")
def connector_catalog() -> dict[str, object]:
    catalog = execution_broker.connector_registry.catalog()
    http_registered = http_connector_manager.list_http_connectors()
    return {
        "product_module": "Integrate",
        "strategy": "Universal connector registry — govern and execute against any enterprise system.",
        "connectors": catalog,
        "total": len(catalog),
        "http_connectors_registered": len(http_registered),
    }


@app.get("/api/connectors/http")
def list_http_connectors() -> dict[str, object]:
    connectors = http_connector_manager.list_http_connectors()
    return {
        "product_module": "Integrate",
        "connectors": connectors,
        "total": len(connectors),
        "persistence": str(http_connector_manager.store.path),
        "guidance": (
            "Register customer HTTP endpoints for demo and pilot. "
            "Use demo_mode=true for Bay Area demos without a live backend; "
            "set auth_secret_env in production instead of auth_value."
        ),
    }


@app.post("/api/connectors/http")
def register_http_connector(payload: HttpConnectorRegisterRequest, auth: AuthRequired) -> dict[str, object]:
    try:
        registration = http_connector_manager.register(
            display_name=payload.display_name,
            base_url=payload.base_url,
            target_system=payload.target_system,
            tool_names=tuple(payload.tool_names),
            connector_id=payload.connector_id,
            http_method=payload.http_method,
            execute_path=payload.execute_path,
            health_path=payload.health_path,
            auth_mode=payload.auth_mode,
            auth_header_name=payload.auth_header_name,
            auth_secret_env=payload.auth_secret_env,
            auth_value=payload.auth_value,
            demo_mode=payload.demo_mode,
            created_by=auth.principal_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    catalog = execution_broker.connector_registry.catalog()
    return {
        "status": "registered",
        "connector": registration.to_public_dict(),
        "catalog_total": len(catalog),
        "auth_value_persisted": False,
    }


@app.post("/api/connectors/http/test")
def test_http_connector(payload: HttpConnectorTestRequest, auth: AuthRequired) -> dict[str, object]:
    try:
        result = http_connector_manager.test_connection(
            base_url=payload.base_url,
            health_path=payload.health_path,
            http_method=payload.http_method,
            auth_mode=payload.auth_mode,
            auth_header_name=payload.auth_header_name,
            auth_value=payload.auth_value,
            auth_secret_env=payload.auth_secret_env,
            connector_id=payload.connector_id,
            demo_mode=payload.demo_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "product_module": "Integrate",
        "tested_by": auth.principal_id,
        "success": result.success,
        "status_code": result.status_code,
        "latency_ms": result.latency_ms,
        "message": result.message,
        "url": result.url,
    }


@app.delete("/api/connectors/http/{connector_id}")
def delete_http_connector(connector_id: str, auth: AuthRequired) -> dict[str, object]:
    removed = http_connector_manager.delete(connector_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Connector not found: {connector_id}")
    return {
        "status": "deleted",
        "connector_id": connector_id,
        "deleted_by": auth.principal_id,
        "catalog_total": len(execution_broker.connector_registry.catalog()),
    }


@app.get("/api/mcp/posture")
def mcp_posture() -> dict[str, object]:
    return mcp_governance_proxy.posture()


@app.post("/api/mcp/tool-call")
def mcp_tool_call(payload: McpToolCallPayload, auth: AuthRequired) -> dict[str, object]:
    return mcp_governance_proxy.invoke(
        McpToolCallRequest(
            tenant_id=payload.tenant_id,
            agent_id=payload.agent_id,
            principal_id=payload.principal_id,
            mcp_server=payload.mcp_server,
            tool_name=payload.tool_name,
            arguments=payload.arguments,
            action_type=payload.action_type,
            target_system=payload.target_system,
            amount_usd=payload.amount_usd,
            data_classification=payload.data_classification.value,
            reversible=payload.reversible,
            customer_impact=payload.customer_impact,
        ),
        execution_token_service,
    )


@app.get("/api/finops/dashboard")
def finops_dashboard() -> dict[str, object]:
    return finops_service.dashboard()


@app.post("/api/hitl/slack/approval-task")
def create_slack_approval_task(payload: SlackApprovalRequest, auth: AuthRequired) -> dict[str, object]:
    return slack_approval_service.create_approval_task(
        tenant_id=payload.tenant_id,
        case_id=payload.case_id,
        proposal_id=payload.proposal_id,
        summary=payload.summary,
        risk_level=payload.risk_level,
        approval_role=payload.approval_role,
    )


@app.post("/api/hitl/slack/interaction")
def slack_interaction(
    payload: SlackInteractionRequest,
    auth: ReviewerAuthRequired,
) -> dict[str, object]:
    return slack_approval_service.handle_interaction(payload.text, auth.principal_id)


@app.get("/api/hitl/slack/posture")
def slack_posture() -> dict[str, object]:
    return slack_approval_service.posture()


@app.get("/api/control-plane/metrics")
def metrics() -> dict[str, object]:
    return {
        "cases": control_plane_store.count("cases"),
        "agent_traces": control_plane_store.count("agent_traces"),
        "action_proposals": control_plane_store.count("action_proposals"),
        "governance_decisions": control_plane_store.count("governance_decisions"),
        "approval_tasks": control_plane_store.count("approval_tasks"),
        "action_executions": control_plane_store.count("action_executions"),
        "audit_events": control_plane_store.count("audit_events"),
        "memory_documents": memory_store.count(),
    }


@app.get("/api/observability/status")
def observability_status() -> dict[str, object]:
    statuses = observability_service.statuses()
    return {
        "source_of_truth": "AegisAI control-plane audit, policy, HITL, and workflow database",
        "exporters": [_status_payload(status) for status in statuses],
        "recommendation": "Use Langfuse or LangSmith as trace/evaluation adapters while keeping regulated HITL and audit state in AegisAI.",
    }


def _status_payload(status: ExporterStatus) -> dict[str, object]:
    return {
        "name": status.name,
        "state": status.state.value,
        "detail": status.detail,
        "environment_keys": list(status.environment_keys),
    }


def _execution_payload(result: ExecutionResult) -> dict[str, object]:
    return {
        "execution_id": result.execution_id,
        "tenant_id": result.tenant_id,
        "case_id": result.case_id,
        "proposal_id": result.proposal_id,
        "status": result.status.value,
        "target_system": result.target_system,
        "action_type": result.action_type,
        "connector": result.connector,
        "idempotency_key": result.idempotency_key,
        "external_reference": result.external_reference,
        "rollback_reference": result.rollback_reference,
        "message": result.message,
    }


def _authorization_payload(result: object) -> dict[str, object]:
    return {
        "allowed": result.allowed,
        "reason": result.reason,
        "required": result.required,
    }


def _tool_name(action_type: str, target_system: str) -> str:
    if target_system == "payments" and action_type == "issue_refund":
        return "payments.issue_refund"
    if target_system == "customer_data_platform":
        return "privacy.modify_or_delete_data"
    if target_system == "infrastructure":
        return "infra.change_production_configuration"
    return f"{target_system}.{action_type}"
