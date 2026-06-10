from aegisai.domain import ActionProposal, EvaluationGateResult


class EvaluationGate:
    """Small blocking gate for proposal-level quality and safety checks."""

    def __init__(self, minimum_score: float = 0.75) -> None:
        self.minimum_score = minimum_score

    def evaluate(self, proposal: ActionProposal) -> EvaluationGateResult:
        failed: list[str] = []

        if proposal.model_confidence < self.minimum_score:
            failed.append("model_confidence_below_threshold")

        for metric_name in ("grounding", "safety", "policy_compliance"):
            score = proposal.evaluation_scores.get(metric_name, 1.0)
            if score < self.minimum_score:
                failed.append(f"{metric_name}_below_threshold")

        return EvaluationGateResult(
            passed=not failed,
            failed_checks=tuple(failed),
            minimum_score=self.minimum_score,
        )
