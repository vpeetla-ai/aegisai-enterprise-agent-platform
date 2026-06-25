"""Unified delivery for orchestrator outputs — Slack webhooks and Telegram bot."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class DeliveryResult:
    channel: str
    delivered: bool
    detail: str


class NotificationDeliveryService:
    """Posts pipeline outputs to Slack and/or Telegram."""

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

    @staticmethod
    def _post_slack(webhook_url: str, text: str) -> DeliveryResult:
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(webhook_url, json={"text": text})
                response.raise_for_status()
            return DeliveryResult(channel="slack", delivered=True, detail="Webhook accepted")
        except httpx.HTTPError as exc:
            return DeliveryResult(channel="slack", delivered=False, detail=str(exc))

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
