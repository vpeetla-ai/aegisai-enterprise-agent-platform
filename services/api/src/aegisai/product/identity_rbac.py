from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    principal_id: str
    tenant_id: str
    roles: tuple[str, ...]
    allowed_tools: tuple[str, ...]


@dataclass(frozen=True)
class AuthorizationResult:
    allowed: bool
    reason: str
    required: str


class IdentityRBACService:
    """Mock enterprise identity/RBAC service for reviewer and tool permissions."""

    _PRINCIPALS = {
        "approver-7": Principal(
            principal_id="approver-7",
            tenant_id="bank-demo",
            roles=("senior_domain_approver", "workflow_owner"),
            allowed_tools=("payments.issue_refund",),
        ),
        "privacy-officer-1": Principal(
            principal_id="privacy-officer-1",
            tenant_id="bank-demo",
            roles=("privacy_officer", "compliance"),
            allowed_tools=("privacy.modify_or_delete_data",),
        ),
        "execution-broker": Principal(
            principal_id="execution-broker",
            tenant_id="bank-demo",
            roles=("execution_broker",),
            allowed_tools=(
                "payments.issue_refund",
                "privacy.modify_or_delete_data",
                "infra.change_production_configuration",
            ),
        ),
        "vap-orchestrator": Principal(
            principal_id="vap-orchestrator",
            tenant_id="bank-demo",
            roles=("workflow_owner", "execution_broker"),
            allowed_tools=(
                "rag.search_policy_memory",
                "notify.slack",
                "notify.telegram",
                "notify.whatsapp",
            ),
        ),
    }

    def principal(self, principal_id: str) -> Principal | None:
        return self._PRINCIPALS.get(principal_id)

    def authorize_reviewer(
        self,
        principal_id: str,
        tenant_id: str,
        required_role: str | None,
    ) -> AuthorizationResult:
        principal = self.principal(principal_id)
        if principal is None:
            return AuthorizationResult(False, "Unknown reviewer identity.", required_role or "any_reviewer")
        if principal.tenant_id != tenant_id:
            return AuthorizationResult(False, "Reviewer belongs to a different tenant.", tenant_id)
        if required_role and required_role not in principal.roles:
            return AuthorizationResult(False, "Reviewer does not have the required approval role.", required_role)
        return AuthorizationResult(True, "Reviewer is authorized for this approval.", required_role or "any_reviewer")

    def authorize_tool(
        self,
        principal_id: str,
        tenant_id: str,
        tool_name: str,
    ) -> AuthorizationResult:
        principal = self.principal(principal_id)
        if principal is None:
            return AuthorizationResult(False, "Unknown execution identity.", tool_name)
        if principal.tenant_id != tenant_id:
            return AuthorizationResult(False, "Execution identity belongs to a different tenant.", tenant_id)
        if tool_name not in principal.allowed_tools:
            if tool_name.startswith("mcp.") and "execution_broker" in principal.roles:
                return AuthorizationResult(
                    True,
                    "Execution broker may invoke MCP tools through the governance proxy.",
                    tool_name,
                )
            return AuthorizationResult(False, "Execution identity is not allowed to run this tool.", tool_name)
        return AuthorizationResult(True, "Execution identity is authorized for this tool.", tool_name)

    def posture(self) -> dict[str, object]:
        principals = tuple(self._PRINCIPALS.values())
        return {
            "product_module": "Identity",
            "principal_count": len(principals),
            "tenant_count": len({principal.tenant_id for principal in principals}),
            "tool_grants": sum(len(principal.allowed_tools) for principal in principals),
            "principals": [
                {
                    "principal_id": principal.principal_id,
                    "tenant_id": principal.tenant_id,
                    "roles": list(principal.roles),
                    "allowed_tools": list(principal.allowed_tools),
                }
                for principal in principals
            ],
        }

    def graph(self, agents: tuple[object, ...]) -> dict[str, object]:
        """Return the enterprise blast-radius graph for agents, tools, owners, and identities."""
        principals = tuple(self._PRINCIPALS.values())
        nodes: list[dict[str, object]] = [
            {
                "id": "tenant:bank-demo",
                "label": "Bank Demo Tenant",
                "kind": "tenant",
                "risk": "medium",
                "detail": "Isolation boundary for agents, identities, tools, and audit evidence.",
            }
        ]
        edges: list[dict[str, object]] = []

        for agent in agents:
            agent_id = getattr(agent, "agent_id")
            owner = getattr(agent, "owner")
            owner_id = f"owner:{owner.lower().replace(' ', '-')}"
            nodes.extend(
                [
                    {
                        "id": f"agent:{agent_id}",
                        "label": getattr(agent, "name"),
                        "kind": "agent",
                        "risk": getattr(agent, "risk_tier"),
                        "detail": f"Autonomy L{getattr(agent, 'autonomy_level')} · {getattr(agent, 'status')}",
                    },
                    {
                        "id": owner_id,
                        "label": owner,
                        "kind": "owner",
                        "risk": "accountable",
                        "detail": getattr(agent, "business_domain"),
                    },
                ]
            )
            edges.extend(
                [
                    {"from": "tenant:bank-demo", "to": f"agent:{agent_id}", "relationship": "contains"},
                    {"from": owner_id, "to": f"agent:{agent_id}", "relationship": "owns"},
                ]
            )
            for tool in getattr(agent, "allowed_tools"):
                tool_id = f"tool:{tool}"
                nodes.append(
                    {
                        "id": tool_id,
                        "label": tool,
                        "kind": "tool",
                        "risk": "high" if tool != "rag.search_policy_memory" else "low",
                        "detail": "Side-effecting tool" if tool != "rag.search_policy_memory" else "Read-only retrieval",
                    }
                )
                edges.append({"from": f"agent:{agent_id}", "to": tool_id, "relationship": "may_request"})

        for principal in principals:
            principal_id = f"principal:{principal.principal_id}"
            nodes.append(
                {
                    "id": principal_id,
                    "label": principal.principal_id,
                    "kind": "principal",
                    "risk": "privileged" if principal.allowed_tools else "reviewer",
                    "detail": ", ".join(principal.roles),
                }
            )
            edges.append({"from": "tenant:bank-demo", "to": principal_id, "relationship": "authenticates"})
            for tool in principal.allowed_tools:
                edges.append(
                    {
                        "from": principal_id,
                        "to": f"tool:{tool}",
                        "relationship": "can_execute",
                    }
                )

        unique_nodes = {node["id"]: node for node in nodes}
        high_risk_tools = sorted(
            {
                edge["to"].replace("tool:", "")
                for edge in edges
                if edge["relationship"] in {"may_request", "can_execute"}
                and edge["to"].startswith("tool:")
                and edge["to"] != "tool:rag.search_policy_memory"
            }
        )
        return {
            "product_module": "Identity Graph",
            "headline": "Agent, owner, principal, and tool blast radius",
            "nodes": list(unique_nodes.values()),
            "edges": edges,
            "blast_radius": {
                "privileged_principals": sum(1 for principal in principals if principal.allowed_tools),
                "side_effecting_tools": len(high_risk_tools),
                "highest_risk_paths": [
                    "agent-refund -> payments.issue_refund -> execution-broker",
                    "agent-data-ops -> privacy.modify_or_delete_data -> privacy-officer-1",
                    "agent-it-ops -> infra.change_production_configuration -> execution-broker",
                ],
                "recommended_controls": [
                    "Use per-agent service identities instead of shared execution identities.",
                    "Require scoped execution tokens for side-effecting tools.",
                    "Attach kill switches to every high-risk tool and tenant workflow.",
                ],
            },
        }

    def permission_matrix(self, agents: tuple[object, ...]) -> dict[str, object]:
        tools = sorted({tool for agent in agents for tool in getattr(agent, "allowed_tools")})
        rows = []
        for agent in agents:
            allowed_tools = set(getattr(agent, "allowed_tools"))
            cells = []
            for tool in tools:
                if tool not in allowed_tools:
                    level = "blocked"
                elif tool == "rag.search_policy_memory":
                    level = "read"
                elif getattr(agent, "status") != "approved":
                    level = "request_only"
                else:
                    level = "request_execute_with_gateway"
                cells.append(
                    {
                        "tool": tool,
                        "permission": level,
                        "requires_gateway": tool != "rag.search_policy_memory",
                        "requires_human_approval": tool != "rag.search_policy_memory"
                        and getattr(agent, "risk_tier") in {"high", "critical"},
                    }
                )
            rows.append(
                {
                    "agent_id": getattr(agent, "agent_id"),
                    "name": getattr(agent, "name"),
                    "owner": getattr(agent, "owner"),
                    "status": getattr(agent, "status"),
                    "risk_tier": getattr(agent, "risk_tier"),
                    "permissions": cells,
                }
            )
        return {
            "product_module": "Permission Matrix",
            "headline": "Agent-to-tool authority with request, execute, approval, and block posture.",
            "columns": tools,
            "rows": rows,
            "legend": {
                "read": "Read-only retrieval or context lookup.",
                "request_only": "Agent may request the tool but cannot execute until promoted.",
                "request_execute_with_gateway": "Agent may request and execute only through gateway controls.",
                "blocked": "Tool is outside the agent allowlist.",
            },
            "recommended_controls": [
                "Use per-agent service principals for all side-effecting tools.",
                "Require gateway execution tokens for request_execute_with_gateway cells.",
                "Review request_only cells before production promotion.",
            ],
        }
