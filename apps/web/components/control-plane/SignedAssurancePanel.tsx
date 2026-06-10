"use client";

import { FileCheck2, ShieldCheck, Stamp } from "lucide-react";
import type { AuditVerificationPayload, SignedAuditPayload } from "@/lib/api/types";

type SignedAssurancePanelProps = {
  signingPosture: Record<string, unknown> | null;
  signedPacket: SignedAuditPayload | null;
  verification: AuditVerificationPayload | null;
  onLoadPosture: () => void;
  onDownloadSigned: () => void;
  onVerify: () => void;
  isLoading?: boolean;
};

export function SignedAssurancePanel({
  signingPosture,
  signedPacket,
  verification,
  onLoadPosture,
  onDownloadSigned,
  onVerify,
  isLoading
}: SignedAssurancePanelProps) {
  const signature = signedPacket?.signature;

  return (
    <section className="product-panel assurance-panel" aria-label="Signed audit assurance">
      <header className="product-panel-header">
        <div>
          <p className="eyebrow">Assure · Tamper-evident audit</p>
          <h2>Signed audit packets (KMS-ready)</h2>
          <p className="product-panel-lead">
            Compliance teams can archive cryptographically signed evidence. Production uses AWS KMS;
            portfolio demos use HMAC signing with the same verification flow.
          </p>
        </div>
        <div className="assurance-actions">
          <button type="button" className="btn-secondary" onClick={onLoadPosture} disabled={isLoading}>
            Signing posture
          </button>
          <button type="button" className="btn-primary" onClick={onDownloadSigned} disabled={isLoading}>
            Download signed JSON
          </button>
          <button type="button" className="btn-secondary" onClick={onVerify} disabled={!signedPacket || isLoading}>
            Verify signature
          </button>
        </div>
      </header>

      <div className="assurance-stats">
        <article>
          <Stamp size={18} />
          <span>Mode</span>
          <strong>{String(signingPosture?.signing_mode ?? "local_hmac")}</strong>
        </article>
        <article>
          <ShieldCheck size={18} />
          <span>Algorithm</span>
          <strong>{String(signingPosture?.algorithm ?? "HMAC-SHA256")}</strong>
        </article>
        <article>
          <FileCheck2 size={18} />
          <span>Verification</span>
          <strong>{verification ? (verification.valid ? "Valid" : "Invalid") : "Not run"}</strong>
        </article>
      </div>

      {signature ? (
        <div className="assurance-signature">
          <p>
            <strong>Signed at:</strong> {signature.signed_at}
          </p>
          <p>
            <strong>Key:</strong> <code>{signature.key_id}</code>
          </p>
          <p>
            <strong>Digest:</strong>{" "}
            <code>
              {typeof signature.content_digest === "string"
                ? `${signature.content_digest.slice(0, 32)}…`
                : "—"}
            </code>
          </p>
        </div>
      ) : (
        <div className="product-panel-empty">
          <p>Run a case workflow, then download a signed audit packet for the selected case.</p>
        </div>
      )}

      {verification ? (
        <p className={verification.valid ? "assurance-valid" : "assurance-invalid"}>
          {verification.reason}
        </p>
      ) : null}
    </section>
  );
}
