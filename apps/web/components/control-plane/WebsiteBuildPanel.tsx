"use client";

import { useState } from "react";
import { Hammer, Loader2, Send } from "lucide-react";
import { requestJson } from "@/lib/api/client";

type WebsiteBuildPanelProps = {
  isLoading: boolean;
  onSubmit: (requirement: string) => void;
  lastRun?: {
    run_id: string;
    status: string;
    hitl_pending?: boolean;
    review_deploy?: { deployment_status?: string; hitl_required?: boolean };
  } | null;
};

const EXAMPLE =
  "Build a marketing site with hero, pricing, auth, and a dashboard that shows gateway coverage and orchestrator runs.";

export function WebsiteBuildPanel({
  isLoading,
  onSubmit,
  lastRun
}: WebsiteBuildPanelProps) {
  const [requirement, setRequirement] = useState(EXAMPLE);
  const [preview, setPreview] = useState<string | null>(null);

  const handlePreview = async () => {
    const { payload } = await requestJson<{ headline?: string }>("/api/platform/gateway-story");
    setPreview(payload?.headline ?? "Governed website build — all deploys pass through AI Gateway.");
  };

  return (
    <section className="aegis-card aegis-website-build" aria-label="Website build requirement">
      <header className="aegis-website-build-header">
        <Hammer size={22} />
        <div>
          <h3>Submit build requirement</h3>
          <p className="aegis-page-lead">
            On-demand LangGraph pipeline: requirements → UI design → FE → BE → review & deploy.
            Deploy tools require HITL approval before Vercel/Render execution.
          </p>
        </div>
      </header>

      <label className="orch-requirement-field">
        <span>What should we build?</span>
        <textarea
          rows={5}
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          placeholder="Describe pages, auth, integrations, design tone…"
        />
      </label>

      <div className="aegis-website-build-actions">
        <button
          type="button"
          className="aegis-btn-primary"
          disabled={isLoading || !requirement.trim()}
          onClick={() => onSubmit(requirement.trim())}
        >
          {isLoading ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
          {isLoading ? "Running pipeline…" : "Run Website Build Pipeline"}
        </button>
        <button type="button" className="aegis-btn-ghost" onClick={() => void handlePreview()}>
          Gateway context
        </button>
      </div>

      {preview ? <p className="aegis-website-preview">{preview}</p> : null}

      {lastRun ? (
        <div className="aegis-website-last-run">
          <strong>Last run:</strong> <code>{lastRun.run_id}</code>
          <span className={`aegis-status-pill ${lastRun.status}`}>{lastRun.status}</span>
          {lastRun.hitl_pending ? (
            <em>Deploy paused — approve in Governance → HITL queue</em>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
