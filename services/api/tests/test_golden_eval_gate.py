"""Real merge gate: aegisai.gateway_invariant_v1 from golden-eval-registry."""

from __future__ import annotations

import os
from dataclasses import fields
from pathlib import Path

import pytest

from aegisai.application.guardrails.opa_policy import OpaPolicyEngine
from aegisai.domain.models import RegisteredAgent
from aegisai.infrastructure.persistence.agent_registry_seeds import seed_agents

try:
    from golden_eval_registry.runner import score_suite
    from golden_eval_registry.schema import parse_manifest
    from golden_eval_registry.validate import load_jsonl

    GOLDEN_EVAL_REGISTRY_AVAILABLE = True
except ImportError:
    GOLDEN_EVAL_REGISTRY_AVAILABLE = False


def _default_registry_path() -> Path:
    env = os.getenv("GOLDEN_EVAL_REGISTRY_PATH")
    if env:
        return Path(env).resolve()
    candidates = [
        Path(__file__).resolve().parents[3] / "golden-eval-registry",
        Path(__file__).resolve().parents[2] / "golden-eval-registry",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


REGISTRY_PATH = _default_registry_path()
SUITE_DIR = REGISTRY_PATH / "suites" / "aegisai_gateway_invariant_v1"

pytestmark = pytest.mark.skipif(
    not GOLDEN_EVAL_REGISTRY_AVAILABLE,
    reason="golden-eval-registry not installed",
)


def test_aegisai_gateway_invariant_v1_suite_passes() -> None:
    if not SUITE_DIR.exists():
        if os.getenv("CI") or os.getenv("GOLDEN_EVAL_REGISTRY_PATH"):
            pytest.fail(f"aegisai gateway suite missing at {SUITE_DIR}")
        pytest.skip("aegisai gateway suite missing")
    manifest = parse_manifest(SUITE_DIR / "manifest.json")
    cases = load_jsonl(manifest.cases_path)
    actual = {
        "gateway_decisions": ["allow", "approval_required", "block", "deny", "frozen"],
        "seed_agent_ids": [agent.agent_id for agent in seed_agents()],
        "passport_fields": [f.name for f in fields(RegisteredAgent)],
        "policy_unavailable_version": OpaPolicyEngine.POLICY_UNAVAILABLE_VERSION,
    }
    actual_by_id = {str(case["id"]): actual for case in cases}
    result = score_suite(manifest, cases, actual_by_id)
    failures = "\n".join(f"{failure.case_id}: {failure.detail}" for failure in result.failures)
    assert result.passed, f"golden eval regressions:\n{failures}"
