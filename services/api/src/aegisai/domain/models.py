from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(StrEnum):
    AUTO_APPROVE = "auto_approve"
    HUMAN_APPROVAL = "human_approval"
    ESCALATE = "escalate"
    BLOCK = "block"


class ExecutionStatus(StrEnum):
    EXECUTED = "executed"
    ROLLED_BACK = "rolled_back"
    REQUIRES_APPROVAL = "requires_approval"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True)
class ActionProposal:
    proposal_id: str
    tenant_id: str
    agent_id: str
    action_type: str
    target_system: str
    amount_usd: float = 0
    data_classification: DataClassification = DataClassification.INTERNAL
    reversible: bool = True
    customer_impact: bool = False
    model_confidence: float = 0.9
    evaluation_scores: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskAssessment:
    score: int
    level: RiskLevel
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationGateResult:
    passed: bool
    failed_checks: tuple[str, ...]
    minimum_score: float


@dataclass(frozen=True)
class GovernanceDecision:
    proposal_id: str
    decision: Decision
    risk: RiskAssessment
    evaluation: EvaluationGateResult
    approval_role: str | None
    policy_version: str


@dataclass(frozen=True)
class ExecutionCommand:
    tenant_id: str
    case_id: str
    proposal_id: str
    actor_id: str
    idempotency_key: str
    dry_run: bool = False


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    tenant_id: str
    case_id: str
    proposal_id: str
    status: ExecutionStatus
    target_system: str
    action_type: str
    connector: str
    idempotency_key: str
    external_reference: str | None
    rollback_reference: str | None
    message: str


@dataclass(frozen=True)
class AgentTrace:
    trace_id: str
    case_id: str
    tenant_id: str
    agent_name: str
    step_name: str
    status: str
    input_ref: str
    output_ref: str
    policy_findings: tuple[str, ...]
    started_at: str
    completed_at: str


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    tenant_id: str
    case_id: str
    event_type: str
    subject_id: str
    actor_id: str
    payload_json: str
    previous_hash: str
    event_hash: str
    occurred_at: str


@dataclass(frozen=True)
class RegisteredAgent:
    agent_id: str
    name: str
    owner: str
    business_domain: str
    risk_tier: str
    autonomy_level: int
    status: str
    model_provider: str
    allowed_tools: tuple[str, ...]
    data_classes: tuple[str, ...]
    last_run_at: str
    monthly_cost_usd: float
    open_incidents: int
    value_metric: str
