"""SCIM 2.0 subset — Users + Groups → IdentityRBAC store (Acme embed)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from aegisai.product.identity_rbac import IdentityRBACService, Principal

router = APIRouter(prefix="/scim/v2", tags=["scim"])


class ScimEmail(BaseModel):
    value: str
    primary: bool = True


class ScimUser(BaseModel):
    userName: str
    active: bool = True
    displayName: str | None = None
    emails: list[ScimEmail] = Field(default_factory=list)
    externalId: str | None = None
    tenant_id: str | None = Field(default=None, alias="tenantId")
    roles: list[str] = Field(default_factory=lambda: ["workflow_owner"])
    allowed_tools: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ScimGroup(BaseModel):
    displayName: str
    members: list[dict[str, str]] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)


def _service(request: Request) -> IdentityRBACService:
    service = getattr(request.app.state, "identity_service", None)
    if service is None:
        raise HTTPException(status_code=500, detail="Identity service not configured.")
    return service


def _user_resource(principal: Principal, *, active: bool = True) -> dict[str, Any]:
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": principal.principal_id,
        "userName": principal.principal_id,
        "active": active and not principal.principal_id.endswith(":deactivated"),
        "displayName": principal.principal_id,
        "meta": {
            "resourceType": "User",
            "lastModified": datetime.now(UTC).isoformat(),
        },
        "roles": [{"value": r} for r in principal.roles],
        "urn:aegisai:params:scim:schemas:extension:tenant:2.0:User": {
            "tenant_id": principal.tenant_id,
            "allowed_tools": list(principal.allowed_tools),
        },
    }


@router.get("/ServiceProviderConfig")
def scim_service_provider_config() -> dict[str, Any]:
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "patch": {"supported": True},
        "bulk": {"supported": False},
        "filter": {"supported": False},
        "changePassword": {"supported": False},
        "sort": {"supported": False},
        "etag": {"supported": False},
        "authenticationSchemes": [
            {
                "type": "oauthbearertoken",
                "name": "OAuth Bearer Token",
                "description": "Use AegisAI auth headers or OIDC bearer.",
            }
        ],
    }


@router.get("/Users")
def list_users(request: Request, startIndex: int = 1, count: int = 100) -> dict[str, Any]:
    service = _service(request)
    principals = service.list_principals()
    resources = [_user_resource(p) for p in principals]
    page = resources[startIndex - 1 : startIndex - 1 + count]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resources),
        "startIndex": startIndex,
        "itemsPerPage": len(page),
        "Resources": page,
    }


@router.get("/Users/{user_id}")
def get_user(user_id: str, request: Request) -> dict[str, Any]:
    principal = _service(request).principal(user_id)
    if principal is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_resource(principal)


@router.post("/Users", status_code=201)
def create_user(body: ScimUser, request: Request) -> dict[str, Any]:
    service = _service(request)
    tenant_id = body.tenant_id or request.headers.get("X-AegisAI-Tenant", "acme")
    principal = Principal(
        principal_id=body.userName,
        tenant_id=tenant_id,
        roles=tuple(body.roles) or ("workflow_owner",),
        allowed_tools=tuple(body.allowed_tools),
    )
    service.upsert_principal(principal)
    return _user_resource(principal)


@router.put("/Users/{user_id}")
def replace_user(user_id: str, body: ScimUser, request: Request) -> dict[str, Any]:
    service = _service(request)
    if service.principal(user_id) is None and body.userName != user_id:
        raise HTTPException(status_code=404, detail="User not found")
    tenant_id = body.tenant_id or request.headers.get("X-AegisAI-Tenant", "acme")
    principal = Principal(
        principal_id=user_id,
        tenant_id=tenant_id,
        roles=tuple(body.roles) or ("workflow_owner",),
        allowed_tools=tuple(body.allowed_tools),
    )
    if not body.active:
        service.deactivate_principal(user_id)
        return _user_resource(principal, active=False)
    service.upsert_principal(principal)
    return _user_resource(principal)


@router.patch("/Users/{user_id}")
def patch_user(user_id: str, request: Request, body: dict[str, Any]) -> dict[str, Any]:
    service = _service(request)
    principal = service.principal(user_id)
    if principal is None:
        raise HTTPException(status_code=404, detail="User not found")
    ops = body.get("Operations") or []
    active = True
    roles = list(principal.roles)
    tools = list(principal.allowed_tools)
    tenant_id = principal.tenant_id
    for op in ops:
        path = (op.get("path") or "").lower()
        value = op.get("value")
        if path == "active" and value is False:
            active = False
        if path in {"roles", "urn:aegisai:params:scim:schemas:extension:tenant:2.0:user.roles"} and isinstance(value, list):
            roles = [str(v.get("value") if isinstance(v, dict) else v) for v in value]
        if "allowed_tools" in path and isinstance(value, list):
            tools = [str(v) for v in value]
        if "tenant" in path and isinstance(value, str):
            tenant_id = value
    if not active:
        service.deactivate_principal(user_id)
        return _user_resource(principal, active=False)
    updated = Principal(
        principal_id=user_id,
        tenant_id=tenant_id,
        roles=tuple(roles),
        allowed_tools=tuple(tools),
    )
    service.upsert_principal(updated)
    return _user_resource(updated)


@router.delete("/Users/{user_id}", status_code=204, response_class=Response)
def delete_user(user_id: str, request: Request) -> Response:
    if not _service(request).deactivate_principal(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=204)


@router.get("/Groups")
def list_groups(request: Request) -> dict[str, Any]:
    groups = _service(request).list_groups()
    resources = [
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": g["id"],
            "displayName": g["displayName"],
            "members": g.get("members", []),
            "meta": {"resourceType": "Group"},
        }
        for g in groups
    ]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resources),
        "Resources": resources,
    }


@router.post("/Groups", status_code=201)
def create_group(body: ScimGroup, request: Request) -> dict[str, Any]:
    group_id = str(uuid.uuid4())
    group = _service(request).upsert_group(
        group_id=group_id,
        display_name=body.displayName,
        members=body.members,
        roles=body.roles,
    )
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "id": group["id"],
        "displayName": group["displayName"],
        "members": group.get("members", []),
    }


@router.put("/Groups/{group_id}")
def replace_group(group_id: str, body: ScimGroup, request: Request) -> dict[str, Any]:
    group = _service(request).upsert_group(
        group_id=group_id,
        display_name=body.displayName,
        members=body.members,
        roles=body.roles,
    )
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "id": group["id"],
        "displayName": group["displayName"],
        "members": group.get("members", []),
    }


@router.delete("/Groups/{group_id}", status_code=204, response_class=Response)
def delete_group(group_id: str, request: Request) -> Response:
    if not _service(request).delete_group(group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    return Response(status_code=204)
