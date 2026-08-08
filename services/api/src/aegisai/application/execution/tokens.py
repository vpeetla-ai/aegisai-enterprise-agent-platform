from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
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
    jti: str
    tool_digest: str | None = None


class ExecutionTokenService:
    """Issues and validates HMAC-signed execution tokens (JWT-like, no external deps)."""

    def __init__(self, secret: str | None = None, ttl_seconds: int | None = None) -> None:
        self.secret = secret or os.getenv("AEGISAI_EXECUTION_TOKEN_SECRET", "dev-change-me-in-production")
        self.ttl_seconds = ttl_seconds or int(os.getenv("AEGISAI_EXECUTION_TOKEN_TTL_SECONDS", "300"))
        self._revoked_jtis: set[str] = set()

    def issue(
        self,
        *,
        tenant_id: str,
        agent_id: str,
        tool_name: str,
        gateway_decision: str,
        proposal_id: str | None = None,
        tool_digest: str | None = None,
        jti: str | None = None,
    ) -> str:
        if gateway_decision not in {"allow", "approval_required", "block", "frozen", "deny"}:
            raise ValueError(f"Unsupported gateway_decision: {gateway_decision}")
        now = int(time.time())
        token_jti = jti or str(uuid.uuid4())
        payload = {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "proposal_id": proposal_id,
            "gateway_decision": gateway_decision,
            "tool_digest": tool_digest,
            "jti": token_jti,
            "iat": now,
            "exp": now + self.ttl_seconds,
        }
        return self._encode(payload)

    def revoke(self, token_or_jti: str) -> dict[str, object]:
        """Revoke by raw token or jti. Idempotent."""
        jti = token_or_jti.strip()
        if token_or_jti.count(".") == 2:
            try:
                payload = self._decode(token_or_jti, check_revocation=False)
                jti = str(payload.get("jti") or "")
            except (ValueError, json.JSONDecodeError):
                return {"revoked": False, "reason": "malformed_token"}
        if not jti:
            return {"revoked": False, "reason": "missing_jti"}
        self._revoked_jtis.add(jti)
        return {"revoked": True, "jti": jti}

    def is_revoked(self, jti: str) -> bool:
        return jti in self._revoked_jtis

    def verify(self, token: str) -> ExecutionTokenClaims | None:
        try:
            payload = self._decode(token, check_revocation=True)
        except (ValueError, json.JSONDecodeError):
            return None
        exp = int(payload.get("exp", 0))
        if exp < int(time.time()):
            return None
        if payload.get("gateway_decision") != "allow":
            return None
        jti = str(payload.get("jti") or "")
        if not jti:
            return None
        digest = payload.get("tool_digest")
        return ExecutionTokenClaims(
            tenant_id=str(payload["tenant_id"]),
            agent_id=str(payload["agent_id"]),
            tool_name=str(payload["tool_name"]),
            proposal_id=payload.get("proposal_id"),
            gateway_decision=str(payload["gateway_decision"]),
            expires_at=exp,
            jti=jti,
            tool_digest=str(digest) if digest else None,
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

    def _decode(self, token: str, *, check_revocation: bool) -> dict[str, Any]:
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
        payload = json.loads(body)
        if check_revocation:
            jti = str(payload.get("jti") or "")
            if jti and jti in self._revoked_jtis:
                raise ValueError("Token revoked")
        return payload


def tool_args_digest(tool_name: str, arguments: dict[str, object] | None = None) -> str:
    """Stable digest binding a token to tool + args preview."""
    blob = json.dumps({"tool": tool_name, "args": arguments or {}}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()
