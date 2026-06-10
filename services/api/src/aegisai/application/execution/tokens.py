from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionTokenClaims:
    tenant_id: str
    agent_id: str
    tool_name: str
    proposal_id: str | None
    gateway_decision: str
    expires_at: int


class ExecutionTokenService:
    """Issues and validates HMAC-signed execution tokens (JWT-like, no external deps)."""

    def __init__(self, secret: str | None = None, ttl_seconds: int | None = None) -> None:
        self.secret = secret or os.getenv("AEGISAI_EXECUTION_TOKEN_SECRET", "dev-change-me-in-production")
        self.ttl_seconds = ttl_seconds or int(os.getenv("AEGISAI_EXECUTION_TOKEN_TTL_SECONDS", "300"))

    def issue(
        self,
        *,
        tenant_id: str,
        agent_id: str,
        tool_name: str,
        gateway_decision: str,
        proposal_id: str | None = None,
    ) -> str:
        if gateway_decision not in {"allow", "approval_required", "block", "frozen", "deny"}:
            raise ValueError(f"Unsupported gateway_decision: {gateway_decision}")
        now = int(time.time())
        payload = {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "proposal_id": proposal_id,
            "gateway_decision": gateway_decision,
            "iat": now,
            "exp": now + self.ttl_seconds,
        }
        return self._encode(payload)

    def verify(self, token: str) -> ExecutionTokenClaims | None:
        try:
            payload = self._decode(token)
        except (ValueError, json.JSONDecodeError):
            return None
        exp = int(payload.get("exp", 0))
        if exp < int(time.time()):
            return None
        if payload.get("gateway_decision") != "allow":
            return None
        return ExecutionTokenClaims(
            tenant_id=str(payload["tenant_id"]),
            agent_id=str(payload["agent_id"]),
            tool_name=str(payload["tool_name"]),
            proposal_id=payload.get("proposal_id"),
            gateway_decision=str(payload["gateway_decision"]),
            expires_at=exp,
        )

    def _encode(self, payload: dict[str, Any]) -> str:
        header = urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
        body = urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
        signing_input = f"{header}.{body}"
        signature = hmac.new(
            self.secret.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest()
        sig = urlsafe_b64encode(signature).decode().rstrip("=")
        return f"{signing_input}.{sig}"

    def _decode(self, token: str) -> dict[str, Any]:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed token")
        header_b64, body_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{body_b64}"
        expected = hmac.new(
            self.secret.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest()
        actual = urlsafe_b64decode(sig_b64 + "==")
        if not hmac.compare_digest(expected, actual):
            raise ValueError("Invalid signature")
        body = urlsafe_b64decode(body_b64 + "==")
        return json.loads(body)
