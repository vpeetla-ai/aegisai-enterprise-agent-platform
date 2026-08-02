"""Shared FinOps metering for cron orchestrators (content / stock).

Mirrors Website Build's pattern (ADR-0004) without pulling LangGraph deps.
Fail-soft when agent-finops is unset — Demo stays Demo.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from agent_finops_client import FinOpsClient

from aegisai.application.knowledge.llm_gateway import LLMResponse
from aegisai.product.agent_registry import AgentRegistryService
from aegisai.product.kill_switch import KillSwitchService

logger = logging.getLogger(__name__)


def default_finops_client() -> FinOpsClient:
    return FinOpsClient(
        base_url=os.getenv("AGENTFINOPS_API_URL") or os.getenv("AGENTFINOPS_URL"),
        api_key=os.getenv("AGENTFINOPS_API_KEY"),
    )


def meter_llm_response(
    *,
    agent_id: str,
    response: LLMResponse,
    finops_client: FinOpsClient | None = None,
    agent_registry: AgentRegistryService | None = None,
    kill_switch_service: KillSwitchService | None = None,
) -> bool:
    """Record usage for one LLM completion. Return True if budget breached."""
    client = finops_client or default_finops_client()
    try:
        result = client.record_usage(
            scope_type="agent",
            scope_value=agent_id,
            provider=response.provider,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
        )
    except Exception as exc:
        logger.warning("cron_finops_record_failed agent=%s err=%s", agent_id, exc)
        return False

    if agent_registry is not None:
        try:
            agent_registry.record_usage(agent_id, result.cost_usd)
        except Exception as exc:
            logger.warning("cron_finops_registry_failed agent=%s err=%s", agent_id, exc)

    if result.breached and kill_switch_service is not None:
        kill_switch_service.activate(
            "agent",
            agent_id,
            reason=(
                f"AgentFinOps budget ${result.budget_usd} exceeded "
                f"(total ${result.total_cost_usd})"
            ),
            created_by="agentfinops",
        )
        return True
    return bool(result.breached)


def finops_trace_note(breached: bool) -> dict[str, Any]:
    return {"finops_budget_breached": breached}
