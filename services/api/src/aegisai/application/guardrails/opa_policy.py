from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from aegisai.domain import Decision, EvaluationGateResult, RiskAssessment, RiskLevel


class OpaPolicyEngine:
    """Evaluates Rego policies via OPA CLI when available; used for simulator/runtime parity."""

    version = "opa-aegisai-2026.05"

    def __init__(self, policy_path: Path | None = None) -> None:
        default = Path(__file__).resolve().parents[6] / "platform" / "policy" / "aegisai.rego"
        self.policy_path = policy_path or Path(os.getenv("AEGISAI_OPA_POLICY_PATH", str(default)))

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
        if not self.policy_path.exists() or not self.available():
            return self._fallback(risk, evaluation)

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
            return self._fallback(risk, evaluation)

    @staticmethod
    def _map_decision(raw: str) -> Decision:
        mapping = {
            "auto_approve": Decision.AUTO_APPROVE,
            "human_approval": Decision.HUMAN_APPROVAL,
            "escalate": Decision.ESCALATE,
            "block": Decision.BLOCK,
        }
        return mapping.get(raw, Decision.HUMAN_APPROVAL)

    @staticmethod
    def _fallback(risk: RiskAssessment, evaluation: EvaluationGateResult) -> tuple[Decision, str | None]:
        from .policy import PolicyEngine

        return PolicyEngine().decide(risk, evaluation)
