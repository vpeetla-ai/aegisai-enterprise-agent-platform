from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class AuditSignatureEnvelope:
    algorithm: str
    key_id: str
    signed_at: str
    content_digest: str
    signature: str
    signing_mode: str

    def as_dict(self) -> dict[str, str]:
        return {
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "signed_at": self.signed_at,
            "content_digest": self.content_digest,
            "signature": self.signature,
            "signing_mode": self.signing_mode,
        }


class AuditPacketSigner:
    """Signs audit packets for tamper-evident export (local HMAC or AWS KMS)."""

    def __init__(
        self,
        signing_mode: str | None = None,
        signing_key: str | None = None,
        kms_key_id: str | None = None,
    ) -> None:
        self.signing_mode = (signing_mode or os.getenv("AEGISAI_AUDIT_SIGNING_MODE", "local_hmac")).lower()
        self.signing_key = signing_key or os.getenv(
            "AEGISAI_AUDIT_SIGNING_KEY",
            "dev-audit-signing-key-change-in-production",
        )
        self.kms_key_id = kms_key_id or os.getenv("AEGISAI_AUDIT_KMS_KEY_ID", "")

    def sign_packet(self, packet: dict[str, object]) -> dict[str, object]:
        canonical = self._canonical_bytes(packet)
        digest = hashlib.sha256(canonical).hexdigest()
        signed_at = datetime.now(UTC).isoformat()

        if self.signing_mode == "kms" and self.kms_key_id:
            signature_b64, algorithm = self._sign_with_kms(canonical)
            mode = "aws_kms"
        else:
            signature_b64 = self._sign_hmac(canonical)
            algorithm = "HMAC-SHA256"
            mode = "local_hmac"

        envelope = AuditSignatureEnvelope(
            algorithm=algorithm,
            key_id=self.kms_key_id or "aegisai-audit-signing-key-v1",
            signed_at=signed_at,
            content_digest=digest,
            signature=signature_b64,
            signing_mode=mode,
        )
        return {
            **packet,
            "signature": envelope.as_dict(),
            "assurance": {
                "tamper_evident": True,
                "verification_endpoint": "POST /api/audit-packets/verify",
                "instructions": (
                    "Compliance teams can verify packet integrity before archival. "
                    "Production deployments should use AEGISAI_AUDIT_SIGNING_MODE=kms."
                ),
            },
        }

    def verify_packet(self, signed_packet: dict[str, object]) -> dict[str, object]:
        signature_block = signed_packet.get("signature")
        if not isinstance(signature_block, dict):
            return {
                "valid": False,
                "reason": "Missing signature block on audit packet.",
            }

        packet_body = {key: value for key, value in signed_packet.items() if key not in {"signature", "assurance"}}
        canonical = self._canonical_bytes(packet_body)
        digest = hashlib.sha256(canonical).hexdigest()
        if digest != signature_block.get("content_digest"):
            return {
                "valid": False,
                "reason": "Content digest mismatch — packet body was altered after signing.",
                "expected_digest": signature_block.get("content_digest"),
                "actual_digest": digest,
            }

        signature_b64 = str(signature_block.get("signature", ""))
        algorithm = str(signature_block.get("algorithm", ""))
        signing_mode = str(signature_block.get("signing_mode", "local_hmac"))

        if signing_mode == "aws_kms" and self.kms_key_id:
            valid = self._verify_kms(canonical, signature_b64)
        else:
            expected = self._sign_hmac(canonical)
            valid = hmac.compare_digest(expected, signature_b64)

        return {
            "valid": valid,
            "algorithm": algorithm,
            "signing_mode": signing_mode,
            "key_id": signature_block.get("key_id"),
            "signed_at": signature_block.get("signed_at"),
            "audit_chain_valid": packet_body.get("audit_chain_valid"),
            "reason": "Signature valid." if valid else "Signature verification failed.",
        }

    def posture(self) -> dict[str, object]:
        kms_configured = bool(self.kms_key_id) and self.signing_mode == "kms"
        return {
            "product_module": "Assure",
            "signing_mode": self.signing_mode if not kms_configured else "kms",
            "kms_key_configured": bool(self.kms_key_id),
            "algorithm": "AWS-KMS" if kms_configured else "HMAC-SHA256",
            "enterprise_recommendation": "Use AWS KMS (or cloud HSM) for long-term audit retention and SOC2 evidence.",
        }

    def _sign_hmac(self, payload: bytes) -> str:
        digest = hmac.new(self.signing_key.encode("utf-8"), payload, hashlib.sha256).digest()
        return base64.b64encode(digest).decode("ascii")

    def _sign_with_kms(self, payload: bytes) -> tuple[str, str]:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 required for KMS audit signing. pip install boto3") from exc

        client = boto3.client("kms")
        response = client.sign(
            KeyId=self.kms_key_id,
            Message=payload,
            MessageType="RAW",
            SigningAlgorithm="RSASSA_PSS_SHA_256",
        )
        signature = base64.b64encode(response["Signature"]).decode("ascii")
        return signature, "RSASSA_PSS_SHA_256"

    def _verify_kms(self, payload: bytes, signature_b64: str) -> bool:
        try:
            import boto3
        except ImportError:
            return False
        client = boto3.client("kms")
        response = client.verify(
            KeyId=self.kms_key_id,
            Message=payload,
            MessageType="RAW",
            Signature=base64.b64decode(signature_b64),
            SigningAlgorithm="RSASSA_PSS_SHA_256",
        )
        return bool(response.get("SignatureValid"))

    @staticmethod
    def _canonical_bytes(packet: dict[str, object]) -> bytes:
        return json.dumps(packet, sort_keys=True, separators=(",", ":")).encode("utf-8")
