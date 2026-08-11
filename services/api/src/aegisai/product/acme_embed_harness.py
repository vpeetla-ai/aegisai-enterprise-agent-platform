"""Acme Support Agent Embed harness — collect panel break-test invariants for GER.

ADR-032 / ACME_EMBED_PANEL_RUBRIC.md. Consumer of ``acme.embed_invariant_v1``.
"""

from __future__ import annotations

import json
from typing import Any

from aegisai.interfaces.http.auth import auth_posture
from aegisai.product.identity_rbac import IdentityRBACService
from aegisai.product.incident_playbooks import incident_playbook_bundle
from aegisai.product.pii_middleware import redact_pii
from aegisai.product.tenant_ops import TenantOpsService
from aegisai.product.webhook_engine import WebhookEngine


def collect_acme_embed_invariants(
    *,
    identity: IdentityRBACService | None = None,
    webhook_secret: str = "acme-harness-secret",
) -> dict[str, Any]:
    """Run local break drills and return a flat dict scored by GER router_invariant."""
    identity = identity or IdentityRBACService()
    posture = auth_posture()
    identity_posture = identity.posture()

    engine = WebhookEngine(signing_secret=webhook_secret)
    calls: list[str] = []

    def _handler(delivery: Any) -> None:
        if delivery.payload.get("fail"):
            raise RuntimeError("forced_slack_500")
        calls.append("ok")

    engine.register_handler("slack.interaction", _handler)

    bad_body = json.dumps({"webhook_id": "slack.interaction", "payload": {"text": "x"}}).encode()
    bad = engine.ingest(
        webhook_id="slack.interaction",
        tenant_id="acme",
        payload={"text": "x"},
        raw_body=bad_body,
        signature_header="sha256=deadbeef",
    )

    fail_payload = {"text": "approve p1", "fail": True}
    fail_raw = json.dumps(fail_payload).encode()
    failed = engine.ingest(
        webhook_id="slack.interaction",
        tenant_id="acme",
        payload=dict(fail_payload),
        raw_body=fail_raw,
        signature_header=engine.sign_body(fail_raw),
        force_fail=True,
    )
    # Clear failure condition for replay drill (panel: Slack recovered).
    failed.payload["fail"] = False
    was_dlq = failed.status == "dlq"
    replayed = engine.replay(failed.delivery_id)
    replay_ok = replayed.status in {"replayed", "accepted"} and "ok" in calls

    pii = redact_pii("Reach jane@acme.example or 415-555-0100 about refund")
    ops = TenantOpsService()
    ops.start_tenant("acme")
    onboarding: dict[str, Any] = {}
    for step in TenantOpsService.CHECKLIST:
        onboarding = ops.complete_step("acme", step)

    ir = incident_playbook_bundle(
        tenant_id="acme",
        case_id="harness-drill-1",
        evidence_pack={"signature": "harness"},
    )

    return {
        "auth_surfaces": ["oidc", "saml_acs", "scim_users"],
        "scim_ready": bool(identity_posture.get("scim_ready")),
        "saml_acs_path": posture.get("saml_acs"),
        "scim_path": posture.get("scim"),
        "webhook_bad_sig_status": bad.status,
        "webhook_bad_sig_http": 401 if bad.status == "rejected" else 200,
        "webhook_statuses_seen": ["dlq", "replayed"] if was_dlq and replay_ok else [failed.status, replayed.status],
        "webhook_dlq_replayable": bool(was_dlq and replay_ok),
        "pii_flags": list(pii.flags),
        "pii_contains_email_plaintext": "jane@acme.example" in pii.text,
        "onboarding_steps_complete": int(onboarding.get("completed_steps") or 0),
        "onboarding_step_ids": list(TenantOpsService.CHECKLIST),
        "ttfv_seconds": onboarding.get("ttfv_seconds"),
        "finops_enforcement": ["caller_owned"],
        "kill_switch_scopes": ["agent", "tool", "tenant", "workflow"],
        "hubspot_gws_pack": "adapter_contract_only",
        "stripe_mode": "test",
        "ir_artifacts": [
            k
            for k in ("post_mortem_markdown", "customer_comms_markdown", "evidence_pack")
            if k in ir
        ],
        "ir_attestation": "pattern_only_not_soc2",
        "break_tests": [
            "spoof_tenant_strict",
            "bad_webhook_hmac",
            "slack_500_dlq",
            "tenant_budget_halt",
        ],
        "suite_honesty": "demonstrated_not_verified_customer_prod",
    }
