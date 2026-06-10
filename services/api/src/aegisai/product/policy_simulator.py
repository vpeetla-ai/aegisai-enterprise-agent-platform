from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from aegisai.application.guardrails import DecisionEngine
from aegisai.domain import ActionProposal, DataClassification


@dataclass(frozen=True)
class PolicySimulationInput:
    tenant_id: str
    action_type: str
    target_system: str
    amount_usd: float
    data_classification: DataClassification
    reversible: bool
    customer_impact: bool
    model_confidence: float
    grounding_score: float
    safety_score: float
    policy_compliance_score: float


class PolicySimulatorService:
    """Explains how governance would route a hypothetical agent action."""

    def __init__(self, decision_engine: DecisionEngine | None = None) -> None:
        self.decision_engine = decision_engine or DecisionEngine()

    def simulate(self, payload: PolicySimulationInput) -> dict[str, object]:
        proposal = ActionProposal(
            proposal_id=f"sim-{uuid4()}",
            tenant_id=payload.tenant_id,
            agent_id="policy_simulator",
            action_type=payload.action_type,
            target_system=payload.target_system,
            amount_usd=payload.amount_usd,
            data_classification=payload.data_classification,
            reversible=payload.reversible,
            customer_impact=payload.customer_impact,
            model_confidence=payload.model_confidence,
            evaluation_scores={
                "grounding": payload.grounding_score,
                "safety": payload.safety_score,
                "policy_compliance": payload.policy_compliance_score,
            },
        )
        decision = self.decision_engine.decide(proposal)
        return {
            "simulation_id": proposal.proposal_id,
            "decision": decision.decision.value,
            "risk_score": decision.risk.score,
            "risk_level": decision.risk.level.value,
            "approval_role": decision.approval_role,
            "policy_version": decision.policy_version,
            "evaluation_passed": decision.evaluation.passed,
            "failed_checks": list(decision.evaluation.failed_checks),
            "reason_codes": list(decision.risk.reason_codes),
            "explanation": self._explain(decision.approval_role, decision.decision.value),
        }

    @staticmethod
    def _explain(approval_role: str | None, decision: str) -> str:
        if decision == "auto_approve":
            return "Policy allows autonomous execution because risk is low and evaluation gates passed."
        if decision == "block":
            return "Policy blocks execution because risk or evaluation failure exceeds the allowed threshold."
        if decision == "escalate":
            return f"Policy requires escalation to {approval_role or 'a senior reviewer'} before execution."
        return f"Policy requires approval from {approval_role or 'a workflow owner'} before execution."
