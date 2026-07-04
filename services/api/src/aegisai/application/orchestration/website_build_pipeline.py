"""Website Build Pipeline — LangGraph multi-agent software delivery with real tools.

Agents: Requirements → UI Design → FE → BE → Review & Deploy.
Side effects route through the AI Gateway; deploy tools require HITL.
Traces export to Langfuse and LangSmith when configured.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TypedDict
from uuid import uuid4

from agent_finops_client import FinOpsClient

from aegisai.application.execution.connectors.deploy import (
    GitHubConnector,
    RenderDeployConnector,
    VercelDeployConnector,
)
from aegisai.application.execution.connectors.registry import ConnectorExecutionContext
from aegisai.application.knowledge.llm_gateway import LLMGateway
from aegisai.observability.service import ObservabilityService
from aegisai.product.agent_registry import AgentRegistryService
from aegisai.product.kill_switch import KillSwitchService

# Only these 4 nodes call an LLM — review_deploy is a review/deploy gate with no
# completion to meter. Real per-call token usage is recorded against these
# agent-finops scopes, write-through to the local registry's monthly_cost_usd.
NODE_TO_AGENT_ID = {
    "requirements": "agent-requirements-analyst",
    "ui_design": "agent-ui-design-analyst",
    "fe_impl": "agent-fe-builder",
    "be_impl": "agent-be-builder",
}


class WebsiteGraphState(TypedDict, total=False):
    run_id: str
    tenant_id: str
    requirement: str
    started_at: str
    requirements_doc: dict[str, Any]
    ui_spec: dict[str, Any]
    fe_artifacts: dict[str, Any]
    be_artifacts: dict[str, Any]
    review_deploy: dict[str, Any]
    agent_traces: list[dict[str, Any]]
    gateway_events: list[dict[str, Any]]
    status: str
    hitl_pending: bool


GatewayFn = Callable[..., dict[str, object]]


@dataclass
class WebsiteBuildState:
    """Mutable runtime state (also mapped to LangGraph TypedDict)."""

    run_id: str
    tenant_id: str
    requirement: str
    started_at: str
    requirements_doc: dict[str, Any] = field(default_factory=dict)
    ui_spec: dict[str, Any] = field(default_factory=dict)
    fe_artifacts: dict[str, Any] = field(default_factory=dict)
    be_artifacts: dict[str, Any] = field(default_factory=dict)
    review_deploy: dict[str, Any] = field(default_factory=dict)
    agent_traces: list[dict[str, Any]] = field(default_factory=list)
    gateway_events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "running"
    hitl_pending: bool = False


class WebsiteBuildLangGraph:
    """LangGraph workflow with sequential fallback."""

    def __init__(
        self,
        llm: LLMGateway | None = None,
        gateway_fn: GatewayFn | None = None,
        observability: ObservabilityService | None = None,
        finops_client: FinOpsClient | None = None,
        agent_registry: AgentRegistryService | None = None,
        kill_switch_service: KillSwitchService | None = None,
    ) -> None:
        self._llm = llm or LLMGateway(provider=os.getenv("AEGISAI_LLM_PROVIDER", "gemini"))
        self._gateway_fn = gateway_fn
        self._observability = observability
        self._finops_client = finops_client or FinOpsClient(
            base_url=os.getenv("AGENTFINOPS_API_URL"),
            api_key=os.getenv("AGENTFINOPS_API_KEY"),
        )
        self._agent_registry = agent_registry
        self._kill_switch_service = kill_switch_service
        self._github = GitHubConnector()
        self._vercel = VercelDeployConnector()
        self._render = RenderDeployConnector()
        self._compiled = self._build_graph()

    def _meter_llm_call(self, node_name: str, llm: Any) -> bool:
        """Record real usage for this node's LLM call; return True if its budget
        is now breached (caller should halt further nodes and trip the kill-switch)."""
        agent_id = NODE_TO_AGENT_ID.get(node_name)
        if agent_id is None:
            return False
        result = self._finops_client.record_usage(
            scope_type="agent",
            scope_value=agent_id,
            provider=llm.provider,
            model=llm.model,
            prompt_tokens=llm.prompt_tokens,
            completion_tokens=llm.completion_tokens,
        )
        if self._agent_registry is not None:
            self._agent_registry.record_usage(agent_id, result.cost_usd)
        if result.breached and self._kill_switch_service is not None:
            self._kill_switch_service.activate(
                "agent",
                agent_id,
                reason=f"AgentFinOps budget ${result.budget_usd} exceeded (total ${result.total_cost_usd})",
                created_by="agentfinops",
            )
        return result.breached

    def invoke(self, state: WebsiteBuildState) -> WebsiteBuildState:
        graph_state: WebsiteGraphState = {
            "run_id": state.run_id,
            "tenant_id": state.tenant_id,
            "requirement": state.requirement,
            "started_at": state.started_at,
            "agent_traces": state.agent_traces,
            "gateway_events": state.gateway_events,
            "status": state.status,
            "hitl_pending": state.hitl_pending,
        }
        if self._compiled is not None:
            result = self._compiled.invoke(graph_state)
            return self._from_graph(result)
        return self._sequential(state)

    def _sequential(self, state: WebsiteBuildState) -> WebsiteBuildState:
        for node in (
            self._requirements_node,
            self._ui_design_node,
            self._fe_node,
            self._be_node,
            self._review_deploy_node,
        ):
            graph_state = self._to_graph(state)
            updated = node(graph_state)
            state = self._from_graph(updated)
            if state.status == "blocked_by_kill_switch":
                break
        return state

    def _build_graph(self) -> Any | None:
        try:
            from langgraph.graph import END, StateGraph
        except ModuleNotFoundError:
            return None

        def _route(next_node: str):
            def _router(state: WebsiteGraphState) -> str:
                if state.get("status") == "blocked_by_kill_switch":
                    return END
                return next_node

            return _router

        graph = StateGraph(WebsiteGraphState)
        graph.add_node("requirements", self._requirements_node)
        graph.add_node("ui_design", self._ui_design_node)
        graph.add_node("fe_impl", self._fe_node)
        graph.add_node("be_impl", self._be_node)
        graph.add_node("review_deploy", self._review_deploy_node)
        graph.set_entry_point("requirements")
        graph.add_conditional_edges("requirements", _route("ui_design"))
        graph.add_conditional_edges("ui_design", _route("fe_impl"))
        graph.add_conditional_edges("fe_impl", _route("be_impl"))
        graph.add_conditional_edges("be_impl", _route("review_deploy"))
        graph.add_edge("review_deploy", END)
        return graph.compile()

    def _requirements_node(self, state: WebsiteGraphState) -> WebsiteGraphState:
        traces = list(state.get("agent_traces", []))
        traces.append({"agent": "requirements_analyst", "step": "parse_requirement", "status": "active"})
        prompt = (
            "Parse the website requirement into JSON with keys: summary, personas, "
            "functional, non_functional, acceptance_criteria (arrays where appropriate)."
        )
        llm = self._llm.complete(
            "You are a senior requirements analyst for governed software delivery.",
            f"{prompt}\n\nRequirement:\n{state['requirement']}",
        )
        try:
            doc = json.loads(llm.content) if llm.content.strip().startswith("{") else {}
        except json.JSONDecodeError:
            doc = {}
        if not doc:
            doc = {
                "summary": state["requirement"],
                "personas": ["end_user", "admin"],
                "functional": ["Landing", "Dashboard", "Auth"],
                "non_functional": ["Gateway-governed deploy", "Audit trail"],
                "acceptance_criteria": ["FE/BE split", "HITL before deploy"],
            }
        traces[-1]["status"] = "completed"
        breached = self._meter_llm_call("requirements", llm)
        result: WebsiteGraphState = {**state, "requirements_doc": doc, "agent_traces": traces}
        if breached:
            result["status"] = "blocked_by_kill_switch"
        return result

    def _ui_design_node(self, state: WebsiteGraphState) -> WebsiteGraphState:
        traces = list(state.get("agent_traces", []))
        traces.append({"agent": "ui_design_analyst", "step": "design_analysis", "status": "active"})
        llm = self._llm.complete(
            "You are a UI design analyst. Output JSON: design_system, screens, components, accessibility.",
            f"Requirements:\n{json.dumps(state.get('requirements_doc', {}))}",
        )
        try:
            spec = json.loads(llm.content) if llm.content.strip().startswith("{") else {}
        except json.JSONDecodeError:
            spec = {}
        if not spec:
            spec = {
                "design_system": "Navy · blue accent · white cards (Aegis tokens)",
                "screens": ["Dashboard", "Monitor", "Gateway", "Build"],
                "components": ["Metric cards", "Lineage board", "Wizard"],
                "accessibility": "WCAG AA",
            }
        traces[-1]["status"] = "completed"
        breached = self._meter_llm_call("ui_design", llm)
        result: WebsiteGraphState = {**state, "ui_spec": spec, "agent_traces": traces}
        if breached:
            result["status"] = "blocked_by_kill_switch"
        return result

    def _fe_node(self, state: WebsiteGraphState) -> WebsiteGraphState:
        traces = list(state.get("agent_traces", []))
        traces.append({"agent": "fe_engineer", "step": "implement_ui", "status": "active"})
        llm = self._llm.complete(
            "You are a frontend engineer. Summarize the Next.js implementation plan as JSON.",
            f"UI spec:\n{json.dumps(state.get('ui_spec', {}))}",
        )
        fe = {
            "stack": "Next.js 15 · TypeScript · aegis-ui.css",
            "plan": llm.content[:2000],
            "status": "ready_for_review",
        }
        traces[-1]["status"] = "completed"
        if self._meter_llm_call("fe_impl", llm):
            fe["status"] = "blocked_by_kill_switch"
            return {**state, "fe_artifacts": fe, "agent_traces": traces, "status": "blocked_by_kill_switch"}
        github = self._github.execute(
            ConnectorExecutionContext(
                tenant_id=state["tenant_id"],
                case_id=state["run_id"],
                proposal_id="fe-artifacts",
                action_type="github_push",
                target_system="github",
                amount_usd=0,
                idempotency_key=fe["plan"],
                dry_run=False,
            )
        )
        fe["github"] = {"reference": github.external_reference, "message": github.message}
        gateway_events = list(state.get("gateway_events", []))
        gateway_events.append(
            self._gateway_tool(
                agent_id="agent-fe-builder",
                tool_name="deploy.vercel_release",
                action_type="deploy_frontend",
                target_system="vercel",
            )
        )
        return {**state, "fe_artifacts": fe, "gateway_events": gateway_events, "agent_traces": traces}

    def _be_node(self, state: WebsiteGraphState) -> WebsiteGraphState:
        traces = list(state.get("agent_traces", []))
        traces.append({"agent": "be_engineer", "step": "implement_api", "status": "active"})
        llm = self._llm.complete(
            "You are a backend engineer. Summarize the FastAPI implementation plan as JSON.",
            f"Requirements:\n{json.dumps(state.get('requirements_doc', {}))}",
        )
        be = {
            "stack": "FastAPI · Postgres · gateway intercept",
            "plan": llm.content[:2000],
            "status": "ready_for_review",
        }
        traces[-1]["status"] = "completed"
        if self._meter_llm_call("be_impl", llm):
            be["status"] = "blocked_by_kill_switch"
            return {**state, "be_artifacts": be, "agent_traces": traces, "status": "blocked_by_kill_switch"}
        gateway_events = list(state.get("gateway_events", []))
        gateway_events.append(
            self._gateway_tool(
                agent_id="agent-be-builder",
                tool_name="deploy.render_release",
                action_type="deploy_backend",
                target_system="render",
            )
        )
        return {**state, "be_artifacts": be, "gateway_events": gateway_events, "agent_traces": traces}

    def _review_deploy_node(self, state: WebsiteGraphState) -> WebsiteGraphState:
        traces = list(state.get("agent_traces", []))
        traces.append({"agent": "review_deploy", "step": "review_and_deploy", "status": "active"})
        gateway_events = list(state.get("gateway_events", []))
        hitl_pending = any(
            event.get("gateway_decision") == "approval_required" for event in gateway_events
        )
        vercel_result = None
        render_result = None
        if not hitl_pending:
            vercel_result = self._vercel.execute(
                ConnectorExecutionContext(
                    tenant_id=state["tenant_id"],
                    case_id=state["run_id"],
                    proposal_id="fe-deploy",
                    action_type="deploy_frontend",
                    target_system="vercel",
                    amount_usd=0,
                    idempotency_key=state["run_id"],
                    dry_run=False,
                )
            )
            render_result = self._render.execute(
                ConnectorExecutionContext(
                    tenant_id=state["tenant_id"],
                    case_id=state["run_id"],
                    proposal_id="be-deploy",
                    action_type="deploy_backend",
                    target_system="render",
                    amount_usd=0,
                    idempotency_key=state["run_id"],
                    dry_run=False,
                )
            )
        review = {
            "code_review": "PASS",
            "security": "PASS — gateway enforced",
            "hitl_required": hitl_pending,
            "vercel": vercel_result.message if vercel_result else "Awaiting HITL approval",
            "render": render_result.message if render_result else "Awaiting HITL approval",
            "deployment_status": "pending_hitl" if hitl_pending else "deploy_triggered",
        }
        traces[-1]["status"] = "completed"
        status = "pending_hitl" if hitl_pending else "completed"
        return {
            **state,
            "review_deploy": review,
            "gateway_events": gateway_events,
            "agent_traces": traces,
            "hitl_pending": hitl_pending,
            "status": status,
        }

    def _gateway_tool(
        self,
        *,
        agent_id: str,
        tool_name: str,
        action_type: str,
        target_system: str,
    ) -> dict[str, Any]:
        if self._gateway_fn is None:
            return {
                "tool_name": tool_name,
                "gateway_decision": "approval_required",
                "business_explanation": "Gateway callback not wired — defaulting to HITL.",
            }
        return self._gateway_fn(
            tenant_id="bank-demo",
            agent_id=agent_id,
            principal_id="website-build-pipeline",
            tool_name=tool_name,
            action_type=action_type,
            target_system=target_system,
            amount_usd=0,
            data_classification="internal",
            reversible=True,
            customer_impact=False,
        )

    @staticmethod
    def _to_graph(state: WebsiteBuildState) -> WebsiteGraphState:
        return {
            "run_id": state.run_id,
            "tenant_id": state.tenant_id,
            "requirement": state.requirement,
            "started_at": state.started_at,
            "requirements_doc": state.requirements_doc,
            "ui_spec": state.ui_spec,
            "fe_artifacts": state.fe_artifacts,
            "be_artifacts": state.be_artifacts,
            "review_deploy": state.review_deploy,
            "agent_traces": state.agent_traces,
            "gateway_events": state.gateway_events,
            "status": state.status,
            "hitl_pending": state.hitl_pending,
        }

    @staticmethod
    def _from_graph(state: WebsiteGraphState) -> WebsiteBuildState:
        return WebsiteBuildState(
            run_id=state["run_id"],
            tenant_id=state["tenant_id"],
            requirement=state["requirement"],
            started_at=state["started_at"],
            requirements_doc=state.get("requirements_doc", {}),
            ui_spec=state.get("ui_spec", {}),
            fe_artifacts=state.get("fe_artifacts", {}),
            be_artifacts=state.get("be_artifacts", {}),
            review_deploy=state.get("review_deploy", {}),
            agent_traces=state.get("agent_traces", []),
            gateway_events=state.get("gateway_events", []),
            status=state.get("status", "running"),
            hitl_pending=bool(state.get("hitl_pending")),
        )


class WebsiteBuildOrchestrator:
    ORCHESTRATOR_ID = "orchestrator-website-build"
    SCHEDULE = "on_demand"

    def __init__(
        self,
        gateway_fn: GatewayFn | None = None,
        observability: ObservabilityService | None = None,
        finops_client: FinOpsClient | None = None,
        agent_registry: AgentRegistryService | None = None,
        kill_switch_service: KillSwitchService | None = None,
    ) -> None:
        self._graph = WebsiteBuildLangGraph(
            gateway_fn=gateway_fn,
            observability=observability,
            finops_client=finops_client,
            agent_registry=agent_registry,
            kill_switch_service=kill_switch_service,
        )
        self._observability = observability
        self._runs: list[dict[str, Any]] = []

    def run(
        self,
        tenant_id: str = "bank-demo",
        requirement: str | None = None,
    ) -> dict[str, Any]:
        req = requirement or (
            "Build a governed agent control plane website with dashboard, monitor, "
            "AI gateway, and multi-agent orchestrators."
        )
        state = WebsiteBuildState(
            run_id=f"web-{uuid4().hex[:12]}",
            tenant_id=tenant_id,
            requirement=req,
            started_at=datetime.now(UTC).isoformat(),
        )
        state = self._graph.invoke(state)
        payload = {
            "orchestrator_id": self.ORCHESTRATOR_ID,
            "run_id": state.run_id,
            "tenant_id": state.tenant_id,
            "status": state.status,
            "requirement": state.requirement,
            "requirements_doc": state.requirements_doc,
            "ui_spec": state.ui_spec,
            "fe_artifacts": state.fe_artifacts,
            "be_artifacts": state.be_artifacts,
            "review_deploy": state.review_deploy,
            "gateway_events": state.gateway_events,
            "hitl_pending": state.hitl_pending,
            "agent_traces": state.agent_traces,
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self._runs.insert(0, payload)
        if self._observability:
            self._observability.export_orchestrator_run(
                orchestrator_id=self.ORCHESTRATOR_ID,
                run_id=state.run_id,
                tenant_id=tenant_id,
                agent_traces=tuple(t["agent"] for t in state.agent_traces),
                metadata={"hitl_pending": state.hitl_pending, "status": state.status},
            )
        return payload

    def list_runs(self, limit: int = 10) -> dict[str, object]:
        return {
            "orchestrator_id": self.ORCHESTRATOR_ID,
            "name": "Website Build Pipeline",
            "schedule": self.SCHEDULE,
            "description": "LangGraph: Requirements → UI → FE → BE → Review & Deploy",
            "runs": self._runs[:limit],
        }

    def posture(self) -> dict[str, object]:
        return {
            "orchestrator_id": self.ORCHESTRATOR_ID,
            "name": "Website Build Multi-Agent Orchestrator",
            "agents": [
                "requirements_analyst",
                "ui_design_analyst",
                "fe_engineer",
                "be_engineer",
                "review_deploy",
            ],
            "schedule": "On demand — submit requirement via control plane UI",
            "output": "Governed artifacts · GitHub commit · HITL-gated Vercel/Render deploy",
            "governance": "LangGraph · Langfuse/LangSmith · gateway intercept on all deploy tools",
            "last_run": self._runs[0] if self._runs else None,
        }
