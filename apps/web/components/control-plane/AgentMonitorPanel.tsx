"use client";

import { AlertTriangle, Bot, RefreshCw, Wrench } from "lucide-react";
import {
  buildLineageFromAgents,
  buildViolations,
  monitorHeroMetrics,
  violationCounts
} from "@/lib/governance-ui";
import { safeArray } from "@/lib/api/safe";
import type {
  AgentCloudMonitorPayload,
  AgentCloudGovernPayload,
  DashboardSummaryPayload
} from "@/lib/api/types";

type AgentMonitorPanelProps = {
  summary: DashboardSummaryPayload | null;
  monitor: AgentCloudMonitorPayload | null;
  govern: AgentCloudGovernPayload | null;
  isLoading: boolean;
  onRefresh: () => void;
};

export function AgentMonitorPanel({
  summary,
  monitor,
  govern,
  isLoading,
  onRefresh
}: AgentMonitorPanelProps) {
  const hero = monitorHeroMetrics(summary, monitor, govern);
  const lineages = buildLineageFromAgents(safeArray(monitor?.agents));
  const activity = safeArray(monitor?.activity);
  const integrations = safeArray(monitor?.integration_hub);
  const violations = buildViolations(monitor, govern);
  const vCounts = violationCounts(violations);
  const featured = lineages[0];

  return (
    <section className="aegis-monitor aegis-page" aria-label="Agent Monitor">
      <header className="aegis-page-header">
        <div>
          <p className="aegis-kicker">Agent Monitor</p>
          <h2>{monitor?.headline ?? "See your AI agents in action"}</h2>
        </div>
        <button type="button" className="aegis-btn-ghost" onClick={onRefresh} disabled={isLoading}>
          <RefreshCw size={16} />
          {isLoading ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      <div className="aegis-hero-metrics">
        {hero.map((metric) => (
          <article key={metric.id} className={`aegis-hero-metric tone-${metric.tone}`}>
            <span className="aegis-hero-icon">
              {metric.id === "agents" ? <Bot size={22} /> : null}
              {metric.id === "risk" ? <Bot size={22} /> : null}
              {metric.id === "tools" ? <Wrench size={22} /> : null}
              {metric.id === "violations" ? <AlertTriangle size={22} /> : null}
            </span>
            <strong>{metric.value}</strong>
            <span>{metric.label}</span>
          </article>
        ))}
      </div>

      {featured ? (
        <div className="aegis-lineage-board">
          <div className="aegis-lineage-col">
            <h3>Agents ({safeArray(monitor?.agents).length})</h3>
            {lineages.map((row) => (
              <div
                key={row.agent.id}
                className={`aegis-lineage-node${row.agent.highlight ? " is-highlight" : ""}`}
              >
                <Bot size={16} />
                <div>
                  <strong>{row.agent.label}</strong>
                  {row.agent.sublabel ? (
                    <span className="aegis-risk-pill">{row.agent.sublabel}</span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>

          <div className="aegis-lineage-connector" aria-hidden />

          <div className="aegis-lineage-col">
            <h3>Identities ({lineages.length})</h3>
            {lineages.map((row) => (
              <div key={row.identity.id} className="aegis-lineage-node is-path">
                <span className="aegis-avatar">{row.identity.label[0]?.toUpperCase()}</span>
                <strong>{row.identity.label}</strong>
              </div>
            ))}
          </div>

          <div className="aegis-lineage-connector" aria-hidden />

          <div className="aegis-lineage-col">
            <h3>Applications</h3>
            {lineages.map((row) => (
              <div key={row.agent.id} className="aegis-lineage-stack">
                {row.applications.map((app) => (
                  <div
                    key={app.id}
                    className={`aegis-lineage-node compact${app.highlight ? " is-path" : ""}`}
                  >
                    <strong>{app.label}</strong>
                  </div>
                ))}
              </div>
            ))}
          </div>

          <div className="aegis-lineage-connector" aria-hidden />

          <div className="aegis-lineage-col">
            <h3>Tools used</h3>
            {lineages.map((row) => (
              <div key={row.agent.id} className="aegis-lineage-stack">
                {row.tools.map((tool) => (
                  <div
                    key={tool.id}
                    className={`aegis-lineage-node compact${tool.warning ? " is-warning" : ""}`}
                  >
                    {tool.warning ? <AlertTriangle size={14} /> : <Wrench size={14} />}
                    <strong>{tool.label}</strong>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="aegis-monitor-grid">
        <article className="aegis-card">
          <header className="aegis-card-header">
            <h3>Live activity</h3>
            <span>{activity.length} events</span>
          </header>
          <div className="aegis-table-wrap">
            <table className="aegis-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Event</th>
                  <th>Agent</th>
                  <th>Detail</th>
                </tr>
              </thead>
              <tbody>
                {activity.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="aegis-empty">
                      Refresh monitor to load activity feed.
                    </td>
                  </tr>
                ) : (
                  activity.map((item, index) => (
                    <tr key={`${item.event_type}-${index}`}>
                      <td>{item.time}</td>
                      <td>
                        <code>{item.event_type}</code>
                      </td>
                      <td>{item.agent_id ?? "—"}</td>
                      <td>{item.detail}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>

        <article className="aegis-card">
          <header className="aegis-card-header">
            <h3>Policy signals</h3>
            <span>{vCounts.open + vCounts.inProgress} active</span>
          </header>
          <div className="aegis-violation-summary">
            <div className="aegis-violation-total">
              <strong>{vCounts.total}</strong>
              <span>Policy violations</span>
            </div>
            <div className="aegis-violation-breakdown">
              <span className="status-open">Open {vCounts.open}</span>
              <span className="status-progress">In progress {vCounts.inProgress}</span>
              <span className="status-done">Remediated {vCounts.remediated}</span>
            </div>
          </div>
          <ul className="aegis-violation-list">
            {violations.slice(0, 4).map((v) => (
              <li key={v.id} className={`status-${v.status}`}>
                <p>{v.violation}</p>
                <div className="aegis-entity-tags">
                  {v.entities.map((e) => (
                    <span key={`${v.id}-${e.label}`} className={`entity-${e.kind}`}>
                      {e.label}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </article>
      </div>

      <div className="aegis-integration-hub">
        <h3>Integration hub</h3>
        <div className="aegis-integration-grid">
          {integrations.map((name) => (
            <span key={name} className="aegis-integration-tile">
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
