"""Incident response playbooks — post-mortem template + customer comms (Acme embed)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


POSTMORTEM_TEMPLATE = """# Post-mortem — {title}

- **Tenant:** {tenant_id}
- **Case / incident id:** {case_id}
- **Severity:** {severity}
- **Detected at:** {detected_at}
- **Resolved at:** {resolved_at}
- **Owner:** {owner}

## Summary
{summary}

## Timeline
{timeline}

## Impact
{impact}

## Root cause
{root_cause}

## What went well
- 

## What went poorly
- 

## Action items
| Action | Owner | Due |
|--------|-------|-----|
| | | |

## Evidence
- Evidence pack: `{evidence_ref}`
- Related deliveries / DLQ ids: {dlq_ids}
"""


CUSTOMER_COMMS_PLAYBOOK = """# Customer communications playbook — Acme Support Agent Embed

## When to notify
- Budget freeze for the tenant (FinOps breach → kill-switch)
- Webhook DLQ backlog > 0 for > 15 minutes
- Slack / Salesforce connector hard-fail after retries
- Strict RAG spoof-tenant / auth outage affecting answers

## First message (T+0)
Subject: Investigating issue affecting {tenant_id} support agent

We are investigating {symptom}. Customer-facing actions that require HITL remain
gated. Next update by {next_update_at}.

## Update cadence
- Sev-1: every 30 minutes until mitigated
- Sev-2: every 2 hours
- Sev-3: daily

## Resolution message
We mitigated {root_cause_one_liner}. Preventive action: {preventive}.
Evidence pack available to your security contact on request.
"""


def render_postmortem(
    *,
    tenant_id: str,
    case_id: str,
    title: str = "Failed webhook / budget breach drill",
    severity: str = "sev-2",
    summary: str = "Panel drill of webhook failure or tenant budget freeze.",
    timeline: str = "- T0 detect\n- T1 contain\n- T2 recover",
    impact: str = "Single-tenant blast radius; other tenants unaffected.",
    root_cause: str = "Forced failure for IR drill (ADR-032).",
    owner: str = "forward-deployed-engineer",
    evidence_ref: str = "",
    dlq_ids: str = "none",
    detected_at: str | None = None,
    resolved_at: str | None = None,
) -> str:
    now = datetime.now(UTC).isoformat()
    return POSTMORTEM_TEMPLATE.format(
        title=title,
        tenant_id=tenant_id,
        case_id=case_id,
        severity=severity,
        detected_at=detected_at or now,
        resolved_at=resolved_at or now,
        owner=owner,
        summary=summary,
        timeline=timeline,
        impact=impact,
        root_cause=root_cause,
        evidence_ref=evidence_ref or f"/api/evidence-packs/{tenant_id}/{case_id}",
        dlq_ids=dlq_ids,
    )


def render_customer_comms(*, tenant_id: str, symptom: str, next_update_at: str) -> str:
    return CUSTOMER_COMMS_PLAYBOOK.format(
        tenant_id=tenant_id,
        symptom=symptom,
        next_update_at=next_update_at,
        root_cause_one_liner="pending",
        preventive="pending",
    )


def incident_playbook_bundle(
    *,
    tenant_id: str,
    case_id: str,
    evidence_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "packet_type": "aegisai.incident_playbook_bundle",
        "generated_at": datetime.now(UTC).isoformat(),
        "tenant_id": tenant_id,
        "case_id": case_id,
        "post_mortem_markdown": render_postmortem(
            tenant_id=tenant_id,
            case_id=case_id,
            evidence_ref=(evidence_pack or {}).get("signature", ""),
        ),
        "customer_comms_markdown": render_customer_comms(
            tenant_id=tenant_id,
            symptom="webhook DLQ or budget breach drill",
            next_update_at=datetime.now(UTC).isoformat(),
        ),
        "evidence_pack": evidence_pack,
    }
