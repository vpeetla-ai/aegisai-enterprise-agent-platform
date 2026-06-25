from __future__ import annotations

from uuid import uuid4

from aegisai.application.knowledge import RAGResult
from aegisai.application.orchestration import OrchestrationResult

from .exporters import LangSmithExporter, LangfuseExporter, TraceExporter
from .models import ExporterStatus, TraceEvent


class ObservabilityService:
    """Vendor-neutral observability boundary for agent traces and eval signals."""

    def __init__(self, exporters: tuple[TraceExporter, ...]) -> None:
        self.exporters = exporters

    def statuses(self) -> list[ExporterStatus]:
        return [exporter.status() for exporter in self.exporters]

    def export_agent_run(
        self,
        result: OrchestrationResult,
        rag_result: RAGResult,
    ) -> list[ExporterStatus]:
        event = self._build_trace_event(result, rag_result)
        return [exporter.export(event) for exporter in self.exporters]

    def export_orchestrator_run(
        self,
        *,
        orchestrator_id: str,
        run_id: str,
        tenant_id: str,
        agent_traces: tuple[str, ...],
        metadata: dict[str, object] | None = None,
    ) -> list[ExporterStatus]:
        event = TraceEvent(
            trace_id=f"trace-{run_id}",
            tenant_id=tenant_id,
            request_id=run_id,
            workflow_type=orchestrator_id,
            decision="orchestrator_completed",
            risk_score=0,
            risk_level="low",
            agents_run=agent_traces,
            retrieved_sources=(),
            evaluation_scores={},
            metadata={"orchestrator_id": orchestrator_id, **(metadata or {})},
        )
        return [exporter.export(event) for exporter in self.exporters]

    @staticmethod
    def _build_trace_event(result: OrchestrationResult, rag_result: RAGResult) -> TraceEvent:
        decision = result.context.governance_decisions[0] if result.context.governance_decisions else None
        proposal = result.context.proposed_actions[0] if result.context.proposed_actions else None
        evaluation_scores = dict(proposal.evaluation_scores) if proposal else {}
        return TraceEvent(
            trace_id=f"trace-{result.request_id}-{uuid4()}",
            tenant_id=result.context.request.tenant_id,
            request_id=result.request_id,
            workflow_type=result.workflow_type.value,
            decision=decision.decision.value if decision else "no_action_proposed",
            risk_score=decision.risk.score if decision else 0,
            risk_level=decision.risk.level.value if decision else "none",
            agents_run=tuple(agent.value for agent in result.agents_run),
            retrieved_sources=tuple(document.source_uri for document in rag_result.retrieved_documents),
            evaluation_scores=evaluation_scores,
            metadata={
                "user_id": result.context.request.user_id,
                "data_classification": result.context.request.data_classification.value,
                "customer_impact": result.context.request.customer_impact,
                "agent_trace_count": len(result.context.agent_traces),
                "proposal_id": proposal.proposal_id if proposal else None,
            },
        )


def build_default_observability_service() -> ObservabilityService:
    return ObservabilityService(exporters=(LangfuseExporter(), LangSmithExporter()))
