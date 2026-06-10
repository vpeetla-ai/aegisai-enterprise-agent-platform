"use client";

import { ShieldCheck, Target, TrendingUp, Zap } from "lucide-react";
import { safeArray, safeNumber } from "@/lib/api/safe";
import type { GovernanceMetricsPayload } from "@/lib/api/types";

type GovernanceNorthStarPanelProps = {
  metrics: GovernanceMetricsPayload | null;
  onRefresh: () => void;
  isLoading?: boolean;
  persistenceMode?: string;
  buyerMode?: boolean;
};

export function GovernanceNorthStarPanel({
  metrics,
  onRefresh,
  isLoading,
  persistenceMode,
  buyerMode = false
}: GovernanceNorthStarPanelProps) {
  const hasMetrics = metrics !== null;
  const coverage = safeNumber(metrics?.gateway_coverage_pct);
  const target = safeNumber(metrics?.pilot_target_pct, 100);
  const progress = Math.min(100, Math.round((coverage / target) * 100));

  return (
    <section className="north-star-panel" aria-label="Gateway coverage north star metric">
      <header className="north-star-header">
        <div>
          <p className="eyebrow">North star · Pilot success metric</p>
          <h2>Gateway coverage</h2>
          <p className="north-star-lead">
            % of side-effecting agent tool calls routed through the governance gateway — target{" "}
            <strong>{target}%</strong> within 90 days.
          </p>
        </div>
        <button type="button" className="btn-secondary" onClick={onRefresh} disabled={isLoading}>
          {isLoading ? "Refreshing…" : "Refresh metrics"}
        </button>
      </header>

      <div className="north-star-grid">
        <article className="north-star-hero-metric">
          <Target size={28} />
          <div className="north-star-coverage">
            <span className="north-star-value">{hasMetrics ? `${coverage.toFixed(0)}%` : "Ready"}</span>
            <span className="north-star-target">
              {hasMetrics ? `/ ${target}% pilot goal` : "run demo to generate coverage"}
            </span>
          </div>
          <div className="north-star-progress" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
            <div className="north-star-progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <p className="north-star-caption">
            Observability shows traces — this metric proves runtime authority.
          </p>
        </article>

        {metrics && !buyerMode ? (
          <>
            <article className="north-star-stat">
              <Zap size={20} />
              <span>Gateway tool calls</span>
              <strong>{metrics.gateway_tool_calls}</strong>
            </article>
            <article className="north-star-stat">
              <ShieldCheck size={20} />
              <span>Token-bound executions</span>
              <strong>{metrics.executions_with_token}</strong>
            </article>
            <article className="north-star-stat">
              <TrendingUp size={20} />
              <span>Bypass attempts blocked</span>
              <strong>{metrics.bypass_attempts_blocked}</strong>
            </article>
          </>
        ) : !metrics ? (
          <article className="north-star-empty">
            <p>Metrics refresh automatically in buyer demo.</p>
          </article>
        ) : null}
      </div>

      {persistenceMode && !buyerMode ? (
        <p className="north-star-footnote">
          Persistence: <code>{persistenceMode}</code>
          {persistenceMode !== "postgres" ? " · Set AEGISAI_DB_BACKEND=postgres for design partners" : " · Production-ready"}
        </p>
      ) : null}

      {safeArray(metrics?.recommended_actions).length && !buyerMode ? (
        <ul className="north-star-actions">
          {safeArray(metrics?.recommended_actions).map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
