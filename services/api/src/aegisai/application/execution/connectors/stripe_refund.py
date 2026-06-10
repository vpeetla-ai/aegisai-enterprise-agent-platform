from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class StripeRefundRequest:
    amount_usd: float
    currency: str
    charge_id: str | None
    idempotency_key: str
    reason: str = "requested_by_customer"


@dataclass(frozen=True)
class StripeRefundResult:
    mode: str
    refund_id: str
    status: str
    amount_usd: float
    message: str


class StripeRefundConnector:
    """Stripe refund connector with mock mode when STRIPE_SECRET_KEY is unset."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("STRIPE_SECRET_KEY", "").strip()

    @property
    def live_mode(self) -> bool:
        return bool(self.api_key)

    def issue_refund(self, request: StripeRefundRequest) -> StripeRefundResult:
        if not self.live_mode:
            refund_id = f"mock_refund_{uuid4()}"
            return StripeRefundResult(
                mode="mock",
                refund_id=refund_id,
                status="succeeded",
                amount_usd=request.amount_usd,
                message="Mock Stripe refund executed (set STRIPE_SECRET_KEY for live mode).",
            )

        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("httpx is required for live Stripe refunds.") from exc

        amount_cents = int(round(request.amount_usd * 100))
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": request.idempotency_key,
        }
        if request.charge_id:
            data = {"charge": request.charge_id, "amount": amount_cents, "reason": request.reason}
        else:
            data = {"amount": amount_cents, "reason": request.reason}
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.stripe.com/v1/refunds",
                data=data,
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
        return StripeRefundResult(
            mode="live",
            refund_id=str(payload.get("id", f"refund_{uuid4()}")),
            status=str(payload.get("status", "succeeded")),
            amount_usd=request.amount_usd,
            message="Stripe refund created.",
        )
