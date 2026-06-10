from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ExporterState(StrEnum):
    ENABLED = "enabled"
    NOT_CONFIGURED = "not_configured"
    SDK_MISSING = "sdk_missing"
    ERROR = "error"


@dataclass(frozen=True)
class ExporterStatus:
    name: str
    state: ExporterState
    detail: str
    environment_keys: tuple[str, ...]


@dataclass(frozen=True)
class TraceEvent:
    trace_id: str
    tenant_id: str
    request_id: str
    workflow_type: str
    decision: str
    risk_score: int
    risk_level: str
    agents_run: tuple[str, ...]
    retrieved_sources: tuple[str, ...]
    evaluation_scores: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)
