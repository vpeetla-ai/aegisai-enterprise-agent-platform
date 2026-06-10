from .evaluation import EvaluationGate
from aegisai.domain import ActionProposal, GovernanceDecision
from .opa_policy import OpaPolicyEngine
from .policy import PolicyEngine, build_policy_engine
from .risk import RiskScorer


class DecisionEngine:
    def __init__(
        self,
        risk_scorer: RiskScorer | None = None,
        evaluation_gate: EvaluationGate | None = None,
        policy_engine: PolicyEngine | None = None,
    ) -> None:
        self.risk_scorer = risk_scorer or RiskScorer()
        self.evaluation_gate = evaluation_gate or EvaluationGate()
        self.policy_engine = policy_engine or build_policy_engine()

    def decide(self, proposal: ActionProposal) -> GovernanceDecision:
        evaluation = self.evaluation_gate.evaluate(proposal)
        risk = self.risk_scorer.score(proposal)
        if isinstance(self.policy_engine, OpaPolicyEngine):
            decision, approval_role = self.policy_engine.decide(
                risk,
                evaluation,
                amount_usd=proposal.amount_usd,
                data_classification=proposal.data_classification.value,
                reversible=proposal.reversible,
                customer_impact=proposal.customer_impact,
            )
        else:
            decision, approval_role = self.policy_engine.decide(risk, evaluation)

        return GovernanceDecision(
            proposal_id=proposal.proposal_id,
            decision=decision,
            risk=risk,
            evaluation=evaluation,
            approval_role=approval_role,
            policy_version=self.policy_engine.version,
        )
