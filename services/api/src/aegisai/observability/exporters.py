from __future__ import annotations

import importlib.util
import os
from abc import ABC, abstractmethod

from .models import ExporterState, ExporterStatus, TraceEvent


class TraceExporter(ABC):
    name: str
    environment_keys: tuple[str, ...]

    @abstractmethod
    def status(self) -> ExporterStatus:
        raise NotImplementedError

    @abstractmethod
    def export(self, event: TraceEvent) -> ExporterStatus:
        raise NotImplementedError


class LangfuseExporter(TraceExporter):
    name = "Langfuse"
    environment_keys = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")

    def status(self) -> ExporterStatus:
        has_keys = bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
        if not has_keys:
            return ExporterStatus(
                name=self.name,
                state=ExporterState.NOT_CONFIGURED,
                detail="Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and optionally LANGFUSE_HOST to export traces.",
                environment_keys=self.environment_keys,
            )
        if importlib.util.find_spec("langfuse") is None:
            return ExporterStatus(
                name=self.name,
                state=ExporterState.SDK_MISSING,
                detail="Langfuse credentials are present, but the langfuse Python SDK is not installed.",
                environment_keys=self.environment_keys,
            )
        return ExporterStatus(
            name=self.name,
            state=ExporterState.ENABLED,
            detail="Langfuse exporter is configured for LLM traces, retrieval spans, costs, prompts, and eval scores.",
            environment_keys=self.environment_keys,
        )

    def export(self, event: TraceEvent) -> ExporterStatus:
        status = self.status()
        if status.state != ExporterState.ENABLED:
            return status

        try:
            from langfuse import get_client

            langfuse = get_client()
            trace = langfuse.trace(
                id=event.trace_id,
                name="aegisai.agent_run",
                user_id=event.metadata.get("user_id"),
                session_id=event.request_id,
                metadata={
                    "tenant_id": event.tenant_id,
                    "workflow_type": event.workflow_type,
                    "decision": event.decision,
                    "risk_score": event.risk_score,
                    "risk_level": event.risk_level,
                    "agents_run": event.agents_run,
                    "retrieved_sources": event.retrieved_sources,
                    **event.metadata,
                },
            )
            trace.score(name="risk_score", value=event.risk_score / 100)
            for score_name, score_value in event.evaluation_scores.items():
                trace.score(name=score_name, value=score_value)
            langfuse.flush()
            return status
        except Exception as exc:  # pragma: no cover - depends on external SDK/network
            return ExporterStatus(
                name=self.name,
                state=ExporterState.ERROR,
                detail=f"Langfuse export failed: {exc}",
                environment_keys=self.environment_keys,
            )


class LangSmithExporter(TraceExporter):
    name = "LangSmith"
    environment_keys = ("LANGSMITH_API_KEY", "LANGSMITH_PROJECT", "LANGSMITH_ENDPOINT")

    def status(self) -> ExporterStatus:
        if not os.getenv("LANGSMITH_API_KEY"):
            return ExporterStatus(
                name=self.name,
                state=ExporterState.NOT_CONFIGURED,
                detail="Set LANGSMITH_API_KEY and optionally LANGSMITH_PROJECT/LANGSMITH_ENDPOINT to export LangGraph traces.",
                environment_keys=self.environment_keys,
            )
        if importlib.util.find_spec("langsmith") is None:
            return ExporterStatus(
                name=self.name,
                state=ExporterState.SDK_MISSING,
                detail="LangSmith credentials are present, but the langsmith Python SDK is not installed.",
                environment_keys=self.environment_keys,
            )
        return ExporterStatus(
            name=self.name,
            state=ExporterState.ENABLED,
            detail="LangSmith exporter is configured for LangGraph trace runs, datasets, evals, and prompt debugging.",
            environment_keys=self.environment_keys,
        )

    def export(self, event: TraceEvent) -> ExporterStatus:
        status = self.status()
        if status.state != ExporterState.ENABLED:
            return status

        try:
            from langsmith import Client

            client = Client()
            project_name = os.getenv("LANGSMITH_PROJECT", "aegisai-agent-governance-control-plane")
            run = client.create_run(
                name="aegisai.agent_run",
                run_type="chain",
                project_name=project_name,
                inputs={"request_id": event.request_id, "tenant_id": event.tenant_id},
                outputs={
                    "decision": event.decision,
                    "risk_score": event.risk_score,
                    "risk_level": event.risk_level,
                    "workflow_type": event.workflow_type,
                },
                extra={
                    "metadata": {
                        "agents_run": event.agents_run,
                        "retrieved_sources": event.retrieved_sources,
                        "evaluation_scores": event.evaluation_scores,
                        **event.metadata,
                    }
                },
            )
            client.update_run(run.id, end_time=None)
            return status
        except Exception as exc:  # pragma: no cover - depends on external SDK/network
            return ExporterStatus(
                name=self.name,
                state=ExporterState.ERROR,
                detail=f"LangSmith export failed: {exc}",
                environment_keys=self.environment_keys,
            )
