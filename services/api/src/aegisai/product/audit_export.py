from __future__ import annotations

import json
from datetime import UTC, datetime

from .audit_signing import AuditPacketSigner


class AuditPacketExporter:
    """Exports case evidence as JSON or a small self-contained PDF artifact."""

    def __init__(self, signer: AuditPacketSigner | None = None) -> None:
        self.signer = signer or AuditPacketSigner()

    def build_packet(self, case_snapshot: dict[str, object]) -> dict[str, object]:
        return {
            "packet_type": "aegisai.case_audit_packet",
            "generated_at": datetime.now(UTC).isoformat(),
            "case": case_snapshot.get("case"),
            "agent_traces": case_snapshot.get("agent_traces", []),
            "action_proposals": case_snapshot.get("action_proposals", []),
            "governance_decisions": case_snapshot.get("governance_decisions", []),
            "approval_tasks": case_snapshot.get("approval_tasks", []),
            "action_executions": case_snapshot.get("action_executions", []),
            "audit_events": case_snapshot.get("audit_events", []),
            "audit_chain_valid": case_snapshot.get("audit_chain_valid", False),
        }

    def build_signed_packet(self, case_snapshot: dict[str, object]) -> dict[str, object]:
        return self.signer.sign_packet(self.build_packet(case_snapshot))

    def verify_signed_packet(self, signed_packet: dict[str, object]) -> dict[str, object]:
        return self.signer.verify_packet(signed_packet)

    def json_bytes(self, packet: dict[str, object]) -> bytes:
        return json.dumps(packet, indent=2, sort_keys=True).encode("utf-8")

    def pdf_bytes(self, packet: dict[str, object]) -> bytes:
        case = packet.get("case") or {}
        case_id = case.get("case_id", "unknown") if isinstance(case, dict) else "unknown"
        signature = packet.get("signature") if isinstance(packet.get("signature"), dict) else None
        lines = [
            "AegisAI Case Audit Packet",
            f"Case: {case_id}",
            f"Generated: {packet['generated_at']}",
            f"Audit chain valid: {packet['audit_chain_valid']}",
            f"Agent traces: {len(packet['agent_traces'])}",
            f"Proposals: {len(packet['action_proposals'])}",
            f"Decisions: {len(packet['governance_decisions'])}",
            f"Approvals: {len(packet['approval_tasks'])}",
            f"Executions: {len(packet['action_executions'])}",
            f"Audit events: {len(packet['audit_events'])}",
        ]
        if signature:
            lines.extend(
                [
                    "--- Cryptographic assurance ---",
                    f"Signing mode: {signature.get('signing_mode', 'n/a')}",
                    f"Algorithm: {signature.get('algorithm', 'n/a')}",
                    f"Key ID: {signature.get('key_id', 'n/a')}",
                    f"Signed at: {signature.get('signed_at', 'n/a')}",
                    f"Content digest: {str(signature.get('content_digest', ''))[:24]}...",
                ]
            )
        return self._simple_pdf(lines)

    @staticmethod
    def _simple_pdf(lines: list[str]) -> bytes:
        escaped_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
        text_commands = ["BT", "/F1 12 Tf", "72 760 Td"]
        for index, line in enumerate(escaped_lines):
            if index:
                text_commands.append("0 -18 Td")
            text_commands.append(f"({line}) Tj")
        text_commands.append("ET")
        stream = "\n".join(text_commands).encode("utf-8")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        ]
        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for number, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{number} 0 obj\n".encode("ascii"))
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")
        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        )
        return bytes(pdf)
