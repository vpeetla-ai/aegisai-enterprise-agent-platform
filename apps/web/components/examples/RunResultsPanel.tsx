"use client";

import { Activity } from "lucide-react";
import { safeArray } from "@/lib/api/safe";
import type { UseCaseRun } from "@/lib/api/types";

type RunResultsPanelProps = {
  runHistory: UseCaseRun[];
  selectedRun: UseCaseRun | undefined;
  setSelectedRunId: (id: string) => void;
};

export function RunResultsPanel({ runHistory, selectedRun, setSelectedRunId }: RunResultsPanelProps) {
  if (runHistory.length === 0) {
    return (
      <section className="run-results-panel run-results-empty product-panel">
        <Activity size={24} />
        <strong>No scenario runs yet</strong>
        <p>Run a scenario above to see decision, risk, agent traces, evidence, and LLM output here.</p>
      </section>
    );
  }

  return (
    <section className="run-results-panel product-panel" aria-label="Scenario run results">
      <header className="product-panel-header">
        <div>
          <p className="eyebrow">Live results</p>
          <h2>Agent orchestration output</h2>
          <p className="product-panel-lead">
            Decisions, risk scores, and traces from the backend — proof the control plane governs
            real runs.
          </p>
        </div>
      </header>
      <div className="run-results-layout">
        <div className="run-results-list" role="listbox" aria-label="Run history">
          {runHistory.map((run) => (
            <button
              key={run.id}
              type="button"
              role="option"
              aria-selected={run.id === selectedRun?.id}
              className={run.id === selectedRun?.id ? "run-result-row selected" : "run-result-row"}
              onClick={() => setSelectedRunId(run.id)}
            >
              <span>{run.label}</span>
              <strong>{run.payload?.decision ?? run.status}</strong>
              <small>
                {run.payload
                  ? `${run.payload.risk_level} · score ${run.payload.risk_score}`
                  : run.error ?? "Pending"}
              </small>
            </button>
          ))}
        </div>
        {selectedRun ? (
          <div className="run-results-detail">
            <div className="run-results-stats">
              <article>
                <span>Decision</span>
                <strong>{selectedRun.payload?.decision ?? selectedRun.status}</strong>
              </article>
              <article>
                <span>Risk</span>
                <strong>
                  {selectedRun.payload
                    ? `${selectedRun.payload.risk_score} / ${selectedRun.payload.risk_level}`
                    : "—"}
                </strong>
              </article>
              <article>
                <span>Reviewer</span>
                <strong>{selectedRun.payload?.approval_role ?? "None"}</strong>
              </article>
              <article>
                <span>Traces</span>
                <strong>{selectedRun.payload?.agent_trace_count ?? 0}</strong>
              </article>
            </div>
            <dl className="run-results-facts">
              <div>
                <dt>Request</dt>
                <dd>{selectedRun.requestText}</dd>
              </div>
              <div>
                <dt>Agents</dt>
                <dd>
                  {safeArray(selectedRun.payload?.agents_run).join(" → ") || "Pending"}
                </dd>
              </div>
              <div>
                <dt>Evidence</dt>
                <dd>
                  {(() => {
                    const context = safeArray(selectedRun.payload?.retrieved_context)[0];
                    return context
                      ? `${context.source_uri} (score ${context.score})`
                      : "No evidence returned";
                  })()}
                </dd>
              </div>
              <div>
                <dt>LLM</dt>
                <dd>
                  {selectedRun.payload
                    ? `${selectedRun.payload.llm.provider}/${selectedRun.payload.llm.model}: ${selectedRun.payload.llm.content}`
                    : selectedRun.error ?? "Waiting"}
                </dd>
              </div>
              <div>
                <dt>Tools</dt>
                <dd>
                  {safeArray(selectedRun.payload?.tools_available)
                    .map((t) => `${t.name}${t.approval_required ? " (approval)" : ""}`)
                    .join(" · ") || "—"}
                </dd>
              </div>
            </dl>
          </div>
        ) : null}
      </div>
    </section>
  );
}
