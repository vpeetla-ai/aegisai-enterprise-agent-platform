"""Real merge gate: acme.embed_invariant_v1 from golden-eval-registry."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from aegisai.product.acme_embed_harness import collect_acme_embed_invariants

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
        Path.home() / "golden-eval-registry",
        Path("/Users/lakshmipraveenabodempudi/golden-eval-registry"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


REGISTRY_PATH = _default_registry_path()
SUITE_DIR = REGISTRY_PATH / "suites" / "acme_embed_invariant_v1"

pytestmark = pytest.mark.skipif(
    not GOLDEN_EVAL_REGISTRY_AVAILABLE,
    reason="golden-eval-registry not installed",
)


def test_acme_embed_invariant_v1_suite_passes() -> None:
    if not SUITE_DIR.exists():
        if os.getenv("CI") or os.getenv("GOLDEN_EVAL_REGISTRY_PATH"):
            pytest.fail(f"acme embed suite missing at {SUITE_DIR}")
        pytest.skip("acme embed suite missing")
    manifest = parse_manifest(SUITE_DIR / "manifest.json")
    cases = load_jsonl(manifest.cases_path)
    actual = collect_acme_embed_invariants()
    actual_by_id = {str(case["id"]): actual for case in cases}
    result = score_suite(manifest, cases, actual_by_id)
    failures = "\n".join(f"{failure.case_id}: {failure.detail}" for failure in result.failures)
    assert result.passed, f"acme embed harness regressions:\n{failures}\nactual={actual}"
