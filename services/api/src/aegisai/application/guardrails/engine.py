from aegisai.domain import ActionProposal, Decision, GovernanceDecision
from .evaluation import EvaluationGate
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

        # Under PRODUCTION_STRICT, irreversible/customer-impact/high-risk actions require
        # a live OPA plane — never silent builtin allow when OPA is down.
        if OpaPolicyEngine.requires_hard_block_when_unavailable(
            reversible=proposal.reversible,
            customer_impact=proposal.customer_impact,
            risk=risk,
        ):
            opa = (
                self.policy_engine
                if isinstance(self.policy_engine, OpaPolicyEngine)
                else OpaPolicyEngine()
            )
            if not opa.policy_path.exists() or not OpaPolicyEngine.available():
                return GovernanceDecision(
                    proposal_id=proposal.proposal_id,
                    decision=Decision.BLOCK,
                    risk=risk,
                    evaluation=evaluation,
                    approval_role=None,
                    policy_version=OpaPolicyEngine.POLICY_UNAVAILABLE_VERSION,
                )

        if isinstance(self.policy_engine, OpaPolicyEngine):
            decision, approval_role = self.policy_engine.decide(
                risk,
                evaluation,
                amount_usd=proposal.amount_usd,
                data_classification=proposal.data_classification.value,
                reversible=proposal.reversible,
                customer_impact=proposal.customer_impact,
            )
            policy_version = getattr(
                self.policy_engine,
                "last_policy_version",
                self.policy_engine.version,
            )
        else:
            decision, approval_role = self.policy_engine.decide(risk, evaluation)
            policy_version = self.policy_engine.version

        return GovernanceDecision(
            proposal_id=proposal.proposal_id,
            decision=decision,
            risk=risk,
            evaluation=evaluation,
            approval_role=approval_role,
            policy_version=policy_version,
        )
