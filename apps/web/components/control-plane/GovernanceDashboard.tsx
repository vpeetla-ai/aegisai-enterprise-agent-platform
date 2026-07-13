"use client";

import {
  Activity,
  ArrowRight,
  Bot,
  DollarSign,
  Eye,
  Plug,
  Shield,
  Undo2,
  Users,
  Workflow
} from "lucide-react";
import { buildViolations, monitorHeroMetrics, violationCounts } from "@/lib/governance-ui";
import { safeArray } from "@/lib/api/safe";
import type {
  AgentCloudGovernPayload,
  AgentCloudMonitorPayload,
  AgentCloudPosturePayload,
  DashboardSummaryPayload
} from "@/lib/api/types";

export type DashboardModule =
  | "dashboard"
  | "monitor"
  | "agents"
  | "governance"
  | "gateway"
  | "llm-plane"
  | "hitl"
  | "finops"
  | "incidents"
  | "orchestrators"
  | "onboard";

const TILE_META: Record<
  string,
  { icon: typeof Bot; accent: string; module?: DashboardModule }
> = {
  agents: { icon: Bot, accent: "blue", module: "monitor" },
  token_cost: { icon: DollarSign, accent: "green", module: "finops" },
  gateway: { icon: Plug, accent: "indigo", module: "gateway" },
  hitl: { icon: Users, accent: "violet", module: "hitl" },
  risk: { icon: Shield, accent: "red", module: "governance" },
  freezes: { icon: Activity, accent: "amber", module: "incidents" },
  executions: { icon: Workflow, accent: "cyan", module: "governance" },
  orchestrators: { icon: Workflow, accent: "slate", module: "orchestrators" }
};

const PILLARS = [
  {
    id: "monitor",
    title: "Monitor",
    subtitle: "See agents in action",
    icon: Eye,
    module: "monitor" as DashboardModule
  },
  {
    id: "govern",
    title: "Govern",
    subtitle: "Zero-trust runtime controls",
    icon: Shield,
    module: "governance" as DashboardModule
  },
  {
    id: "remediate",
    title: "Remediate",
    subtitle: "Undo mistakes in minutes",
    icon: Undo2,
    module: "governance" as DashboardModule
  }
];

type GovernanceDashboardProps = {
  summary: DashboardSummaryPayload | null;
  monitor: AgentCloudMonitorPayload | null;
  govern: AgentCloudGovernPayload | null;
  posture: AgentCloudPosturePayload | null;
  isLoading: boolean;
  onRefresh: () => void;
  onSelectModule: (module: DashboardModule) => void;
  apiHealthy: boolean;
};

function resolveModule(tileModule: string): DashboardModule {
  if (tileModule === "agents") return "monitor";
  return tileModule as DashboardModule;
}

