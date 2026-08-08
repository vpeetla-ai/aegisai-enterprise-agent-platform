from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from aegisai.domain import Decision, EvaluationGateResult, RiskAssessment, RiskLevel


class OpaPolicyEngine:
    """Evaluates Rego policies via OPA CLI when available; used for simulator/runtime parity."""

    version = "opa-aegisai-2026.05"
    POLICY_UNAVAILABLE_VERSION = "policy_unavailable"

    def __init__(self, policy_path: Path | None = None) -> None:
        default = Path(__file__).resolve().parents[6] / "platform" / "policy" / "aegisai.rego"
        self.policy_path = policy_path or Path(os.getenv("AEGISAI_OPA_POLICY_PATH", str(default)))
        self.last_policy_version = self.version
        self.last_unavailable_reason: str | None = None

    @staticmethod
    def available() -> bool:
        try:
            subprocess.run(
                ["opa", "version"],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

    @staticmethod
    def _production_strict() -> bool:
        return os.getenv("PRODUCTION_STRICT", "false").lower() in {"1", "true", "yes", "on"}

    @classmethod
    def requires_hard_block_when_unavailable(
        cls,
        *,
        reversible: bool,
        customer_impact: bool,
        risk: RiskAssessment,
    ) -> bool:
        """Under Strict, irreversible / customer-impact / elevated risk must not fall open."""
        if not cls._production_strict():
            return False
        if not reversible or customer_impact:
            return True
        return risk.level in {RiskLevel.HIGH, RiskLevel.CRITICAL}

    def decide(
        self,
        risk: RiskAssessment,
        evaluation: EvaluationGateResult,
        *,
        amount_usd: float = 0,
        data_classification: str = "internal",
        reversible: bool = True,
        customer_impact: bool = False,
    ) -> tuple[Decision, str | None]:
        self.last_unavailable_reason = None
        self.last_policy_version = self.version

        if not self.policy_path.exists() or not self.available():
            return self._fallback(
                risk,
                evaluation,
                reversible=reversible,
                customer_impact=customer_impact,
                reason="opa_binary_or_policy_pack_missing",
            )

        input_doc = {
            "risk_level": risk.level.value,
            "risk_score": risk.score,
            "evaluation_passed": evaluation.passed,
            "amount_usd": amount_usd,
            "data_classification": data_classification,
            "reversible": reversible,
            "customer_impact": customer_impact,
        }
        try:
            result = subprocess.run(
                [
                    "opa",
                    "eval",
                    "-i",
                    "/dev/stdin",
                    "-d",
                    str(self.policy_path),
                    "data.aegisai.policy",
                    "--format=json",
                ],
                input=json.dumps(input_doc),
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            value = payload[0]["result"][0]["expressions"][0]["value"]
            decision_raw = value.get("decision", "auto_approve")
            role = value.get("approval_role") or None
            return self._map_decision(decision_raw), role if role else None
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError):
            return self._fallback(
                risk,
                evaluation,
                reversible=reversible,
                customer_impact=customer_impact,
                reason="opa_eval_error",
            )

    @staticmethod
    def _map_decision(raw: str) -> Decision:
        mapping = {
            "auto_approve": Decision.AUTO_APPROVE,
            "human_approval": Decision.HUMAN_APPROVAL,
            "escalate": Decision.ESCALATE,
            "block": Decision.BLOCK,
        }
        return mapping.get(raw, Decision.HUMAN_APPROVAL)

    def _fallback(
        self,
        risk: RiskAssessment,
        evaluation: EvaluationGateResult,
        *,
        reversible: bool,
        customer_impact: bool,
        reason: str,
    ) -> tuple[Decision, str | None]:
        if self.requires_hard_block_when_unavailable(
            reversible=reversible,
            customer_impact=customer_impact,
            risk=risk,
        ):
            self.last_policy_version = self.POLICY_UNAVAILABLE_VERSION
            self.last_unavailable_reason = reason
            return Decision.BLOCK, None

        from .policy import PolicyEngine

        self.last_policy_version = PolicyEngine.version
        return PolicyEngine().decide(risk, evaluation)
