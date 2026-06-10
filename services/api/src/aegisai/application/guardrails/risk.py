from aegisai.domain import ActionProposal, DataClassification, RiskAssessment, RiskLevel


class RiskScorer:
    """Contextual risk scoring for proposed agent actions."""

    def score(self, proposal: ActionProposal) -> RiskAssessment:
        score = 0
        reasons: list[str] = []

        if proposal.amount_usd >= 10_000:
            score += 35
            reasons.append("large_financial_amount")
        elif proposal.amount_usd >= 1_000:
            score += 20
            reasons.append("moderate_financial_amount")
        elif proposal.amount_usd > 0:
            score += 5
            reasons.append("financial_action")

        if proposal.data_classification == DataClassification.RESTRICTED:
            score += 35
            reasons.append("restricted_data")
        elif proposal.data_classification == DataClassification.CONFIDENTIAL:
            score += 20
            reasons.append("confidential_data")

        if not proposal.reversible:
            score += 25
            reasons.append("irreversible_action")

        if proposal.data_classification == DataClassification.RESTRICTED and not proposal.reversible:
            score += 15
            reasons.append("restricted_irreversible_action")

        if proposal.customer_impact:
            score += 15
            reasons.append("customer_impacting")

        if proposal.model_confidence < 0.75:
            score += 15
            reasons.append("low_model_confidence")

        level = self._level(score)
        return RiskAssessment(score=score, level=level, reason_codes=tuple(reasons))

    @staticmethod
    def _level(score: int) -> RiskLevel:
        if score >= 80:
            return RiskLevel.CRITICAL
        if score >= 55:
            return RiskLevel.HIGH
        if score >= 25:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
