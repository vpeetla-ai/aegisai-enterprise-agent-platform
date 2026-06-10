import { Network } from "lucide-react";
import { safeArray, safeNumber } from "@/lib/api/safe";
import { platformCommandModules } from "@/lib/controlPlaneData";
import type { GovernanceMetricsPayload, PlatformPosturePayload } from "@/lib/api/types";

type EnterpriseValuePanelProps = {
  platformPostureResult: PlatformPosturePayload | null;
  governanceMetrics?: GovernanceMetricsPayload | null;
};

export function EnterpriseValuePanel({
  platformPostureResult,
  governanceMetrics
}: EnterpriseValuePanelProps) {
  return (
    <section className="panel test-results-panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">What Enterprises Buy</p>
          <h2>A control plane above any agent framework, not just another agent demo</h2>
        </div>
        <Network size={18} />
      </div>
      <div className="module-grid">
        {platformCommandModules.map((module) => (
          <article className="packet-item" key={module.label}>
            <span>{module.label}</span>
            <strong>{module.headline}</strong>
            <p>{module.detail}</p>
          </article>
        ))}
      </div>
      {platformPostureResult || governanceMetrics ? (
        <>
          {governanceMetrics &&
          typeof governanceMetrics.gateway_coverage_pct === "number" ? (
            <div className="decision-preview execution-result north-star-inline">
              <div>
                <span>Gateway coverage (primary KPI)</span>
                <strong>
                  {safeNumber(governanceMetrics.gateway_coverage_pct).toFixed(0)}%
                </strong>
              </div>
              <p>{governanceMetrics.headline ?? "Gateway coverage metric"}</p>
            </div>
          ) : null}
          {platformPostureResult ? (
          <div className="decision-preview execution-result">
            <div>
              <span>Inventory posture (secondary)</span>
              <strong>{platformPostureResult.posture_score}/100</strong>
            </div>
            <p>{platformPostureResult.headline}</p>
            <div className="simulator-explain">
              <span>Executive summary</span>
              <p>{platformPostureResult.executive_summary}</p>
            </div>
          </div>
          ) : null}
          <div className="run-summary registry-summary">
            {safeArray(
              governanceMetrics?.board_metrics ?? platformPostureResult?.board_metrics
            ).map((metric) => (
              <article key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <p>{metric.meaning}</p>
              </article>
            ))}
          </div>
          <div className="milestone-strip">
            {safeArray(
              governanceMetrics?.recommended_actions ?? platformPostureResult?.recommended_actions
            ).map((action) => (
              <span key={action}>{action}</span>
            ))}
          </div>
        </>
      ) : (
        <div className="empty-results">
          <strong>Refresh executive posture to see the buyer-facing control plane.</strong>
          <p>It summarizes agent inventory, high-risk autonomy, cost, incidents, freezes, and recommended next actions.</p>
        </div>
      )}
    </section>
  );
}
