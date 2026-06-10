"use client";

import { CheckCircle2, Circle, Loader2 } from "lucide-react";

export type GuidedDemoStepId =
  | "metrics"
  | "catalog"
  | "gateway"
  | "hitl"
  | "execute"
  | "audit";

export type GuidedDemoStep = {
  id: GuidedDemoStepId;
  label: string;
  detail: string;
  status: "pending" | "active" | "done" | "error";
};

type GuidedBuyerDemoProps = {
  steps: GuidedDemoStep[];
  isRunning: boolean;
  demoState?: "idle" | "preparing" | "running" | "evidence_ready" | "failed";
  timeline?: string[];
  onRun: () => void;
  onRetryStep?: (stepId: GuidedDemoStepId) => void;
  onCopyReport?: () => void;
  onCopyJsonReport?: () => void;
  onDownloadJsonReport?: () => void;
};

export function GuidedBuyerDemo({
  steps,
  isRunning,
  demoState = "idle",
  timeline = [],
  onRun,
  onRetryStep,
  onCopyReport,
  onCopyJsonReport,
  onDownloadJsonReport
}: GuidedBuyerDemoProps) {
  const stateCopy: Record<NonNullable<GuidedBuyerDemoProps["demoState"]>, string> = {
    idle: "Ready to run",
    preparing: "Preparing workflow",
    running: "Workflow in progress",
    evidence_ready: "Evidence ready",
    failed: "Workflow needs retry"
  };

  return (
    <section className="guided-demo-panel" aria-label="12-minute buyer demo">
      <header className="guided-demo-header">
        <div>
          <p className="eyebrow">Demo · Governed workflow proof</p>
          <h2>Run the agent governance path</h2>
          <p className="guided-demo-lead">
            Catalog → gateway → policy and evals → HITL → broker execution → signed audit.
            Each step proves one control an enterprise buyer needs before production rollout.
          </p>
          <p className={`guided-demo-state guided-demo-state-${demoState}`}>{stateCopy[demoState]}</p>
        </div>
        <div className="guided-demo-header-actions">
          <button type="button" className="btn-primary" onClick={onRun} disabled={isRunning}>
            {isRunning ? (
              <>
                <Loader2 size={16} className="spin" />
                Running…
              </>
            ) : (
              "Run governed workflow"
            )}
          </button>
          {onCopyReport ? (
            <button type="button" className="btn-secondary" onClick={onCopyReport}>
              Copy incident report
            </button>
          ) : null}
          {onCopyJsonReport ? (
            <button type="button" className="btn-secondary" onClick={onCopyJsonReport}>
              Copy JSON report
            </button>
          ) : null}
          {onDownloadJsonReport ? (
            <button type="button" className="btn-secondary" onClick={onDownloadJsonReport}>
              Download JSON report
            </button>
          ) : null}
        </div>
      </header>
      <ol className="guided-demo-steps">
        {steps.map((step) => (
          <li
            key={step.id}
            className={`guided-demo-step guided-demo-step-${step.status}`}
            data-status={step.status}
          >
            {step.status === "done" ? (
              <CheckCircle2 size={20} className="step-icon done" />
            ) : step.status === "active" ? (
              <Loader2 size={20} className="step-icon spin" />
            ) : step.status === "error" ? (
              <Circle size={20} className="step-icon error" />
            ) : (
              <Circle size={20} className="step-icon" />
            )}
            <div>
              <strong>{step.label}</strong>
              <p>{step.detail}</p>
              {step.status === "error" && onRetryStep ? (
                <button
                  type="button"
                  className="btn-secondary guided-demo-retry"
                  onClick={() => onRetryStep(step.id)}
                  disabled={isRunning}
                >
                  Retry step
                </button>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
      <div className="guided-demo-timeline" aria-label="Workflow timeline">
        <strong>Timeline</strong>
        <ul>
          {timeline.length > 0 ? (
            timeline.map((entry) => <li key={entry}>{entry}</li>)
          ) : (
            <li>No events yet. Run workflow to populate execution history.</li>
          )}
        </ul>
      </div>
    </section>
  );
}
