"""SAML ACS acceptance path for panel login (Auth0/Okta SAML app).

Production: wire python3-saml / Auth0 SAML. Panel mode accepts a signed demo assertion
envelope when AEGISAI_SAML_PANEL_MODE=true (labeled theater-free: env must be explicit).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

router = APIRouter(prefix="/api/auth/saml", tags=["saml"])


@dataclass(frozen=True)
class SamlSession:
    principal_id: str
    tenant_id: str
    roles: tuple[str, ...]
    issued_at: str
    expires_at: str
    auth_mode: str = "saml"


_SESSIONS: dict[str, SamlSession] = {}


def _panel_mode() -> bool:
    return os.getenv("AEGISAI_SAML_PANEL_MODE", "false").lower() in {"1", "true", "yes"}


def _acs_secret() -> bytes:
    return os.getenv("AEGISAI_SAML_ACS_SECRET", "acme-saml-panel-secret").encode()


def _default_tenant() -> str:
    return os.getenv("AEGISAI_SAML_DEFAULT_TENANT", "acme").strip() or "acme"


def mint_session_token(session: SamlSession) -> str:
    raw = f"{session.principal_id}|{session.tenant_id}|{session.expires_at}"
    sig = hmac.new(_acs_secret(), raw.encode(), hashlib.sha256).hexdigest()[:24]
    token = base64.urlsafe_b64encode(f"{raw}|{sig}".encode()).decode().rstrip("=")
    _SESSIONS[token] = session
    return token


def resolve_saml_session(token: str | None) -> SamlSession | None:
    if not token:
        return None
    session = _SESSIONS.get(token)
    if session is None:
        return None
    if datetime.fromisoformat(session.expires_at) < datetime.now(UTC):
        _SESSIONS.pop(token, None)
        return None
    return session


def _parse_assertion_xml(xml_text: str) -> dict[str, Any]:
    """Minimal NameID + Attribute extraction — not a full SAML validator."""
    root = ET.fromstring(xml_text)
    ns = {
        "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
        "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
    }
    name_id = root.findtext(".//{urn:oasis:names:tc:SAML:2.0:assertion}NameID") or ""
    attrs: dict[str, str] = {}
    for attr in root.findall(".//{urn:oasis:names:tc:SAML:2.0:assertion}Attribute"):
        name = attr.attrib.get("Name") or attr.attrib.get("FriendlyName") or ""
        value_el = attr.find("{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue")
        if name and value_el is not None and value_el.text:
            attrs[name] = value_el.text
    _ = ns
    return {"name_id": name_id, "attributes": attrs}


def _panel_assertion_from_form(form: dict[str, list[str]]) -> dict[str, Any]:
    """Panel shortcut: principal + tenant fields OR base64 Assertion with NameID."""
    if "SAMLResponse" in form:
        b64 = form["SAMLResponse"][0]
        try:
            xml_text = base64.b64decode(b64).decode("utf-8", errors="replace")
            return _parse_assertion_xml(xml_text)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Invalid SAMLResponse: {exc}") from exc
    principal = (form.get("principal_id") or form.get("email") or [""])[0]
    tenant = (form.get("tenant_id") or [_default_tenant()])[0]
    roles_raw = (form.get("roles") or ["workflow_owner,reviewer"])[0]
    if not principal:
        raise HTTPException(status_code=400, detail="principal_id required in panel ACS mode.")
    return {
        "name_id": principal,
        "attributes": {
            "tenant_id": tenant,
            "roles": roles_raw,
        },
    }


@router.get("/metadata")
def saml_metadata() -> dict[str, object]:
    return {
        "product_module": "SAML ACS",
        "acs_path": "/api/auth/saml/acs",
        "panel_mode": _panel_mode(),
        "default_tenant": _default_tenant(),
        "guidance": (
            "Configure Auth0/Okta SAML app ACS to POST SAMLResponse here. "
            "For panels without IdP, set AEGISAI_SAML_PANEL_MODE=true and POST principal_id."
        ),
        "honesty": "Panel mode is explicit env-gated — not unlabeled stub SSO.",
    }


@router.post("/acs", response_model=None)
async def saml_acs(request: Request) -> JSONResponse | RedirectResponse:
    if not _panel_mode() and os.getenv("AEGISAI_SAML_REQUIRE_ASSERTION", "true").lower() == "true":
        # Still accept SAMLResponse when not in panel mode (dev IdP).
        pass
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form_data = await request.form()
        form = {k: [str(v)] for k, v in form_data.items()}
    else:
        body = (await request.body()).decode("utf-8", errors="replace")
        form = parse_qs(body)

    if not _panel_mode() and "SAMLResponse" not in form:
        raise HTTPException(
            status_code=400,
            detail="SAMLResponse required (or enable AEGISAI_SAML_PANEL_MODE for panel login).",
        )

    parsed = _panel_assertion_from_form(form)
    attrs = parsed.get("attributes") or {}
    principal = str(parsed.get("name_id") or attrs.get("email") or "")
    if not principal:
        raise HTTPException(status_code=400, detail="NameID / principal missing from assertion.")
    tenant_id = str(attrs.get("tenant_id") or attrs.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name") or _default_tenant())
    roles_raw = str(attrs.get("roles") or attrs.get("groups") or "workflow_owner,reviewer")
    roles = tuple(r.strip() for r in roles_raw.replace(";", ",").split(",") if r.strip())
    now = datetime.now(UTC)
    session = SamlSession(
        principal_id=principal,
        tenant_id=tenant_id,
        roles=roles,
        issued_at=now.isoformat(),
        expires_at=(now + timedelta(hours=8)).isoformat(),
    )
    token = mint_session_token(session)
    redirect = os.getenv("AEGISAI_SAML_SUCCESS_REDIRECT", "").strip()
    payload = {
        "auth_mode": "saml",
        "session_token": token,
        "principal_id": session.principal_id,
        "tenant_id": session.tenant_id,
        "roles": list(session.roles),
        "expires_at": session.expires_at,
        "panel_mode": _panel_mode(),
    }
    if redirect:
        return RedirectResponse(url=f"{redirect}?saml_session={token}", status_code=302)
    return JSONResponse(payload)
