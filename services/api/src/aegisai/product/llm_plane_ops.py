"""BFF helpers — proxy LLM gateway / semantic cache ops metrics into AegisAI Control Room.

Does not move LLM proxy code into AegisAI; only reads satellite plane metrics (ADR-028).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_GATEWAY_OPS = "http://127.0.0.1:8100/v1/ops/metrics"
DEFAULT_CACHE_OPS = "http://127.0.0.1:8101/v1/ops/metrics"


def _url(env_key: str, default: str) -> str:
    return (os.getenv(env_key) or default).strip()


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
            return {"reachable": True, "url": url, "metrics": data}
    except Exception as exc:  # noqa: BLE001 — Control Room must degrade gracefully
        return {"reachable": False, "url": url, "error": type(exc).__name__, "detail": str(exc)[:200]}


def gateway_ops_payload() -> dict[str, Any]:
    url = _url("LLM_GATEWAY_OPS_URL", DEFAULT_GATEWAY_OPS)
    payload = dict(fetch_plane_metrics(url))
    payload["plane"] = "aegis-llm-gateway"
    return payload


def cache_ops_payload() -> dict[str, Any]:
    url = _url("SEMANTIC_CACHE_OPS_URL", DEFAULT_CACHE_OPS)
    payload = dict(fetch_plane_metrics(url))
    payload["plane"] = "aegis-semantic-cache"
    return payload
