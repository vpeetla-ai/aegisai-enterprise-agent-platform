from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from uuid import uuid4

from .registry import (
    ConnectorExecutionContext,
    ConnectorExecutionResult,
    ConnectorRegistry,
    EnterpriseConnector,
)


def _default_store_path() -> Path:
    configured = os.getenv("AEGISAI_HTTP_CONNECTORS_FILE")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[5] / "data" / "http_connectors.json"


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return normalized[:48] or "integration"


@dataclass(frozen=True)
class HttpConnectorRegistration:
    connector_id: str
    display_name: str
    base_url: str
    target_system: str
    tool_names: tuple[str, ...] = ()
    provider: str = "http"
    http_method: str = "POST"
    execute_path: str = "/execute"
    health_path: str = "/health"
    auth_mode: str = "none"
    auth_header_name: str = "Authorization"
    auth_secret_env: str | None = None
    demo_mode: bool = False
    created_by: str = "platform-lead"

    def to_catalog_entry(self) -> dict[str, object]:
        parsed = urlparse(self.base_url)
        return {
            "connector_id": self.connector_id,
            "provider": self.provider,
            "supported_tools": list(self.tool_names),
            "kind": "http",
            "display_name": self.display_name,
            "target_system": self.target_system,
            "base_url": self.base_url,
            "base_url_host": parsed.netloc or self.base_url,
            "http_method": self.http_method,
            "execute_path": self.execute_path,
            "health_path": self.health_path,
            "auth_mode": self.auth_mode,
            "demo_mode": self.demo_mode,
        }

    def to_public_dict(self) -> dict[str, object]:
        entry = self.to_catalog_entry()
        entry["auth_secret_env"] = self.auth_secret_env
        entry["created_by"] = self.created_by
        return entry


class HttpEnterpriseConnector:
    """Executes approved actions by calling a customer-registered HTTP endpoint."""

    def __init__(
        self,
        registration: HttpConnectorRegistration,
        auth_value: str | None = None,
    ) -> None:
        self.registration = registration
        self.connector_id = registration.connector_id
        self.provider = registration.provider
        self.supported_tools = registration.tool_names
        self._auth_value = auth_value

    def can_handle(self, tool_name: str, target_system: str, action_type: str) -> bool:
        if tool_name and tool_name in self.supported_tools:
            return True
        return target_system == self.registration.target_system

    def execute(self, context: ConnectorExecutionContext) -> ConnectorExecutionResult:
        registration = self.registration
        if context.dry_run or registration.demo_mode:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"http://dry-run/{registration.target_system}/{uuid4()}",
                message=(
                    "Dry-run or demo mode — HTTP endpoint not invoked. "
                    "Disable demo_mode for live execution."
                ),
                provider=self.provider,
            )

        url = _join_url(registration.base_url, registration.execute_path)
        payload = {
            "tenant_id": context.tenant_id,
            "case_id": context.case_id,
            "proposal_id": context.proposal_id,
            "action_type": context.action_type,
            "target_system": context.target_system,
            "amount_usd": context.amount_usd,
            "idempotency_key": context.idempotency_key,
        }
        response = _http_request(
            method=registration.http_method,
            url=url,
            json_body=payload,
            auth_mode=registration.auth_mode,
            auth_header_name=registration.auth_header_name,
            auth_value=self._resolve_auth_value(),
            timeout_seconds=30.0,
        )
        external_reference = _extract_external_reference(response, registration.target_system)
        return ConnectorExecutionResult(
            connector_id=self.connector_id,
            external_reference=external_reference,
            message=f"HTTP connector invoked ({response.get('status_code')}).",
            provider=self.provider,
        )

    def _resolve_auth_value(self) -> str | None:
        if self._auth_value:
            return self._auth_value
        env_name = self.registration.auth_secret_env
        if env_name:
            return os.getenv(env_name)
        return None


@dataclass
class HttpConnectorTestResult:
    success: bool
    status_code: int | None
    latency_ms: int
    message: str
    url: str


