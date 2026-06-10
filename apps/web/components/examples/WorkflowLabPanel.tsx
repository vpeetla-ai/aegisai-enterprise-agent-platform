"use client";

import { Activity, CheckCircle2, UserRound } from "lucide-react";
import { outcomePacket } from "@/lib/controlPlaneData";
import type { ExecutionPayload } from "@/lib/api/types";

type WorkflowLabPanelProps = {
  requestText: string;
  setRequestText: (value: string) => void;
  selectedTemplate: {
    label: string;
    expectedDecision: string;
    impact: string;
    classification: string;
    amountUsd: number;
  };
  onRunAgents: () => void;
  onApproveExecute: () => void;
  executionResult: ExecutionPayload | null;
};

export function WorkflowLabPanel({
  requestText,
  setRequestText,
  selectedTemplate,
  onRunAgents,
  onApproveExecute,
  executionResult
}: WorkflowLabPanelProps) {
  return (
    <section className="workflow-lab">
      <div className="workflow-lab-grid">
        <article className="workflow-lab-intake product-panel">
          <header className="product-panel-header">
            <div>
              <p className="eyebrow">Workflow lab · Step 1</p>
              <h2>Business request intake</h2>
              <p className="product-panel-lead">
                Edit the request, then run agents to see policy routing, risk, and HITL in the
                results panel.
              </p>
            </div>
            <UserRound size={20} />
          </header>
          <textarea
            className="workflow-textarea"
            value={requestText}
            onChange={(event) => setRequestText(event.target.value)}
            aria-label="Business request"
            rows={5}
          />
          <div className="workflow-meta-chips">
            <span>Tenant: bank-demo</span>
            <span>{selectedTemplate.classification}</span>
            <span>${selectedTemplate.amountUsd.toLocaleString()}</span>
            <span>{selectedTemplate.impact}</span>
          </div>
          <div className="workflow-lab-actions">
            <button type="button" className="btn-primary" onClick={onRunAgents}>
              <Activity size={16} />
              Run LangGraph agents
            </button>
            <button type="button" className="btn-secondary" onClick={onApproveExecute}>
              Approve + execute (full path)
            </button>
          </div>
          <div className="workflow-expected">
            <span>Expected routing</span>
            <strong>{selectedTemplate.expectedDecision}</strong>
          </div>
        </article>

        <article className="workflow-lab-packet product-panel">
          <header className="product-panel-header">
            <div>
              <p className="eyebrow">Decision packet</p>
              <h2>What reviewers see</h2>
            </div>
            <CheckCircle2 size={20} />
          </header>
          <ul className="decision-packet-list">
            {outcomePacket.map((item) => (
              <li key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
                <p>{item.detail}</p>
              </li>
            ))}
          </ul>
          <div className="workflow-execution-outcome">
            <span>Latest broker execution</span>
            <strong>{executionResult?.status ?? "Not executed yet"}</strong>
            <p>
              {executionResult
                ? `${executionResult.connector} · ${executionResult.external_reference ?? executionResult.message}`
                : "Use Approve + execute after HITL to prove the governed broker path."}
            </p>
          </div>
        </article>
      </div>
    </section>
  );
}
