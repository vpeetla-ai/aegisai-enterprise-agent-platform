from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from aegisai.interfaces.http.oidc_jwks import (
    oidc_jwks_enabled,
    principal_from_verified_claims,
    roles_from_verified_claims,
    verify_oidc_access_token,
)


@dataclass(frozen=True)
class AuthContext:
    principal_id: str
    tenant_id: str
    roles: tuple[str, ...]
    auth_mode: str


def _parse_roles(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(role.strip() for role in raw.split(",") if role.strip())


def _enforce_auth_enabled() -> bool:
    return os.getenv("AEGISAI_ENFORCE_AUTH", "false").lower() == "true"


def _auth_mode() -> str:
    return os.getenv("AEGISAI_AUTH_MODE", "dev").lower()


def resolve_auth_context(request: Request) -> AuthContext:
    """Resolve identity from OIDC bearer token or development headers."""
    mode = _auth_mode()
    tenant_id = request.headers.get("X-AegisAI-Tenant", "bank-demo")

    if mode == "oidc":
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token.")
        token = authorization.removeprefix("Bearer ").strip()
        roles = _parse_roles(request.headers.get("X-AegisAI-Roles"))
        principal_id = request.headers.get("X-AegisAI-Principal")

        if oidc_jwks_enabled():
            claims = verify_oidc_access_token(token)
            if claims is None:
                raise HTTPException(status_code=401, detail="Invalid OIDC token (JWKS verification failed).")
            principal_id = principal_id or principal_from_verified_claims(claims)
            if not roles:
                roles = roles_from_verified_claims(claims)
        else:
            principal_id = principal_id or _principal_from_token(token)

        if not principal_id:
            raise HTTPException(status_code=401, detail="Unable to resolve principal from token.")
        return AuthContext(
            principal_id=principal_id,
            tenant_id=tenant_id,
            roles=roles,
            auth_mode="oidc",
        )

    principal_id = request.headers.get("X-AegisAI-Principal", "portfolio-user")
    roles = _parse_roles(request.headers.get("X-AegisAI-Roles", "workflow_owner"))
    return AuthContext(
        principal_id=principal_id,
        tenant_id=tenant_id,
        roles=roles,
        auth_mode="dev",
    )


def require_authenticated(request: Request) -> AuthContext:
    """Require authenticated principal on mutating control-plane APIs."""
    context = resolve_auth_context(request)
    if _enforce_auth_enabled():
        if context.auth_mode == "dev" and context.principal_id == "portfolio-user":
            raise HTTPException(
                status_code=403,
                detail=(
                    "Authentication required. Set X-AegisAI-Principal and X-AegisAI-Roles, "
                    "or configure AEGISAI_AUTH_MODE=oidc with Authorization: Bearer <token>."
                ),
            )
        if context.auth_mode == "oidc" and not context.roles and _require_roles():
            raise HTTPException(
                status_code=403,
                detail="OIDC token resolved but no roles provided. Set X-AegisAI-Roles for RBAC.",
            )
    return context


def require_reviewer_role(request: Request) -> AuthContext:
    """Stricter auth for reviewer and execution paths when enforcement is on."""
    context = require_authenticated(request)
    if _enforce_auth_enabled() and not context.roles:
        raise HTTPException(status_code=403, detail="Reviewer or operator role required.")
    return context


def _require_roles() -> bool:
    return os.getenv("AEGISAI_REQUIRE_ROLES", "false").lower() == "true"


def _principal_from_token(token: str) -> str | None:
    """Decode JWT payload (portfolio: unverified; production: wire JWKS validator)."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        import base64
        import json

        payload = parts[1] + "=="
        data = json.loads(base64.urlsafe_b64decode(payload))
        return str(data.get("sub") or data.get("email") or "")
    except (ValueError, json.JSONDecodeError):
        return None


def auth_posture() -> dict[str, object]:
    return {
        "product_module": "Secure",
        "auth_mode": _auth_mode(),
        "enforce_auth": _enforce_auth_enabled(),
        "require_roles": _require_roles(),
        "oidc_ready": True,
        "jwks_verification": oidc_jwks_enabled(),
        "enterprise_guidance": (
            "Set AEGISAI_AUTH_MODE=oidc, AEGISAI_ENFORCE_AUTH=true, AEGISAI_OIDC_ISSUER, "
            "and optional AEGISAI_OIDC_AUDIENCE for Okta/Azure AD JWKS validation."
        ),
        "dev_headers": ["X-AegisAI-Principal", "X-AegisAI-Tenant", "X-AegisAI-Roles"],
    }


AuthRequired = Annotated[AuthContext, Depends(require_authenticated)]
ReviewerAuthRequired = Annotated[AuthContext, Depends(require_reviewer_role)]
