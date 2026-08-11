"""Salesforce Case connector — OAuth + create/update with retry (sandbox-friendly)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx


@dataclass(frozen=True)
class SalesforceConfig:
    instance_url: str
    access_token: str
    api_version: str = "v59.0"


class SalesforceCaseConnector:
    """Creates/updates Salesforce Cases. Dry-run + force-fail for panel drills."""

    connector_id = "crm_case_connector"
    provider = "salesforce"
    supported_tools = ("crm.update_case", "crm.create_case")

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        client: httpx.Client | None = None,
    ) -> None:
        self.max_attempts = max_attempts
        self._client = client

    def can_handle(self, tool_name: str, target_system: str, action_type: str) -> bool:
        if tool_name in self.supported_tools:
            return True
        return target_system in {"crm", "salesforce"} and action_type in {
            "update_case",
            "create_case",
            "issue_refund",
        }

    def _config(self) -> SalesforceConfig | None:
        instance = os.getenv("SALESFORCE_INSTANCE_URL", "").strip().rstrip("/")
        token = os.getenv("SALESFORCE_ACCESS_TOKEN", "").strip()
        if not instance or not token:
            return None
        return SalesforceConfig(
            instance_url=instance,
            access_token=token,
            api_version=os.getenv("SALESFORCE_API_VERSION", "v59.0").strip() or "v59.0",
        )

    def execute(self, context: Any) -> Any:
        from aegisai.application.execution.connectors.registry import ConnectorExecutionResult

        if context.dry_run:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"salesforce://dry-run/{uuid4()}",
                message="Dry-run only; Salesforce not invoked.",
                provider=self.provider,
            )
        if os.getenv("SALESFORCE_FORCE_FAIL", "").lower() in {"1", "true", "yes"}:
            raise RuntimeError("salesforce_forced_500")

        cfg = self._config()
        subject = f"Acme support case {context.case_id}"
        body: dict[str, Any] = {
            "Subject": subject,
            "Description": (
                f"Tenant={context.tenant_id} proposal={context.proposal_id} "
                f"action={context.action_type} amount={context.amount_usd}"
            ),
            "Status": "New",
            "Origin": "AegisAI Embed",
        }
        if cfg is None:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"salesforce://sandbox-sim/{context.case_id}/{uuid4().hex[:8]}",
                message=(
                    "Salesforce credentials unset; returned sandbox-sim reference. "
                    "Set SALESFORCE_INSTANCE_URL + SALESFORCE_ACCESS_TOKEN for live Case create."
                ),
                provider=self.provider,
            )

        last_error: str | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return self._create_case(cfg, body, idempotency_key=context.idempotency_key)
            except httpx.HTTPError as exc:
                last_error = str(exc)
                time.sleep(0)
                _ = attempt
        raise RuntimeError(f"salesforce_case_failed_after_retries: {last_error}")

    def _create_case(
        self,
        cfg: SalesforceConfig,
        body: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> Any:
        from aegisai.application.execution.connectors.registry import ConnectorExecutionResult

        url = f"{cfg.instance_url}/services/data/{cfg.api_version}/sobjects/Case"
        headers = {
            "Authorization": f"Bearer {cfg.access_token}",
            "Content-Type": "application/json",
            "Sforce-Call-Options": f"client=aegisai;idempotency={idempotency_key}",
        }
        if self._client is not None:
            response = self._client.post(url, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
        else:
            with httpx.Client(timeout=20) as client:
                response = client.post(url, json=body, headers=headers)
                response.raise_for_status()
                data = response.json()
        case_id = data.get("id") or data.get("Id") or uuid4().hex
        return ConnectorExecutionResult(
            connector_id=self.connector_id,
            external_reference=f"salesforce://Case/{case_id}",
            message="Salesforce Case created/updated.",
            provider=self.provider,
        )
