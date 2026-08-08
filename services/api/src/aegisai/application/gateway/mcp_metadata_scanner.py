from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass


_POISON_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I),
    re.compile(r"disregard\s+(your|the)\s+system\s+prompt", re.I),
    re.compile(r"exfiltrat", re.I),
    re.compile(r"send\s+(all|the)\s+(secrets?|api[_\s-]?keys?|credentials?)", re.I),
    re.compile(r"do\s+not\s+tell\s+the\s+user", re.I),
    re.compile(r"<\s*script\b", re.I),
    re.compile(r"[\u200b\u200c\u200d\ufeff\u202e]"),  # zero-width / bidi override
)


@dataclass(frozen=True)
class McpToolManifest:
    name: str
    description: str
    input_schema: dict[str, object] | None = None
    owner: str | None = None
    risk_class: str | None = None
    manifest_sha256: str | None = None
    mcp_server: str = "custom_enterprise_mcp"


class McpMetadataScanner:
    """Discovery-time trust gate — scan tool metadata before it reaches the model."""

    def scan(self, manifest: McpToolManifest) -> dict[str, object]:
        findings: list[str] = []
        haystacks = [
            manifest.name,
            manifest.description,
            json.dumps(manifest.input_schema or {}, sort_keys=True),
        ]
        for text in haystacks:
            for pattern in _POISON_PATTERNS:
                if pattern.search(text or ""):
                    findings.append(f"poison_pattern:{pattern.pattern[:48]}")
                    break

        if not (manifest.owner or "").strip():
            findings.append("missing_owner")
        if not (manifest.risk_class or "").strip():
            findings.append("missing_risk_class")

        expected = self.compute_digest(manifest)
        if manifest.manifest_sha256:
            if manifest.manifest_sha256.lower() != expected.lower():
                findings.append("manifest_sha256_mismatch")

        decision = "allow"
        if any(f.startswith("poison_pattern") for f in findings) or "manifest_sha256_mismatch" in findings:
            decision = "deny"
        elif "missing_owner" in findings or "missing_risk_class" in findings:
            decision = "hitl_required"

        return {
            "name": manifest.name,
            "mcp_server": manifest.mcp_server,
            "decision": decision,
            "findings": findings,
            "manifest_sha256": expected,
            "owner": manifest.owner,
            "risk_class": manifest.risk_class,
            "message": _message(decision, findings),
        }

    def scan_many(self, manifests: list[McpToolManifest]) -> dict[str, object]:
        results = [self.scan(item) for item in manifests]
        allowed = [r for r in results if r["decision"] == "allow"]
        denied = [r for r in results if r["decision"] == "deny"]
        hitl = [r for r in results if r["decision"] == "hitl_required"]
        return {
            "product_module": "MCP Discovery Trust Gate",
            "strategy": (
                "Scan MCP tool name/description/schema before discovery reaches the model; "
                "require owner + risk_class; optionally verify manifest_sha256."
            ),
            "tools_scanned": len(results),
            "allowed": allowed,
            "denied": denied,
            "hitl_required": hitl,
            "model_visible_tools": [r["name"] for r in allowed],
            "blocked_from_model": [r["name"] for r in denied + hitl],
        }

    @staticmethod
    def compute_digest(manifest: McpToolManifest) -> str:
        blob = json.dumps(
            {
                "name": manifest.name,
                "description": manifest.description,
                "input_schema": manifest.input_schema or {},
                "owner": manifest.owner,
                "risk_class": manifest.risk_class,
                "mcp_server": manifest.mcp_server,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(blob.encode()).hexdigest()


def _message(decision: str, findings: list[str]) -> str:
    if decision == "allow":
        return "Manifest passed discovery trust gate; safe to expose to the model."
    if decision == "deny":
        return f"Manifest blocked before model discovery ({', '.join(findings)})."
    return f"Manifest requires human review before discovery ({', '.join(findings)})."