class HttpConnectorStore:
    """Persists HTTP connector definitions (secrets referenced via env, not stored)."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _default_store_path()
        self._registrations: dict[str, HttpConnectorRegistration] = {}
        self._runtime_auth: dict[str, str] = {}

    def load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        items = raw.get("connectors", [])
        for item in items:
            registration = _registration_from_dict(item)
            self._registrations[registration.connector_id] = registration

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "connectors": [
                _registration_to_persist(registration)
                for registration in self._registrations.values()
            ]
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def list_registrations(self) -> tuple[HttpConnectorRegistration, ...]:
        return tuple(self._registrations.values())

    def get(self, connector_id: str) -> HttpConnectorRegistration | None:
        return self._registrations.get(connector_id)

    def upsert(
        self,
        registration: HttpConnectorRegistration,
        auth_value: str | None = None,
    ) -> HttpConnectorRegistration:
        self._registrations[registration.connector_id] = registration
        if auth_value:
            self._runtime_auth[registration.connector_id] = auth_value
        self.save()
        return registration

    def delete(self, connector_id: str) -> bool:
        if connector_id not in self._registrations:
            return False
        del self._registrations[connector_id]
        self._runtime_auth.pop(connector_id, None)
        self.save()
        return True

    def auth_value_for(self, connector_id: str) -> str | None:
        return self._runtime_auth.get(connector_id)


class HttpConnectorManager:
    """Registers customer HTTP integrations with the execution broker."""

    def __init__(self, registry: ConnectorRegistry, store: HttpConnectorStore | None = None) -> None:
        self.registry = registry
        self.store = store or HttpConnectorStore()
        self._connector_instances: dict[str, HttpEnterpriseConnector] = {}

    def bootstrap(self) -> None:
        self.store.load()
        for registration in self.store.list_registrations():
            self._mount(registration)

    def list_http_connectors(self) -> tuple[dict[str, object], ...]:
        return tuple(item.to_public_dict() for item in self.store.list_registrations())

    def register(
        self,
        *,
        display_name: str,
        base_url: str,
        target_system: str,
        tool_names: tuple[str, ...],
        connector_id: str | None = None,
        http_method: str = "POST",
        execute_path: str = "/execute",
        health_path: str = "/health",
        auth_mode: str = "none",
        auth_header_name: str = "Authorization",
        auth_secret_env: str | None = None,
        auth_value: str | None = None,
        demo_mode: bool = False,
        created_by: str = "platform-lead",
    ) -> HttpConnectorRegistration:
        normalized_url = base_url.rstrip("/")
        if not normalized_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")

        resolved_id = connector_id or f"http_{_slug(target_system)}_{uuid4().hex[:8]}"
        registration = HttpConnectorRegistration(
            connector_id=resolved_id,
            display_name=display_name,
            base_url=normalized_url,
            target_system=target_system,
            tool_names=tool_names,
            http_method=http_method.upper(),
            execute_path=execute_path if execute_path.startswith("/") else f"/{execute_path}",
            health_path=health_path if health_path.startswith("/") else f"/{health_path}",
            auth_mode=auth_mode,
            auth_header_name=auth_header_name,
            auth_secret_env=auth_secret_env,
            demo_mode=demo_mode,
            created_by=created_by,
        )
        self.store.upsert(registration, auth_value=auth_value)
        self._mount(registration)
        return registration

    def delete(self, connector_id: str) -> bool:
        removed = self.store.delete(connector_id)
        if removed:
            self.registry.unregister(connector_id)
            self._connector_instances.pop(connector_id, None)
        return removed

    def test_connection(
        self,
        *,
        base_url: str | None = None,
        health_path: str = "/health",
        http_method: str = "GET",
        auth_mode: str = "none",
        auth_header_name: str = "Authorization",
        auth_value: str | None = None,
        auth_secret_env: str | None = None,
        connector_id: str | None = None,
        demo_mode: bool = False,
    ) -> HttpConnectorTestResult:
        if connector_id:
            registration = self.store.get(connector_id)
            if registration is None:
                raise ValueError(f"Unknown connector_id: {connector_id}")
            base_url = registration.base_url
            health_path = registration.health_path
            http_method = "GET"
            auth_mode = registration.auth_mode
            auth_header_name = registration.auth_header_name
            auth_value = auth_value or self.store.auth_value_for(connector_id)
            auth_secret_env = registration.auth_secret_env
            demo_mode = registration.demo_mode

        if not base_url:
            raise ValueError("base_url is required when connector_id is not provided.")

        if demo_mode:
            return HttpConnectorTestResult(
                success=True,
                status_code=200,
                latency_ms=0,
                message="Demo mode — connection marked reachable without calling the endpoint.",
                url=base_url,
            )

        url = _join_url(base_url.rstrip("/"), health_path)
        resolved_auth = auth_value or (os.getenv(auth_secret_env) if auth_secret_env else None)
        import time

        started = time.perf_counter()
        response = _http_request(
            method=http_method.upper(),
            url=url,
            json_body=None,
            auth_mode=auth_mode,
            auth_header_name=auth_header_name,
            auth_value=resolved_auth,
            timeout_seconds=10.0,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        status_code = int(response.get("status_code") or 0)
        success = 200 <= status_code < 400
        return HttpConnectorTestResult(
            success=success,
            status_code=status_code,
            latency_ms=latency_ms,
            message="Reachable" if success else f"Unexpected status {status_code}",
            url=url,
        )

    def _mount(self, registration: HttpConnectorRegistration) -> None:
        auth_value = self.store.auth_value_for(registration.connector_id)
        connector = HttpEnterpriseConnector(registration, auth_value=auth_value)
        self._connector_instances[registration.connector_id] = connector
        self.registry.register_connector(connector)


def _join_url(base_url: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))


def _http_request(
    *,
    method: str,
    url: str,
    json_body: dict[str, Any] | None,
    auth_mode: str,
    auth_header_name: str,
    auth_value: str | None,
    timeout_seconds: float,
) -> dict[str, object]:
    import httpx

    headers: dict[str, str] = {"Accept": "application/json"}
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    if auth_mode == "bearer" and auth_value:
        headers[auth_header_name] = (
            auth_value if auth_value.lower().startswith("bearer ") else f"Bearer {auth_value}"
        )
    elif auth_mode == "api_key" and auth_value:
        headers[auth_header_name] = auth_value

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.request(method, url, json=json_body, headers=headers)
        body: object
        try:
            body = response.json()
        except ValueError:
            body = response.text[:500]
        return {
            "status_code": response.status_code,
            "body": body,
        }


def _extract_external_reference(response: dict[str, object], target_system: str) -> str:
    body = response.get("body")
    if isinstance(body, dict):
        for key in ("external_reference", "id", "reference", "transaction_id"):
            value = body.get(key)
            if value:
                return f"http://{target_system}/{value}"
    status_code = response.get("status_code")
    return f"http://{target_system}/responses/{status_code}/{uuid4()}"


def _registration_from_dict(item: dict[str, object]) -> HttpConnectorRegistration:
    tools = item.get("tool_names") or item.get("supported_tools") or ()
    return HttpConnectorRegistration(
        connector_id=str(item["connector_id"]),
        display_name=str(item.get("display_name") or item["connector_id"]),
        base_url=str(item["base_url"]),
        target_system=str(item["target_system"]),
        tool_names=tuple(str(tool) for tool in tools),
        provider=str(item.get("provider") or "http"),
        http_method=str(item.get("http_method") or "POST"),
        execute_path=str(item.get("execute_path") or "/execute"),
        health_path=str(item.get("health_path") or "/health"),
        auth_mode=str(item.get("auth_mode") or "none"),
        auth_header_name=str(item.get("auth_header_name") or "Authorization"),
        auth_secret_env=(
            str(item["auth_secret_env"]) if item.get("auth_secret_env") else None
        ),
        demo_mode=bool(item.get("demo_mode", False)),
        created_by=str(item.get("created_by") or "platform-lead"),
    )


def _registration_to_persist(registration: HttpConnectorRegistration) -> dict[str, object]:
    return {
        "connector_id": registration.connector_id,
        "display_name": registration.display_name,
        "base_url": registration.base_url,
        "target_system": registration.target_system,
        "tool_names": list(registration.tool_names),
        "provider": registration.provider,
        "http_method": registration.http_method,
        "execute_path": registration.execute_path,
        "health_path": registration.health_path,
        "auth_mode": registration.auth_mode,
        "auth_header_name": registration.auth_header_name,
        "auth_secret_env": registration.auth_secret_env,
        "demo_mode": registration.demo_mode,
        "created_by": registration.created_by,
    }
