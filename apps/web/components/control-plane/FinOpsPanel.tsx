"use client";

import { useCallback, useEffect, useState } from "react";
import { safeArray } from "@/lib/api/safe";
import { requestJson } from "@/lib/api/client";
import type { FinOpsDashboardPayload } from "@/lib/api/types";

type KpiFetch = {
  reachable?: boolean;
  source?: string;
  note?: string;
  metrics?: {
    cost_per_compliant_outcome?: number | null;
    compliant_outcomes?: number;
    total_cost_usd?: number;
    tenant_id?: string | null;
    kpi?: string;
  };
};

type FinOpsPanelProps = {
  finopsResult: FinOpsDashboardPayload | null;
  onLoad: () => void;
};

export function FinOpsPanel({ finopsResult, onLoad }: FinOpsPanelProps) {
  const [kpi, setKpi] = useState<KpiFetch | null>(null);

  const refreshKpi = useCallback(async () => {
    const res = await requestJson<KpiFetch>("/api/finops/kpi/cost-per-compliant-outcome");
    setKpi(res.payload);
  }, []);

  useEffect(() => {
    void refreshKpi();
  }, [refreshKpi]);

  const m = kpi?.metrics ?? {};
  const cpo =
    m.cost_per_compliant_outcome == null
      ? "—"
      : `$${Number(m.cost_per_compliant_outcome).toFixed(4)}`;

  return (
    <section className="panel">
      <div className="panel-header">
        <h3>FinOps — Agent Cost & Anomalies</h3>
        <button
          type="button"
          onClick={() => {
            onLoad();
            void refreshKpi();
          }}
        >
          Show FinOps posture
        </button>
      </div>
      <div className="metric-grid" style={{ marginBottom: 12 }}>
        <div>
          <span>Cost / compliant outcome</span>
          <strong>{cpo}</strong>
        </div>
        <div>
          <span>Compliant outcomes</span>
          <strong>{Number(m.compliant_outcomes ?? 0)}</strong>
        </div>
        <div>
          <span>Outcome spend</span>
          <strong>${Number(m.total_cost_usd ?? 0).toFixed(2)}</strong>
        </div>
      </div>
      {kpi?.source === "demo_fallback" ? (
        <p className="aegis-muted-line">{kpi.note || "Demo sample KPI — wire AGENTFINOPS_API_URL for live."}</p>
      ) : null}
      {!finopsResult ? (
        <p>Review fleet spend, per-agent cost, and anomaly recommendations from the control plane API.</p>
      ) : (
        <>
          <p>{finopsResult.executive_summary}</p>
          <div className="metric-grid">
            <div>
              <span>Total monthly cost</span>
              <strong>${finopsResult.total_monthly_cost_usd}</strong>
            </div>
            <div>
              <span>Average per agent</span>
              <strong>${finopsResult.average_cost_per_agent_usd}</strong>
            </div>
            <div>
              <span>Anomalies</span>
              <strong>{finopsResult.anomaly_count}</strong>
            </div>
            {finopsResult.roi ? (
              <>
                <div>
                  <span>Loss prevented</span>
                  <strong>${finopsResult.roi.estimated_loss_prevented_usd}</strong>
                </div>
                <div>
                  <span>Review minutes saved</span>
                  <strong>{finopsResult.roi.estimated_review_minutes_saved}</strong>
                </div>
                <div>
                  <span>Autonomy ROI score</span>
                  <strong>{finopsResult.roi.autonomy_roi_score}</strong>
                </div>
              </>
            ) : null}
          </div>
          {finopsResult.roi ? <p>{finopsResult.roi.business_value_summary}</p> : null}
          <ul>
            {safeArray(finopsResult.cost_by_agent).slice(0, 5).map((agent) => (
              <li key={agent.agent_id}>
                {agent.name} — ${agent.monthly_cost_usd}/mo ({agent.risk_tier})
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
