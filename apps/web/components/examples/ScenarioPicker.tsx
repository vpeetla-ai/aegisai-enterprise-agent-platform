"use client";

import { ShieldAlert } from "lucide-react";
import { requestTemplates } from "@/lib/controlPlaneData";

type ScenarioPickerProps = {
  selectedIndex: number;
  onSelect: (index: number) => void;
  onRun: (index: number) => void;
};

const scenarioMeta: Record<string, { tone: string; icon: string }> = {
  "High-value refund": { tone: "warn", icon: "refund" },
  "Low-risk fee credit": { tone: "ok", icon: "credit" },
  "Data deletion": { tone: "block", icon: "privacy" }
};

export function ScenarioPicker({ selectedIndex, onSelect, onRun }: ScenarioPickerProps) {
  return (
    <section className="scenario-picker" aria-label="Governed scenario library">
      <header>
        <p className="eyebrow">Scenarios</p>
        <h2>Pick a proof workload</h2>
        <p className="scenario-picker-lead">
          Each scenario exercises LangGraph agents, policy routing, and audit — the same path
          your design partner will run in staging.
        </p>
      </header>
      <div className="scenario-grid">
        {requestTemplates.map((template, index) => {
          const meta = scenarioMeta[template.label] ?? { tone: "neutral", icon: "default" };
          const selected = index === selectedIndex;
          return (
            <article
              key={template.label}
              className={`scenario-card scenario-card-${meta.tone}${selected ? " scenario-card-selected" : ""}`}
            >
              <button
                type="button"
                className="scenario-card-select"
                onClick={() => onSelect(index)}
              >
                <span className="scenario-label">{template.label}</span>
                <strong className="scenario-decision">{template.expectedDecision}</strong>
                <span className="scenario-meta">
                  ${template.amountUsd.toLocaleString()} · {template.classification}
                </span>
                <p>{template.impact}</p>
              </button>
              <button
                type="button"
                className="scenario-run-btn"
                onClick={() => onRun(index)}
              >
                Run
              </button>
            </article>
          );
        })}
      </div>
      <p className="scenario-footnote">
        <ShieldAlert size={14} />
        Run scenarios against FastAPI on :8000 — results appear in the workflow lab below.
      </p>
    </section>
  );
}
