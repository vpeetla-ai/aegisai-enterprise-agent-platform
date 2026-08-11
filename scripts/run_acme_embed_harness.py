#!/usr/bin/env python3
"""Run Acme embed harness and optionally score against GER suite.

Usage:
  python scripts/run_acme_embed_harness.py
  GOLDEN_EVAL_REGISTRY_PATH=../golden-eval-registry python scripts/run_acme_embed_harness.py --score
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api" / "src"))

from aegisai.product.acme_embed_harness import collect_acme_embed_invariants  # noqa: E402


def _registry_path() -> Path:
    env = os.getenv("GOLDEN_EVAL_REGISTRY_PATH")
    if env:
        return Path(env).resolve()
    sibling = ROOT.parent / "golden-eval-registry"
    return sibling


def main() -> int:
    parser = argparse.ArgumentParser(description="Acme Support Agent Embed panel harness")
    parser.add_argument("--score", action="store_true", help="Score against GER acme.embed_invariant_v1")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    actual = collect_acme_embed_invariants()
    if args.json and not args.score:
        print(json.dumps(actual, indent=2, sort_keys=True))
        return 0

    if not args.json:
        print("Acme embed harness — panel break invariants")
        for key in sorted(actual):
            print(f"  {key}: {actual[key]}")

    if not args.score:
        return 0

    try:
        from golden_eval_registry.runner import score_suite
        from golden_eval_registry.schema import parse_manifest
        from golden_eval_registry.validate import load_jsonl
    except ImportError:
        print("golden-eval-registry not installed", file=sys.stderr)
        return 2

    suite_dir = _registry_path() / "suites" / "acme_embed_invariant_v1"
    if not suite_dir.exists():
        print(f"suite missing: {suite_dir}", file=sys.stderr)
        return 2

    manifest = parse_manifest(suite_dir / "manifest.json")
    cases = load_jsonl(manifest.cases_path)
    result = score_suite(manifest, cases, {str(c["id"]): actual for c in cases})
    summary = {
        "suite_id": manifest.suite_id,
        "passed": result.passed,
        "case_count": len(result.results),
        "failures": [{"case_id": f.case_id, "detail": f.detail} for f in result.failures],
    }
    print(json.dumps(summary, indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
