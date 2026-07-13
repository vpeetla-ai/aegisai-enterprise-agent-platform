"""BFF helpers — proxy LLM gateway / semantic cache ops metrics into AegisAI Control Room.

Does not move LLM proxy code into AegisAI; only reads satellite plane metrics (ADR-028).
When the live plane is unreachable, returns honest demo_fallback metrics so the Control Room
is demoable on Vercel without localhost.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_GATEWAY_OPS = "http://127.0.0.1:8100/v1/ops/metrics"
DEFAULT_CACHE_OPS = "http://127.0.0.1:8101/v1/ops/metrics"

DEMO_GATEWAY_METRICS = {
    "service": "aegis-llm-gateway",
    "completions": 128,
    "cache_hits": 41,
    "cache_misses": 87,
    "stub_completions": 128,
    "finops_meters": 120,
    "finops_breaches_blocked": 2,
    "finops_errors": 0,
    "control_plane_mode": "demo",
}

DEMO_CACHE_METRICS = {
    "service": "aegis-semantic-cache",
    "hits": 41,
    "misses": 87,
    "entries": 64,
    "hit_rate": 0.32,
}


def _url(env_key: str, default: str) -> str:
    return (os.getenv(env_key) or default).strip()


def _demo_fallback_enabled() -> bool:
    raw = (os.getenv("LLM_PLANE_DEMO_FALLBACK") or "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def fetch_plane_metrics(url: str, *, timeout: float = 3.0) -> dict[str, Any]:
    """Fetch ops metrics JSON; return unreachable stub on failure (never raise)."""
    if not url:
        return {"reachable": False, "error": "url_not_configured"}
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                return {"reachable": False, "error": "invalid_payload"}
            return {"reachable": True, "source": "live", "url": url, "metrics": data}
    except Exception as exc:  # noqa: BLE001 — Control Room must degrade gracefully
        return {
            "reachable": False,
            "url": url,
            "error": type(exc).__name__,
            "detail": str(exc)[:200],
        }


def _with_demo_fallback(
    *,
    plane: str,
    url: str,
    live: dict[str, Any],
    demo_metrics: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(live)
    payload["plane"] = plane
    if payload.get("reachable"):
        return payload
    if not _demo_fallback_enabled():
        return payload
    return {
        "reachable": True,
        "source": "demo_fallback",
        "plane": plane,
        "url": url,
        "metrics": demo_metrics,
        "note": "Live plane unreachable — illustrative demo metrics. Set public Render ops URLs.",
        "live_error": payload.get("error"),
    }


def gateway_ops_payload() -> dict[str, Any]:
    url = _url("LLM_GATEWAY_OPS_URL", DEFAULT_GATEWAY_OPS)
    return _with_demo_fallback(
        plane="aegis-llm-gateway",
        url=url,
        live=fetch_plane_metrics(url),
        demo_metrics=DEMO_GATEWAY_METRICS,
    )


def cache_ops_payload() -> dict[str, Any]:
    url = _url("SEMANTIC_CACHE_OPS_URL", DEFAULT_CACHE_OPS)
    return _with_demo_fallback(
        plane="aegis-semantic-cache",
        url=url,
        live=fetch_plane_metrics(url),
        demo_metrics=DEMO_CACHE_METRICS,
    )
