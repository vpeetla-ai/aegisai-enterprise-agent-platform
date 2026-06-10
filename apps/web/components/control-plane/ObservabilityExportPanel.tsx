"use client";

import { Radio } from "lucide-react";

type ObservabilityExportPanelProps = {
  onRefreshStatus: () => void;
};

export function ObservabilityExportPanel({ onRefreshStatus }: ObservabilityExportPanelProps) {
  return (
    <section className="product-panel observability-export-panel">
      <header className="product-panel-header">
        <div>
          <p className="eyebrow">Observe · Adapters only</p>
          <h2>Export traces to Langfuse / LangSmith</h2>
          <p className="product-panel-lead">
            AegisAI remains the audit system of record. Observability tools receive exports —
            configure LANGFUSE_* or LANGSMITH_* in the API environment.
          </p>
        </div>
        <Radio size={18} />
      </header>
      <button type="button" className="btn-secondary" onClick={onRefreshStatus}>
        Refresh adapter status
      </button>
    </section>
  );
}
