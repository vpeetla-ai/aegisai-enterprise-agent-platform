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
DEFAULT_ROUTING_OPS = "http://127.0.0.1:8100/v1/ops/routing-decisions"

DEMO_GATEWAY_METRICS = {
    "service": "aegis-llm-gateway",
    "completions": 128,
    "cache_hits": 41,
    "cache_misses": 87,
    "stub_completions": 128,
    "finops_meters": 120,
    "finops_breaches_blocked": 2,
    "finops_errors": 0,
    "routing_denies": 3,
    "routing_decisions_recorded": 128,
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



DEMO_ROUTING = {
    "selection_sor": "app",
    "plane_role": "enforce_and_record",
    "decisions": [
        {
            "tenant_id": "omniforge",
            "workflow_id": "demo-wf",
            "factors": {"thesis_role": "executor", "agent_role": "analysis", "data_class": "internal"},
            "tier": "high_reasoning",
            "provider": "anthropic",
            "model_id": "claude-sonnet",
            "reason": "app_selected_gateway_allowed",
            "policy_allowed": True,
            "cost_usd": 0.012,
        },
        {
            "tenant_id": "vap",
            "workflow_id": "demo-wf",
            "factors": {"thesis_role": "verifier", "agent_role": "critic", "data_class": "internal"},
            "tier": "high_reasoning",
            "provider": "gemini",
            "model_id": "gemini-2.0-flash",
            "reason": "app_selected_gateway_allowed",
            "policy_allowed": True,
            "cost_usd": 0.004,
        },
    ],
}

# Static agent → tier → model table for Control Room (apps select; keys from env/docs)
AGENT_MODEL_CATALOG = [
    {"consumer": "omniforge", "agent": "planner", "thesis_role": "planner", "tier": "specialized", "free_model": "gemini-2.0-flash", "byok_model": "claude-sonnet"},
    {"consumer": "omniforge", "agent": "web", "thesis_role": "retriever", "tier": "fast", "free_model": "llama-3.3-70b (Groq)", "byok_model": "gpt-4o-mini"},
    {"consumer": "omniforge", "agent": "analysis", "thesis_role": "executor", "tier": "high_reasoning", "free_model": "gemini-2.0-flash", "byok_model": "claude-sonnet"},
    {"consumer": "omniforge", "agent": "synthesizer", "thesis_role": "summarizer", "tier": "high_reasoning", "free_model": "gemini-2.0-flash", "byok_model": "gpt-4o"},
    {"consumer": "vap", "agent": "critic", "thesis_role": "verifier", "tier": "high_reasoning", "free_model": "gemini (≠ generator)", "byok_model": "claude (≠ generator)"},
    {"consumer": "acf", "agent": "research", "thesis_role": "retriever", "tier": "fast", "free_model": "gemini-2.5-flash", "byok_model": "gpt-4o-mini"},
    {"consumer": "acf", "agent": "content", "thesis_role": "executor", "tier": "high_reasoning", "free_model": "gemini-2.5-flash", "byok_model": "claude-sonnet"},
    {"consumer": "domainforge", "agent": "generator", "thesis_role": "executor", "tier": "local_private", "free_model": "ollama/mistral", "byok_model": "vLLM adapter"},
    {"consumer": "aegisai", "agent": "knowledge", "thesis_role": "retriever", "tier": "fast", "free_model": "gemini-2.0-flash", "byok_model": "gpt-4.1-mini"},
]


def routing_decisions_payload() -> dict[str, Any]:
    """Proxy gateway routing audit; apps still select (ADR-029)."""
    metrics_url = _url("LLM_GATEWAY_OPS_URL", DEFAULT_GATEWAY_OPS)
    # Derive decisions URL from metrics URL when possible
    if metrics_url.endswith("/v1/ops/metrics"):
        url = metrics_url[: -len("/v1/ops/metrics")] + "/v1/ops/routing-decisions"
    else:
        url = _url("LLM_GATEWAY_ROUTING_OPS_URL", DEFAULT_ROUTING_OPS)
    live = fetch_plane_metrics(url)
    if live.get("reachable") and isinstance(live.get("metrics"), dict):
        return {
            "reachable": True,
            "source": "live",
            "plane": "aegis-llm-gateway",
            "url": url,
            "catalog": AGENT_MODEL_CATALOG,
            "metrics": live["metrics"],
            "honesty": "Apps select models; gateway enforces+records (ADR-029).",
        }
    if not _demo_fallback_enabled():
        return {**live, "plane": "aegis-llm-gateway", "catalog": AGENT_MODEL_CATALOG}
    return {
        "reachable": True,
        "source": "demo_fallback",
        "plane": "aegis-llm-gateway",
        "url": url,
        "catalog": AGENT_MODEL_CATALOG,
        "metrics": DEMO_ROUTING,
        "note": "Live routing audit unreachable — sample decisions for demo.",
        "honesty": "Apps select models; gateway enforces+records (ADR-029).",
    }



DEMO_KPI = {
    "service": "agent-finops",
    "kpi": "cost_per_compliant_outcome",
    "tenant_id": None,
    "compliant_outcomes": 12,
    "total_cost_usd": 1.84,
    "cost_per_compliant_outcome": 0.1533,
}


def cost_per_compliant_outcome_payload(tenant_id: str | None = None) -> dict[str, Any]:
    """Fetch ADR-029 KPI from agent-finops (AGENTFINOPS_API_URL)."""
    base = (os.getenv("AGENTFINOPS_API_URL") or os.getenv("AGENTFINOPS_URL") or "").strip()
    if not base:
        if not _demo_fallback_enabled():
            return {"reachable": False, "error": "AGENTFINOPS_API_URL_not_configured"}
        return {
            "reachable": True,
            "source": "demo_fallback",
            "plane": "agent-finops",
            "metrics": DEMO_KPI,
            "note": "Set AGENTFINOPS_API_URL for live cost-per-compliant-outcome.",
        }
    url = base.rstrip("/") + "/v1/kpi/cost-per-compliant-outcome"
    if tenant_id:
        url = f"{url}?tenant_id={tenant_id}"
    live = fetch_plane_metrics(url)
    if live.get("reachable") and isinstance(live.get("metrics"), dict):
        return {
            "reachable": True,
            "source": "live",
            "plane": "agent-finops",
            "url": url,
            "metrics": live["metrics"],
        }
    if not _demo_fallback_enabled():
        return {**live, "plane": "agent-finops"}
    return {
        "reachable": True,
        "source": "demo_fallback",
        "plane": "agent-finops",
        "url": url,
        "metrics": DEMO_KPI,
        "note": "Live FinOps KPI unreachable — demo sample.",
        "live_error": live.get("error"),
    }
