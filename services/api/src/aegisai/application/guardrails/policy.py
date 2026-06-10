import os

from aegisai.domain import Decision, EvaluationGateResult, RiskAssessment, RiskLevel


def build_policy_engine() -> "PolicyEngine":
    if os.getenv("AEGISAI_POLICY_ENGINE", "builtin").lower() == "opa":
        from .opa_policy import OpaPolicyEngine

        return OpaPolicyEngine()
    return PolicyEngine()


class PolicyEngine:
    """Maps risk and evaluation results to an enterprise routing decision."""

    version = "policy-2026.05"

    def decide(
        self,
        risk: RiskAssessment,
        evaluation: EvaluationGateResult,
    ) -> tuple[Decision, str | None]:
        if not evaluation.passed and risk.level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            return Decision.BLOCK, None

        if risk.level == RiskLevel.CRITICAL:
            return Decision.BLOCK, None

        if risk.level == RiskLevel.HIGH:
            return Decision.ESCALATE, "senior_domain_approver"

        if risk.level == RiskLevel.MEDIUM or not evaluation.passed:
            return Decision.HUMAN_APPROVAL, "workflow_owner"

        return Decision.AUTO_APPROVE, None
