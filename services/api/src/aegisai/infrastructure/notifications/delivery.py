"""Unified delivery for orchestrator outputs — Slack webhooks and Telegram bot."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx


@dataclass(frozen=True)
class DeliveryResult:
    channel: str
    delivered: bool
    detail: str
    attempts: int = 1
    dead_lettered: bool = False


@dataclass
class DeadLetterEntry:
    channel: str
    text: str
    detail: str
    attempts: int
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class NotificationDeliveryService:
    """Posts pipeline outputs to Slack and/or Telegram with retry + DLQ."""

    def __init__(self, *, max_attempts: int = 3) -> None:
        self.max_attempts = max_attempts
        self._dlq: list[DeadLetterEntry] = []

    def deliver_markdown(
        self,
        markdown: str,
        *,
        slack_webhook_env: str,
        telegram_parse_mode: str = "Markdown",
    ) -> list[DeliveryResult]:
        results: list[DeliveryResult] = []
        slack_url = os.getenv(slack_webhook_env, "").strip() or os.getenv(
            "SLACK_APPROVAL_WEBHOOK_URL", ""
        ).strip()
        if slack_url:
            results.append(self._post_slack(slack_url, markdown[:3900]))
        telegram = self._post_telegram(markdown[:3900], parse_mode=telegram_parse_mode)
        if telegram:
            results.append(telegram)
        return results

    def list_dlq(self) -> list[dict[str, Any]]:
        return [
            {
                "channel": e.channel,
                "detail": e.detail,
                "attempts": e.attempts,
                "created_at": e.created_at,
                "text_preview": e.text[:120],
            }
            for e in self._dlq
        ]

    def replay_dlq(self, index: int = 0) -> DeliveryResult:
        if index < 0 or index >= len(self._dlq):
            raise IndexError("dlq_index_out_of_range")
        entry = self._dlq.pop(index)
        if entry.channel == "slack":
            url = os.getenv("SLACK_APPROVAL_WEBHOOK_URL", "").strip()
            if not url:
                raise RuntimeError("SLACK_APPROVAL_WEBHOOK_URL unset for replay")
            return self._post_slack(url, entry.text)
        raise RuntimeError(f"unsupported_dlq_channel:{entry.channel}")

    def _post_slack(self, webhook_url: str, text: str) -> DeliveryResult:
        if os.getenv("SLACK_FORCE_FAIL", "").lower() in {"1", "true", "yes"}:
            self._dlq.append(
                DeadLetterEntry(
                    channel="slack", text=text, detail="forced_500", attempts=self.max_attempts
                )
            )
            return DeliveryResult(
                channel="slack",
                delivered=False,
                detail="forced_500",
                attempts=self.max_attempts,
                dead_lettered=True,
            )
        last_error = "unknown"
        for attempt in range(1, self.max_attempts + 1):
            try:
                with httpx.Client(timeout=15) as client:
                    response = client.post(webhook_url, json={"text": text})
                    response.raise_for_status()
                return DeliveryResult(
                    channel="slack", delivered=True, detail="Webhook accepted", attempts=attempt
                )
            except httpx.HTTPError as exc:
                last_error = str(exc)
                time.sleep(0)
        self._dlq.append(
            DeadLetterEntry(
                channel="slack", text=text, detail=last_error, attempts=self.max_attempts
            )
        )
        return DeliveryResult(
            channel="slack",
            delivered=False,
            detail=last_error,
            attempts=self.max_attempts,
            dead_lettered=True,
        )

    @staticmethod
    def _post_telegram(text: str, parse_mode: str = "Markdown") -> DeliveryResult | None:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat_id:
            return None
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                )
                response.raise_for_status()
            return DeliveryResult(channel="telegram", delivered=True, detail="Message sent")
        except httpx.HTTPError as exc:
            return DeliveryResult(channel="telegram", delivered=False, detail=str(exc))
