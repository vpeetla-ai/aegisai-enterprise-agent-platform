import unittest

from aegisai.product.audit_export import AuditPacketExporter
from aegisai.product.audit_signing import AuditPacketSigner


class AuditSigningTests(unittest.TestCase):
    def test_sign_and_verify_round_trip(self) -> None:
        signer = AuditPacketSigner(signing_mode="local_hmac", signing_key="test-signing-key")
        exporter = AuditPacketExporter(signer=signer)
        snapshot = {
            "case": {"case_id": "case-1", "tenant_id": "bank-demo"},
            "audit_chain_valid": True,
            "audit_events": [],
            "action_proposals": [],
        }
        signed = exporter.build_signed_packet(snapshot)
        verification = exporter.verify_signed_packet(signed)
        self.assertTrue(verification["valid"])
        self.assertIn("signature", signed)

    def test_tampered_packet_fails_verification(self) -> None:
        signer = AuditPacketSigner(signing_mode="local_hmac", signing_key="test-signing-key")
        exporter = AuditPacketExporter(signer=signer)
        signed = exporter.build_signed_packet(
            {"case": {"case_id": "case-1"}, "audit_chain_valid": True, "audit_events": []}
        )
        signed["audit_chain_valid"] = False
        verification = exporter.verify_signed_packet(signed)
        self.assertFalse(verification["valid"])


if __name__ == "__main__":
    unittest.main()
