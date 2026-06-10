from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


def oidc_jwks_enabled() -> bool:
    return bool(os.getenv("AEGISAI_OIDC_ISSUER", "").strip())


def _issuer() -> str:
    return os.getenv("AEGISAI_OIDC_ISSUER", "").strip().rstrip("/")


def _jwks_uri() -> str:
    explicit = os.getenv("AEGISAI_OIDC_JWKS_URI", "").strip()
    if explicit:
        return explicit
    return f"{_issuer()}/.well-known/jwks.json"


def _audience() -> str | None:
    value = os.getenv("AEGISAI_OIDC_AUDIENCE", "").strip()
    return value or None


@lru_cache(maxsize=1)
def _jwks_client() -> Any:
    from jwt import PyJWKClient

    return PyJWKClient(_jwks_uri(), cache_keys=True)


def verify_oidc_access_token(token: str) -> dict[str, Any] | None:
    """Validate Bearer token against IdP JWKS (Okta, Azure AD, Auth0)."""
    if not oidc_jwks_enabled():
        return None
    try:
        import jwt

        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
            "issuer": _issuer(),
            "options": {"verify_aud": bool(_audience())},
        }
        if _audience():
            decode_kwargs["audience"] = _audience()
        return jwt.decode(token, signing_key.key, **decode_kwargs)
    except Exception:
        return None


def principal_from_verified_claims(claims: dict[str, Any]) -> str | None:
    for key in ("sub", "email", "preferred_username", "upn"):
        value = claims.get(key)
        if value:
            return str(value)
    return None


def roles_from_verified_claims(claims: dict[str, Any]) -> tuple[str, ...]:
    groups = claims.get("groups") or claims.get("roles") or []
    if isinstance(groups, str):
        return (groups,)
    if isinstance(groups, list):
        return tuple(str(item) for item in groups if item)
    return ()
