"use client";

import { safeArray } from "@/lib/api/safe";
import type { FinOpsDashboardPayload } from "@/lib/api/types";

type FinOpsPanelProps = {
  finopsResult: FinOpsDashboardPayload | null;
  onLoad: () => void;
};

export function FinOpsPanel({ finopsResult, onLoad }: FinOpsPanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h3>FinOps — Agent Cost & Anomalies</h3>
        <button type="button" onClick={onLoad}>
          Show FinOps posture
        </button>
      </div>
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
