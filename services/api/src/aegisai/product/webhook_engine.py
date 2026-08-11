"""Generic inbound webhook engine — HMAC verify, idempotency, retry, DLQ + replay."""

from __future__ import annotations

import hashlib
import hmac
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable


@dataclass
class WebhookDelivery:
    delivery_id: str
    webhook_id: str
    tenant_id: str
    payload: dict[str, Any]
    signature_valid: bool
    idempotency_key: str
    status: str  # accepted | rejected | failed | dlq | replayed
    attempt: int = 0
    last_error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


Handler = Callable[[WebhookDelivery], None]


class WebhookEngine:
    """In-memory webhook ingress for panel drills (HMAC + DLQ)."""

    def __init__(self, *, max_attempts: int = 3, signing_secret: str | None = None) -> None:
        self.max_attempts = max_attempts
        self._secret = (signing_secret or os.getenv("AEGISAI_WEBHOOK_HMAC_SECRET", "acme-embed-dev-secret")).encode()
        self._handlers: dict[str, Handler] = {}
        self._deliveries: dict[str, WebhookDelivery] = {}
        self._idempotency: dict[str, str] = {}  # key -> delivery_id
        self._dlq: list[str] = []

    def register_handler(self, webhook_id: str, handler: Handler) -> None:
        self._handlers[webhook_id] = handler

    def sign_body(self, body: bytes) -> str:
        digest = hmac.new(self._secret, body, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def verify_signature(self, body: bytes, signature_header: str | None) -> bool:
        if not signature_header:
            return False
        expected = self.sign_body(body)
        return hmac.compare_digest(expected, signature_header.strip())

    def ingest(
        self,
        *,
        webhook_id: str,
        tenant_id: str,
        payload: dict[str, Any],
        raw_body: bytes,
        signature_header: str | None,
        idempotency_key: str | None = None,
        force_fail: bool = False,
    ) -> WebhookDelivery:
        if not self.verify_signature(raw_body, signature_header):
            delivery = WebhookDelivery(
                delivery_id=str(uuid.uuid4()),
                webhook_id=webhook_id,
                tenant_id=tenant_id,
                payload=payload,
                signature_valid=False,
                idempotency_key=idempotency_key or "",
                status="rejected",
                last_error="invalid_hmac_signature",
            )
            self._deliveries[delivery.delivery_id] = delivery
            return delivery

        key = idempotency_key or hashlib.sha256(raw_body).hexdigest()
        if key in self._idempotency:
            existing = self._deliveries[self._idempotency[key]]
            return existing

        delivery = WebhookDelivery(
            delivery_id=str(uuid.uuid4()),
            webhook_id=webhook_id,
            tenant_id=tenant_id,
            payload=payload,
            signature_valid=True,
            idempotency_key=key,
            status="accepted",
        )
        self._deliveries[delivery.delivery_id] = delivery
        self._idempotency[key] = delivery.delivery_id
        self._process(delivery, force_fail=force_fail)
        return delivery

    def _process(self, delivery: WebhookDelivery, *, force_fail: bool = False) -> None:
        handler = self._handlers.get(delivery.webhook_id)
        for attempt in range(1, self.max_attempts + 1):
            delivery.attempt = attempt
            delivery.updated_at = datetime.now(UTC).isoformat()
            try:
                if force_fail:
                    raise RuntimeError("forced_connector_failure")
                if handler is None:
                    # Accept-only path when no handler registered (storage + audit).
                    delivery.status = "accepted"
                    return
                handler(delivery)
                delivery.status = "accepted" if attempt == 1 else "replayed"
                return
            except Exception as exc:  # noqa: BLE001 — panel drill surfaces any handler error
                delivery.last_error = str(exc)
                backoff = min(2 ** (attempt - 1), 8)
                time.sleep(0)  # deterministic; real worker would sleep(backoff)
                _ = backoff
        delivery.status = "dlq"
        if delivery.delivery_id not in self._dlq:
            self._dlq.append(delivery.delivery_id)

    def replay(self, delivery_id: str) -> WebhookDelivery:
        delivery = self._deliveries.get(delivery_id)
        if delivery is None:
            raise KeyError(delivery_id)
        delivery.status = "accepted"
        delivery.last_error = None
        self._process(delivery, force_fail=False)
        if delivery.status == "accepted":
            delivery.status = "replayed"
            if delivery_id in self._dlq:
                self._dlq.remove(delivery_id)
        return delivery

    def list_dlq(self, tenant_id: str | None = None) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for delivery_id in self._dlq:
            d = self._deliveries[delivery_id]
            if tenant_id and d.tenant_id != tenant_id:
                continue
            rows.append(self.to_payload(d))
        return rows

    def get(self, delivery_id: str) -> WebhookDelivery | None:
        return self._deliveries.get(delivery_id)

    @staticmethod
    def to_payload(delivery: WebhookDelivery) -> dict[str, object]:
        return {
            "delivery_id": delivery.delivery_id,
            "webhook_id": delivery.webhook_id,
            "tenant_id": delivery.tenant_id,
            "signature_valid": delivery.signature_valid,
            "idempotency_key": delivery.idempotency_key,
            "status": delivery.status,
            "attempt": delivery.attempt,
            "last_error": delivery.last_error,
            "created_at": delivery.created_at,
            "updated_at": delivery.updated_at,
            "payload": delivery.payload,
        }

    def posture(self) -> dict[str, object]:
        return {
            "product_module": "WebhookEngine",
            "handlers": sorted(self._handlers),
            "deliveries": len(self._deliveries),
            "dlq_depth": len(self._dlq),
            "max_attempts": self.max_attempts,
            "hmac_algo": "sha256",
        }
