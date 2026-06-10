from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GatewayMetricsSnapshot:
    tenant_id: str
    gateway_tool_calls: int
    broker_executions: int
    executions_with_token: int
    executions_without_token: int
    bypass_attempts_blocked: int
    audit_packets_available: int
    gateway_coverage_pct: float
    pilot_target_pct: float
    mean_time_to_approve_minutes: float | None


class _AuditCounter(Protocol):
    def count_audit_events(
        self,
        tenant_id: str,
        *,
        event_type: str | None = None,
        event_type_prefix: str | None = None,
    ) -> int: ...


class GatewayMetricsService:
    """North-star KPI: % of side-effecting tool paths governed through the gateway."""

    PILOT_TARGET_PCT = 100.0

    def __init__(self, store: _AuditCounter) -> None:
        self._store = store

    def snapshot(self, tenant_id: str = "bank-demo") -> dict[str, object]:
        metrics = self._compute(tenant_id)
        return {
            "product_module": "Govern",
            "headline": "Gateway coverage — primary pilot success metric",
            "tenant_id": metrics.tenant_id,
            "pilot_target_pct": metrics.pilot_target_pct,
            "gateway_coverage_pct": metrics.gateway_coverage_pct,
            "gateway_tool_calls": metrics.gateway_tool_calls,
            "broker_executions": metrics.broker_executions,
            "executions_with_token": metrics.executions_with_token,
            "executions_without_token": metrics.executions_without_token,
            "bypass_attempts_blocked": metrics.bypass_attempts_blocked,
            "audit_packets_available": metrics.audit_packets_available,
            "mean_time_to_approve_minutes": metrics.mean_time_to_approve_minutes,
            "board_metrics": [
                {
                    "label": "Gateway coverage",
                    "value": f"{metrics.gateway_coverage_pct:.0f}%",
                    "meaning": "Side-effecting paths intercepted before execution (target 100% in 90 days)",
                },
                {
                    "label": "Gateway tool calls",
                    "value": metrics.gateway_tool_calls,
                    "meaning": "Tool requests evaluated by policy, risk, and HITL routing",
                },
                {
                    "label": "Broker executions",
                    "value": metrics.broker_executions,
                    "meaning": "Approved actions executed only through the connector broker",
                },
                {
                    "label": "Token-bound executions",
                    "value": metrics.executions_with_token,
                    "meaning": "Executions with valid gateway-issued execution token",
                },
            ],
            "recommended_actions": self._recommendations(metrics),
        }

    def _compute(self, tenant_id: str) -> GatewayMetricsSnapshot:
        gateway_calls = self._store.count_audit_events(
            tenant_id, event_type="gateway.tool_request"
        )
        with_token = self._store.count_audit_events(
            tenant_id, event_type="execution.executed"
        )
        # Executed events that recorded token binding in payload are counted separately
        token_bound = self._store.count_audit_events(
            tenant_id, event_type="execution.token_bound"
        )
        without_token = self._store.count_audit_events(
            tenant_id, event_type="execution.denied.no_token"
        )
        blocked_bypass = self._store.count_audit_events(
            tenant_id, event_type="execution.denied.invalid_token"
        )
        broker_executions = max(with_token, token_bound)
        denominator = max(gateway_calls, broker_executions, 1)
        coverage = min(
            self.PILOT_TARGET_PCT,
            round(100.0 * gateway_calls / denominator, 1),
        )
        if gateway_calls > 0 and token_bound > 0:
            coverage = min(
                self.PILOT_TARGET_PCT,
                round(100.0 * token_bound / max(broker_executions, 1), 1),
            )
        cases = 0
        if hasattr(self._store, "count"):
            try:
                cases = int(self._store.count("cases"))  # type: ignore[attr-defined]
            except (ValueError, TypeError):
                cases = 0
        return GatewayMetricsSnapshot(
            tenant_id=tenant_id,
            gateway_tool_calls=gateway_calls,
            broker_executions=broker_executions,
            executions_with_token=token_bound or with_token,
            executions_without_token=without_token,
            bypass_attempts_blocked=blocked_bypass + without_token,
            audit_packets_available=cases,
            gateway_coverage_pct=coverage,
            pilot_target_pct=self.PILOT_TARGET_PCT,
            mean_time_to_approve_minutes=None,
        )

    def _recommendations(self, metrics: GatewayMetricsSnapshot) -> list[str]:
        actions: list[str] = []
        if metrics.gateway_coverage_pct < 100:
            actions.append(
                "Route all side-effecting agent tool calls through POST /api/gateway/tool-request."
            )
        if metrics.executions_without_token > 0:
            actions.append(
                "Enable AEGISAI_REQUIRE_EXECUTION_TOKEN=true in pilot environments."
            )
        if metrics.gateway_tool_calls == 0:
            actions.append("Run the guided buyer demo to seed gateway audit events.")
        if not actions:
            actions.append("Maintain 100% gateway coverage for production promotion.")
        return actions
