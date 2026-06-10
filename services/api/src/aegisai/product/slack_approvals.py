from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class SlackApprovalTask:
    task_id: str
    tenant_id: str
    case_id: str
    proposal_id: str
    channel: str
    message: str
    status: str


class SlackApprovalService:
    """Creates HITL approval tasks in Slack (webhook mock or Slack API when configured)."""

    def __init__(self, webhook_url: str | None = None, bot_token: str | None = None) -> None:
        self.webhook_url = webhook_url or os.getenv("SLACK_APPROVAL_WEBHOOK_URL", "").strip()
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN", "").strip()
        self.default_channel = os.getenv("SLACK_APPROVAL_CHANNEL", "#aegisai-hitl")
        self._tasks: dict[str, SlackApprovalTask] = {}

    @property
    def configured(self) -> bool:
        return bool(self.webhook_url or self.bot_token)

    def create_approval_task(
        self,
        *,
        tenant_id: str,
        case_id: str,
        proposal_id: str,
        summary: str,
        risk_level: str,
        approval_role: str | None,
    ) -> dict[str, object]:
        task_id = f"slack-task-{uuid4()}"
        message = (
            f":shield: *AegisAI approval required*\n"
            f"*Case:* `{case_id}` · *Proposal:* `{proposal_id}`\n"
            f"*Risk:* `{risk_level}` · *Approver role:* `{approval_role or 'workflow_owner'}`\n"
            f"*Summary:* {summary}\n"
            f"Reply with `approve {proposal_id}` or `reject {proposal_id}`."
        )
        task = SlackApprovalTask(
            task_id=task_id,
            tenant_id=tenant_id,
            case_id=case_id,
            proposal_id=proposal_id,
            channel=self.default_channel,
            message=message,
            status="pending",
        )
        self._tasks[task_id] = task
        delivery = self._deliver(message)
        return {
            "product_module": "HITL",
            "channel": "slack",
            "task_id": task_id,
            "status": task.status,
            "delivery_mode": delivery["mode"],
            "delivery_detail": delivery["detail"],
            "message_preview": message,
        }

    def handle_interaction(self, text: str, reviewer_id: str) -> dict[str, object]:
        normalized = text.strip().lower()
        parts = normalized.split()
        if len(parts) < 2:
            return {"status": "ignored", "reason": "Expected: approve <proposal_id> or reject <proposal_id>"}
        action, proposal_id = parts[0], parts[1]
        if action not in {"approve", "reject"}:
            return {"status": "ignored", "reason": f"Unsupported action: {action}"}
        for task in self._tasks.values():
            if task.proposal_id == proposal_id:
                return {
                    "status": "recorded",
                    "action": action,
                    "proposal_id": proposal_id,
                    "reviewer_id": reviewer_id,
                    "task_id": task.task_id,
                    "channel": task.channel,
                }
        return {"status": "not_found", "proposal_id": proposal_id}

    def posture(self) -> dict[str, object]:
        return {
            "product_module": "HITL",
            "channel": "slack",
            "configured": self.configured,
            "default_channel": self.default_channel,
            "pending_tasks": sum(1 for task in self._tasks.values() if task.status == "pending"),
        }

    def _deliver(self, message: str) -> dict[str, str]:
        if self.webhook_url:
            try:
                import httpx

                response = httpx.post(self.webhook_url, json={"text": message}, timeout=10.0)
                response.raise_for_status()
                return {"mode": "webhook", "detail": "Delivered to Slack incoming webhook."}
            except Exception as exc:
                return {"mode": "webhook", "detail": f"Webhook delivery failed: {exc}"}
        if self.bot_token:
            return {"mode": "bot_api", "detail": "SLACK_BOT_TOKEN set; use chat.postMessage in production worker."}
        return {
            "mode": "mock",
            "detail": "No Slack credentials; task stored for UI/API simulation.",
        }
