"""Shared PII redaction for gateway tool args and audit — pattern, not SOC2 attestation."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
_CREDIT_CARD = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


@dataclass(frozen=True)
class PiiSpan:
    kind: str
    start: int
    end: int
    redaction_token: str


@dataclass(frozen=True)
class RedactionResult:
    text: str
    spans: tuple[PiiSpan, ...]
    flags: tuple[str, ...]


_COMPLIANCE_LOG: list[dict[str, object]] = []


def extract_pii(text: str) -> list[PiiSpan]:
    spans: list[PiiSpan] = []
    for match in _EMAIL.finditer(text):
        spans.append(PiiSpan("email", match.start(), match.end(), "[REDACTED_EMAIL]"))
    for match in _PHONE.finditer(text):
        spans.append(PiiSpan("phone", match.start(), match.end(), "[REDACTED_PHONE]"))
    for match in _CREDIT_CARD.finditer(text):
        spans.append(PiiSpan("payment_token", match.start(), match.end(), "[REDACTED_PAYMENT_TOKEN]"))
    spans.sort(key=lambda s: s.start)
    return spans


def redact_pii(text: str) -> RedactionResult:
    spans = extract_pii(text)
    if not spans:
        return RedactionResult(text=text, spans=(), flags=())
    # Apply from end so offsets stay valid.
    out = text
    for span in reversed(spans):
        out = out[: span.start] + span.redaction_token + out[span.end :]
    flags = tuple(dict.fromkeys(f"pii_{s.kind}_redacted" for s in spans))
    return RedactionResult(text=out, spans=tuple(spans), flags=flags)


def redact_tool_args(tool_args: dict[str, Any] | None) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Redact string values in tool args; return (redacted_args, flags)."""
    if not tool_args:
        return {}, ()
    flags: list[str] = []
    redacted: dict[str, Any] = {}
    for key, value in tool_args.items():
        if isinstance(value, str):
            result = redact_pii(value)
            redacted[key] = result.text
            flags.extend(result.flags)
        elif isinstance(value, dict):
            nested, nested_flags = redact_tool_args(value)
            redacted[key] = nested
            flags.extend(nested_flags)
        else:
            redacted[key] = value
    return redacted, tuple(dict.fromkeys(flags))


def log_compliance_event(
    *,
    purpose: str,
    tenant_id: str,
    action: str,
    flags: tuple[str, ...] = (),
    detail: str | None = None,
) -> dict[str, object]:
    """Append a compliance log event (in-memory for demo; exportable in evidence packs)."""
    event = {
        "event_type": "aegisai.compliance_log",
        "attestation": "pattern_only_not_soc2",
        "purpose": purpose,
        "tenant_id": tenant_id,
        "action": action,
        "flags": list(flags),
        "detail": detail,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    _COMPLIANCE_LOG.append(event)
    logger.info("compliance_log %s", json.dumps(event, sort_keys=True))
    return event


def compliance_log_tail(limit: int = 50) -> list[dict[str, object]]:
    return list(_COMPLIANCE_LOG[-limit:])


def reset_compliance_log_for_tests() -> None:
    _COMPLIANCE_LOG.clear()
