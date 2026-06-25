"""Real deploy connectors — GitHub, Vercel, Render (env-gated)."""

from __future__ import annotations

import base64
import os
from uuid import uuid4

import httpx

from .registry import ConnectorExecutionContext, ConnectorExecutionResult


class GitHubConnector:
    connector_id = "github_connector"
    provider = "github"
    supported_tools = ("github.push_files", "github.create_pull_request")

    def __init__(self) -> None:
        self._token = os.getenv("GITHUB_TOKEN", "").strip()
        self._owner = os.getenv("GITHUB_REPO_OWNER", "").strip()
        self._repo = os.getenv("GITHUB_REPO_NAME", "").strip()
        self._base_branch = os.getenv("GITHUB_BASE_BRANCH", "main")

    def can_handle(self, tool_name: str, target_system: str, action_type: str) -> bool:
        return tool_name in self.supported_tools or target_system == "github"

    def execute(self, context: ConnectorExecutionContext) -> ConnectorExecutionResult:
        if context.dry_run or not self._token:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"github://dry-run/{uuid4()}",
                message="GitHub dry-run or GITHUB_TOKEN not configured.",
                provider=self.provider,
            )
        branch = f"aegisai/{context.case_id}"
        path = f"generated/{context.proposal_id}.md"
        content = context.idempotency_key or "AegisAI generated artifact"
        encoded = base64.b64encode(content.encode()).decode()
        url = f"https://api.github.com/repos/{self._owner}/{self._repo}/contents/{path}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
        }
        payload = {
            "message": f"chore(aegisai): {context.action_type} for {context.case_id}",
            "content": encoded,
            "branch": branch,
        }
        try:
            with httpx.Client(timeout=30) as client:
                ref = client.post(
                    f"https://api.github.com/repos/{self._owner}/{self._repo}/git/refs",
                    headers=headers,
                    json={"ref": f"refs/heads/{branch}", "sha": self._resolve_sha(client, headers)},
                )
                if ref.status_code == 422:
                    pass  # branch may already exist
                put = client.put(url, headers=headers, json=payload)
                put.raise_for_status()
                data = put.json()
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=data.get("html_url", f"github://{self._owner}/{self._repo}"),
                message=f"Committed {path} on branch {branch}",
                provider=self.provider,
            )
        except httpx.HTTPError as exc:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"github://error/{uuid4()}",
                message=f"GitHub API error: {exc}",
                provider=self.provider,
            )

    def _resolve_sha(self, client: httpx.Client, headers: dict[str, str]) -> str:
        response = client.get(
            f"https://api.github.com/repos/{self._owner}/{self._repo}/git/ref/heads/{self._base_branch}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()["object"]["sha"]


class VercelDeployConnector:
    connector_id = "vercel_deploy_connector"
    provider = "vercel"
    supported_tools = ("deploy.vercel_release",)

    def __init__(self) -> None:
        self._token = os.getenv("VERCEL_TOKEN", "").strip()
        self._project_id = os.getenv("VERCEL_PROJECT_ID", "").strip()

    def can_handle(self, tool_name: str, target_system: str, action_type: str) -> bool:
        return tool_name == "deploy.vercel_release" or target_system == "vercel"

    def execute(self, context: ConnectorExecutionContext) -> ConnectorExecutionResult:
        if context.dry_run or not self._token or not self._project_id:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"vercel://dry-run/{uuid4()}",
                message="Vercel dry-run or VERCEL_TOKEN/VERCEL_PROJECT_ID not configured.",
                provider=self.provider,
            )
        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={"Authorization": f"Bearer {self._token}"},
                    json={
                        "name": self._project_id,
                        "project": self._project_id,
                        "target": "production",
                        "meta": {"aegisai_case": context.case_id},
                    },
                )
                response.raise_for_status()
                data = response.json()
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=data.get("url", f"vercel://deploy/{uuid4()}"),
                message=f"Vercel deployment triggered (id={data.get('id', 'unknown')})",
                provider=self.provider,
            )
        except httpx.HTTPError as exc:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"vercel://error/{uuid4()}",
                message=f"Vercel API error: {exc}",
                provider=self.provider,
            )


class RenderDeployConnector:
    connector_id = "render_deploy_connector"
    provider = "render"
    supported_tools = ("deploy.render_release",)

    def __init__(self) -> None:
        self._api_key = os.getenv("RENDER_API_KEY", "").strip()
        self._service_id = os.getenv("RENDER_SERVICE_ID", "").strip()

    def can_handle(self, tool_name: str, target_system: str, action_type: str) -> bool:
        return tool_name == "deploy.render_release" or target_system == "render"

    def execute(self, context: ConnectorExecutionContext) -> ConnectorExecutionResult:
        if context.dry_run or not self._api_key or not self._service_id:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"render://dry-run/{uuid4()}",
                message="Render dry-run or RENDER_API_KEY/RENDER_SERVICE_ID not configured.",
                provider=self.provider,
            )
        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    f"https://api.render.com/v1/services/{self._service_id}/deploys",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={"clearCache": False},
                )
                response.raise_for_status()
                data = response.json()
            deploy_id = data.get("id", uuid4())
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"render://deploy/{deploy_id}",
                message=f"Render deploy triggered for service {self._service_id}",
                provider=self.provider,
            )
        except httpx.HTTPError as exc:
            return ConnectorExecutionResult(
                connector_id=self.connector_id,
                external_reference=f"render://error/{uuid4()}",
                message=f"Render API error: {exc}",
                provider=self.provider,
            )
