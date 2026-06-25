"use client";

import { Calendar, Play, Radio } from "lucide-react";
import { useState } from "react";
import { safeArray } from "@/lib/api/safe";
import type { OrchestratorRegistryPayload, OrchestratorRunPayload } from "@/lib/api/types";

type OrchestratorsPanelProps = {
  registry: OrchestratorRegistryPayload | null;
  contentRuns: OrchestratorRunPayload | null;
  stockRuns: OrchestratorRunPayload | null;
  websiteRuns: OrchestratorRunPayload | null;
  isLoading: boolean;
  onRefresh: () => void;
  onRunContent: () => void;
  onRunStock: () => void;
  onRunWebsite: (requirement?: string) => void;
};

function runHandler(
  orchestratorId: string,
  handlers: {
    onRunContent: () => void;
    onRunStock: () => void;
    onRunWebsite: (requirement?: string) => void;
    websiteRequirement: string;
  }
) {
  if (orchestratorId.includes("content")) return handlers.onRunContent;
  if (orchestratorId.includes("stock")) return handlers.onRunStock;
  if (orchestratorId.includes("website")) {
    return () =>
      handlers.onRunWebsite(
        handlers.websiteRequirement.trim() || undefined
      );
  }
  return undefined;
}

function runLabel(orchestratorId: string): string {
  if (orchestratorId.includes("content")) return "Run pipeline";
  if (orchestratorId.includes("stock")) return "Run briefing";
  return "Run build";
}

export function OrchestratorsPanel({
  registry,
  contentRuns,
  stockRuns,
  websiteRuns,
  isLoading,
  onRefresh,
  onRunContent,
  onRunStock,
  onRunWebsite
}: OrchestratorsPanelProps) {
  const [websiteRequirement, setWebsiteRequirement] = useState(
    "Build a marketing site with dashboard, monitor, AI gateway, and orchestrator views."
  );
  const orchestrators = safeArray(registry?.orchestrators);

  return (
    <section className="panel orchestrators-panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Managed orchestrators</p>
          <h2>Onboarded multi-agent pipelines governed by this control plane</h2>
        </div>
        <button type="button" className="btn-secondary" onClick={onRefresh} disabled={isLoading}>
          Refresh
        </button>
      </div>

      <div className="orchestrator-cards">
        {orchestrators.map((orch) => {
          const handler = runHandler(orch.orchestrator_id, {
            onRunContent,
            onRunStock,
            onRunWebsite,
            websiteRequirement
          });
          const isWebsite = orch.orchestrator_id.includes("website");
          return (
            <article key={orch.orchestrator_id} className="orchestrator-card">
              <header>
                <Radio size={18} />
                <div>
                  <h3>{orch.name}</h3>
                  <p className="orch-schedule">
                    <Calendar size={14} /> {orch.schedule}
                  </p>
                </div>
              </header>
              <p>{orch.description ?? orch.output}</p>
              <ul className="orch-agents">
                {safeArray(orch.agents as string[]).map((agent) => (
                  <li key={agent}>{agent}</li>
                ))}
              </ul>
              {isWebsite ? (
                <label className="orch-requirement-field">
                  <span>Build requirement</span>
                  <textarea
                    value={websiteRequirement}
                    onChange={(e) => setWebsiteRequirement(e.target.value)}
                    rows={3}
                    placeholder="Describe the website to build…"
                  />
                </label>
              ) : null}
              <div className="orch-actions">
                {handler ? (
                  <button type="button" className="btn-primary" onClick={handler} disabled={isLoading}>
                    <Play size={14} /> {runLabel(orch.orchestrator_id)}
                  </button>
                ) : null}
              </div>
              {orch.last_run ? (
                <p className="orch-last-run">
                  Last run: {(orch.last_run as { run_id: string }).run_id} ·{" "}
                  {(orch.last_run as { status: string }).status}
                </p>
              ) : null}
            </article>
          );
        })}
      </div>

      <div className="orchestrator-runs-grid">
        <RunHistory title="AI Content Pipeline runs" runs={contentRuns?.runs} />
        <RunHistory title="Stock Research runs" runs={stockRuns?.runs} />
        <RunHistory title="Website Build runs" runs={websiteRuns?.runs} />
      </div>
    </section>
  );
}

function RunHistory({
  title,
  runs
}: {
  title: string;
  runs?: Array<{ run_id: string; status: string; completed_at?: string }>;
}) {
  const items = safeArray(runs);
  return (
    <article className="orch-run-history">
      <h4>{title}</h4>
      {items.length === 0 ? (
        <p className="orch-empty">No runs yet — trigger manually or wait for schedule.</p>
      ) : (
        <ul>
          {items.slice(0, 5).map((run) => (
            <li key={run.run_id}>
              <code>{run.run_id}</code>
              <span className={`status-pill ${run.status}`}>{run.status}</span>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
