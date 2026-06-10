from __future__ import annotations

from typing import Any, TypedDict

from aegisai.application.knowledge import RAGPipeline, RAGResult, SQLiteVectorMemoryStore
from aegisai.application.orchestration.multi_agent import (
    BusinessRequest,
    MultiAgentOrchestrator,
    OrchestrationResult,
)


class AgentGraphState(TypedDict, total=False):
    request: BusinessRequest
    rag_result: RAGResult
    orchestration_result: OrchestrationResult
    control_plane_status: str


class EnterpriseAgentGraph:
    """LangGraph-compatible orchestrator with deterministic fallback."""

    def __init__(
        self,
        orchestrator: MultiAgentOrchestrator | None = None,
        memory_store: SQLiteVectorMemoryStore | None = None,
    ) -> None:
        self.orchestrator = orchestrator or MultiAgentOrchestrator()
        self.memory_store = memory_store or SQLiteVectorMemoryStore()
        if self.memory_store.count() == 0:
            self.memory_store.seed_enterprise_memory()
        self.rag = RAGPipeline(self.memory_store)
        self._compiled_graph = self._build_langgraph_if_available()

    def invoke(self, request: BusinessRequest) -> AgentGraphState:
        if self._compiled_graph is not None:
            return self._compiled_graph.invoke({"request": request})
        return self._fallback_invoke({"request": request})

    def _fallback_invoke(self, state: AgentGraphState) -> AgentGraphState:
        request = state["request"]
        namespace = self._namespace_for_request(request.text)
        rag_result = self.rag.answer(
            tenant_id=request.tenant_id,
            namespace=namespace,
            query=request.text,
        )
        orchestration_result = self.orchestrator.run(request)
        decision = (
            orchestration_result.context.governance_decisions[0].decision.value
            if orchestration_result.context.governance_decisions
            else "no_action_proposed"
        )
        return {
            **state,
            "rag_result": rag_result,
            "orchestration_result": orchestration_result,
            "control_plane_status": decision,
        }

    def _build_langgraph_if_available(self) -> Any | None:
        try:
            from langgraph.graph import END, StateGraph
        except ModuleNotFoundError:
            return None

        graph = StateGraph(AgentGraphState)
        graph.add_node("retrieve_context", self._retrieve_context_node)
        graph.add_node("run_agents", self._run_agents_node)
        graph.add_node("control_plane", self._control_plane_node)
        graph.set_entry_point("retrieve_context")
        graph.add_edge("retrieve_context", "run_agents")
        graph.add_edge("run_agents", "control_plane")
        graph.add_edge("control_plane", END)
        return graph.compile()

    def _retrieve_context_node(self, state: AgentGraphState) -> AgentGraphState:
        request = state["request"]
        namespace = self._namespace_for_request(request.text)
        return {
            **state,
            "rag_result": self.rag.answer(request.tenant_id, namespace, request.text),
        }

    def _run_agents_node(self, state: AgentGraphState) -> AgentGraphState:
        return {
            **state,
            "orchestration_result": self.orchestrator.run(state["request"]),
        }

    @staticmethod
    def _control_plane_node(state: AgentGraphState) -> AgentGraphState:
        orchestration_result = state["orchestration_result"]
        decision = (
            orchestration_result.context.governance_decisions[0].decision.value
            if orchestration_result.context.governance_decisions
            else "no_action_proposed"
        )
        return {**state, "control_plane_status": decision}

    @staticmethod
    def _namespace_for_request(text: str) -> str:
        lowered = text.lower()
        if "refund" in lowered or "credit" in lowered or "cancel" in lowered:
            return "refund_policy"
        if "delete" in lowered or "deletion" in lowered or "data" in lowered:
            return "data_policy"
        if "dispute" in lowered or "chargeback" in lowered:
            return "refund_policy"
        if "message" in lowered or "customer" in lowered:
            return "communication_policy"
        return "refund_policy"
