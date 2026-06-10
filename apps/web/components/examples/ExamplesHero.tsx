"use client";

import { ArrowLeft, FlaskConical, Play, Search } from "lucide-react";

type ExamplesHeroProps = {
  isRunningUseCases: boolean;
  onRunScenario: () => void;
  onRunAll: () => void;
  onCheckEvidence: () => void;
  onBackToControlPlane: () => void;
};

export function ExamplesHero({
  isRunningUseCases,
  onRunScenario,
  onRunAll,
  onCheckEvidence,
  onBackToControlPlane
}: ExamplesHeroProps) {
  return (
    <section className="examples-hero">
      <div className="examples-hero-copy">
        <p className="eyebrow">Proof workloads · Reference agents</p>
        <h1>See how the control plane governs real agent scenarios</h1>
        <p>
          These multi-agent workflows are not the product enterprises buy — they prove that
          refunds, credits, and data operations run through policy, evidence, HITL, and audit
          before anything side-effects.
        </p>
      </div>
      <div className="examples-hero-actions">
        <button type="button" className="btn-primary btn-lg" onClick={onRunScenario}>
          <Play size={18} />
          Run selected scenario
        </button>
        <button type="button" className="btn-secondary" onClick={onRunAll} disabled={isRunningUseCases}>
          <FlaskConical size={18} />
          {isRunningUseCases ? "Running all…" : "Run all scenarios"}
        </button>
        <button type="button" className="btn-secondary" onClick={onCheckEvidence}>
          <Search size={18} />
          Retrieve evidence
        </button>
        <button type="button" className="examples-back-link" onClick={onBackToControlPlane}>
          <ArrowLeft size={16} />
          Back to control plane
        </button>
      </div>
    </section>
  );
}