export function GovernanceDashboard({
  summary,
  monitor,
  govern,
  posture,
  isLoading,
  onRefresh,
  onSelectModule,
  apiHealthy
}: GovernanceDashboardProps) {
  const tiles = safeArray(summary?.tiles);
  const hero = monitorHeroMetrics(summary, monitor, govern, { apiHealthy });
  const violations = buildViolations(monitor, govern);
  const vCounts = violationCounts(violations);
  const metricsReady = apiHealthy && Boolean(summary || monitor || govern);

  return (
    <section className="aegis-dashboard" aria-label="Agent Governance Main Dashboard">
      <header className="aegis-dashboard-hero">
        <div className="aegis-dashboard-hero-copy">
          <p className="aegis-kicker">Agent Governance Control Plane</p>
          <h1>{summary?.headline ?? "Main Dashboard"}</h1>
          <p>
            Monitor agent sprawl, enforce gateway policy, and remediate reversible actions — Rubrik-style
            visibility with Guild-style control plane authority.
          </p>
          {summary ? (
            <div className="aegis-posture-ring">
              <strong>{summary.posture_score}</strong>
              <span>Posture score / 100</span>
            </div>
          ) : null}
        </div>
        <div className="aegis-dashboard-hero-actions">
          <button type="button" className="aegis-btn-secondary" onClick={onRefresh} disabled={isLoading}>
            {isLoading ? "Refreshing…" : "Refresh"}
          </button>
          <button
            type="button"
            className="aegis-btn-primary"
            onClick={() => onSelectModule("gateway")}
            disabled={!apiHealthy}
          >
            <Plug size={16} />
            Open AI Gateway
          </button>
        </div>
      </header>

      {!apiHealthy ? (
        <p className="aegis-empty" role="status">
          Governance API is waking or offline — module shortcuts stay on Dashboard until Recheck succeeds.
          Metrics show “—” instead of false zeros.
        </p>
      ) : null}

      <div className="aegis-hero-metrics on-dashboard">
        {hero.map((metric) => (
          <button
            key={metric.id}
            type="button"
            className={`aegis-hero-metric tone-${metric.tone}`}
            disabled={!apiHealthy}
            onClick={() =>
              onSelectModule(metric.id === "violations" ? "governance" : "monitor")
            }
          >
            <strong>{metric.value}</strong>
            <span>{metric.label}</span>
          </button>
        ))}
      </div>

      <div className="aegis-pillar-shortcuts">
        {PILLARS.map((pillar) => {
          const Icon = pillar.icon;
          const boardMetric = safeArray(posture?.board_metrics).find((m) =>
            pillar.id === "monitor"
              ? m.label.toLowerCase().includes("registered")
              : pillar.id === "govern"
                ? m.label.toLowerCase().includes("gateway")
                : m.label.toLowerCase().includes("undo")
          );
          return (
            <button
              key={pillar.id}
              type="button"
              className={`aegis-pillar-card pillar-${pillar.id}`}
              disabled={!apiHealthy}
              onClick={() => onSelectModule(pillar.module)}
            >
              <Icon size={22} />
              <div>
                <strong>{pillar.title}</strong>
                <span>{pillar.subtitle}</span>
                {boardMetric ? <em>{boardMetric.value} · {boardMetric.meaning}</em> : null}
              </div>
              <ArrowRight size={18} />
            </button>
          );
        })}
      </div>

      <div className="aegis-dashboard-grid">
        <div className="aegis-tile-grid">
          {tiles.length === 0 ? (
            <p className="aegis-empty">Load dashboard to see governance metrics.</p>
          ) : (
            tiles.map((tile) => {
              const meta = TILE_META[tile.id] ?? { icon: Bot, accent: "blue" };
              const Icon = meta.icon;
              const targetModule = meta.module ?? resolveModule(tile.module);
              return (
                <button
                  key={tile.id}
                  type="button"
                  className={`aegis-tile accent-${meta.accent} status-${tile.status}`}
                  disabled={!apiHealthy}
                  onClick={() => onSelectModule(targetModule)}
                >
                  <div className="aegis-tile-top">
                    <Icon size={20} />
                    <span className={`aegis-tile-status ${tile.status}`} />
                  </div>
                  <span className="aegis-tile-label">{tile.label}</span>
                  <strong className="aegis-tile-value">{tile.value}</strong>
                  <span className="aegis-tile-delta">{tile.delta}</span>
                </button>
              );
            })
          )}
        </div>

        <article className="aegis-violations-preview">
          <header>
            <div>
              <h3>Policy violations</h3>
              <p>
                {metricsReady
                  ? `${vCounts.open + vCounts.inProgress} need attention`
                  : "Unavailable until API is ready"}
              </p>
            </div>
            <button
              type="button"
              className="aegis-link-btn"
              disabled={!apiHealthy}
              onClick={() => onSelectModule("governance")}
            >
              View all <ArrowRight size={14} />
            </button>
          </header>
          <div className="aegis-violation-summary compact">
            <div className="aegis-violation-total">
              <strong>{metricsReady ? vCounts.total : "—"}</strong>
              <span>Total</span>
            </div>
            <div className="aegis-violation-breakdown">
              <span className="status-open">Open {metricsReady ? vCounts.open : "—"}</span>
              <span className="status-progress">In progress {metricsReady ? vCounts.inProgress : "—"}</span>
              <span className="status-done">Remediated {metricsReady ? vCounts.remediated : "—"}</span>
            </div>
          </div>
          <div className="aegis-table-wrap">
            <table className="aegis-table compact">
              <thead>
                <tr>
                  <th>Violation</th>
                  <th>Status</th>
                  <th>Policy</th>
                </tr>
              </thead>
              <tbody>
                {!metricsReady ? (
                  <tr>
                    <td colSpan={3}>Waiting for governance API…</td>
                  </tr>
                ) : violations.length === 0 ? (
                  <tr>
                    <td colSpan={3}>No open violations in the current sample.</td>
                  </tr>
                ) : (
                  violations.slice(0, 5).map((v) => (
                    <tr key={v.id} className={`row-${v.status}`}>
                      <td>{v.violation}</td>
                      <td>
                        <span className={`aegis-status-pill ${v.status}`}>
                          {v.status === "in_progress" ? "In progress" : v.status}
                        </span>
                      </td>
                      <td>{v.policy}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>
      </div>

      {summary ? (
        <div className="aegis-quick-actions">
          {safeArray(summary.quick_actions).map((action) => (
            <button
              key={action.id}
              type="button"
              className="aegis-quick-chip"
              disabled={!apiHealthy}
              onClick={() => onSelectModule(resolveModule(action.module))}
            >
              {action.label}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
