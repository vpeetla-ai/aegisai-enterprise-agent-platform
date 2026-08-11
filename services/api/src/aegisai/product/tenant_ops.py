"""Tenant health + Acme embed onboarding (TTFV) — control-plane ops, not CS SaaS."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class OnboardingState:
    tenant_id: str
    created_at: float
    steps: dict[str, bool] = field(default_factory=dict)
    ttfv_seconds: float | None = None
    first_governed_at: float | None = None


class TenantOpsService:
    """Tracks embed checklist + aggregates tenant health signals."""

    CHECKLIST = (
        "connect_idp",
        "scim_sync",
        "ingest_docs",
        "connect_slack",
        "first_hitl_path",
    )

    def __init__(self) -> None:
        self._onboarding: dict[str, OnboardingState] = {}
        self._metrics: dict[str, dict[str, float]] = {}
        self._alerts: list[dict[str, Any]] = []

    def start_tenant(self, tenant_id: str) -> OnboardingState:
        state = OnboardingState(
            tenant_id=tenant_id,
            created_at=time.time(),
            steps={step: False for step in self.CHECKLIST},
        )
        self._onboarding[tenant_id] = state
        self._metrics.setdefault(
            tenant_id,
            {
                "missions_week": 0.0,
                "error_rate_pct": 0.0,
                "hitl_reject_rate_pct": 0.0,
                "budget_burn_pct": 0.0,
                "warm_sla_breaches": 0.0,
            },
        )
        return state

    def complete_step(self, tenant_id: str, step: str) -> dict[str, Any]:
        state = self._onboarding.get(tenant_id) or self.start_tenant(tenant_id)
        if step not in state.steps:
            raise KeyError(step)
        state.steps[step] = True
        if step == "first_hitl_path" and state.ttfv_seconds is None:
            state.first_governed_at = time.time()
            state.ttfv_seconds = round(state.first_governed_at - state.created_at, 3)
        return self.onboarding_payload(tenant_id)

    def record_metric(self, tenant_id: str, **kwargs: float) -> None:
        bucket = self._metrics.setdefault(
            tenant_id,
            {
                "missions_week": 0.0,
                "error_rate_pct": 0.0,
                "hitl_reject_rate_pct": 0.0,
                "budget_burn_pct": 0.0,
                "warm_sla_breaches": 0.0,
            },
        )
        for key, value in kwargs.items():
            if key in bucket:
                bucket[key] = float(value)

    def maybe_alert(self, tenant_id: str, *, channel: str = "slack") -> dict[str, Any] | None:
        m = self._metrics.get(tenant_id) or {}
        reasons: list[str] = []
        if m.get("budget_burn_pct", 0) >= 100:
            reasons.append("budget_breach")
        if m.get("error_rate_pct", 0) >= 25:
            reasons.append("error_rate_high")
        if m.get("warm_sla_breaches", 0) >= 1:
            reasons.append("warm_sla_breach")
        if not reasons:
            return None
        alert = {
            "tenant_id": tenant_id,
            "channel": channel,
            "reasons": reasons,
            "metrics": m,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        self._alerts.append(alert)
        return alert

    def onboarding_payload(self, tenant_id: str) -> dict[str, Any]:
        state = self._onboarding.get(tenant_id) or self.start_tenant(tenant_id)
        done = sum(1 for v in state.steps.values() if v)
        return {
            "product_module": "EmbedOnboarding",
            "tenant_id": tenant_id,
            "checklist": [{"id": k, "complete": v} for k, v in state.steps.items()],
            "completed_steps": done,
            "total_steps": len(state.steps),
            "ttfv_seconds": state.ttfv_seconds,
            "created_at": datetime.fromtimestamp(state.created_at, tz=UTC).isoformat(),
        }

    def health_payload(self, tenant_id: str) -> dict[str, Any]:
        m = self._metrics.get(tenant_id) or {
            "missions_week": 0.0,
            "error_rate_pct": 0.0,
            "hitl_reject_rate_pct": 0.0,
            "budget_burn_pct": 0.0,
            "warm_sla_breaches": 0.0,
        }
        onboarding = self.onboarding_payload(tenant_id)
        alert = self.maybe_alert(tenant_id)
        return {
            "product_module": "TenantHealth",
            "tenant_id": tenant_id,
            "usage": {
                "missions_per_week": m["missions_week"],
                "error_rate_pct": m["error_rate_pct"],
                "hitl_reject_rate_pct": m["hitl_reject_rate_pct"],
                "budget_burn_pct": m["budget_burn_pct"],
                "warm_sla_breaches": int(m["warm_sla_breaches"]),
            },
            "onboarding": onboarding,
            "latest_alert": alert,
            "alerts_total": len([a for a in self._alerts if a["tenant_id"] == tenant_id]),
            "honesty": "Tenant ops for the embed — not a customer-success SaaS.",
        }
