"use client";

import {
  BarChart3,
  FileSearch,
  Lock,
  RefreshCw,
  RotateCcw,
  Shield
} from "lucide-react";
import { buildViolations, violationCounts } from "@/lib/governance-ui";
import { safeArray, safeNumber } from "@/lib/api/safe";
import type {
  AgentCloudGovernPayload,
  AgentCloudMonitorPayload,
  AgentCloudUndoablePayload,
  GovernanceMetricsPayload
} from "@/lib/api/types";

const PILLARS = [
  { id: "policies", label: "Policies", icon: Shield, desc: "OPA + built-in policy gates" },
  { id: "permissions", label: "Permissions", icon: Lock, desc: "Least-privilege tool matrix" },
  { id: "observability", label: "Observability", icon: BarChart3, desc: "Traces, metrics, gateway coverage" },
  { id: "audit", label: "Audit & logs", icon: FileSearch, desc: "Signed hash-chained evidence" }
] as const;

type GovernanceControlPlanePanelProps = {
  metrics: GovernanceMetricsPayload | null;
  monitor: AgentCloudMonitorPayload | null;
  govern: AgentCloudGovernPayload | null;
  undoable: AgentCloudUndoablePayload | null;
  isLoading: boolean;
  onRefresh: () => void;
  onUndo: (executionId: string) => void;
};

export function GovernanceControlPlanePanel({
  metrics,
  monitor,
  govern,
  undoable,
  isLoading,
  onRefresh,
  onUndo
}: GovernanceControlPlanePanelProps) {
  const violations = buildViolations(monitor, govern);
  const counts = violationCounts(violations);
  const controls = safeArray(govern?.zero_trust_controls);
  const integrations = safeArray(monitor?.integration_hub);
  const coverage = safeNumber(metrics?.gateway_coverage_pct ?? govern?.gateway_coverage_pct);
  const target = safeNumber(metrics?.pilot_target_pct ?? govern?.pilot_target_pct, 100);
  const actions = safeArray(undoable?.actions);

  return (
    <section className="aegis-govern aegis-page" aria-label="Governance Control Plane">
      <header className="aegis-page-header">
        <div>
          <p className="aegis-kicker">AegisAI Control Plane</p>
          <h2>{govern?.headline ?? "Keep agents under control"}</h2>
          <p className="aegis-page-lead">
            Guild-style runtime authority — policies, permissions, observability, and audit before any
            side effect executes.
          </p>
        </div>
        <button type="button" className="aegis-btn-ghost" onClick={onRefresh} disabled={isLoading}>
          <RefreshCw size={16} />
          {isLoading ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      <div className="aegis-guild-layout">
        <div className="aegis-guild-sources">
          <article>
            <span className="aegis-guild-label">Agent hub</span>
            <ul>
              <li>Refund workflow</li>
              <li>Ticket triage</li>
              <li>Data operations</li>
              <li>IT remediation</li>
            </ul>
          </article>
          <article>
            <span className="aegis-guild-label">Company agents</span>
            <ul>
              <li>AI Content Pipeline</li>
              <li>Stock Research</li>
              <li>HITL reviewer path</li>
              <li>Gateway SDK clients</li>
            </ul>
          </article>
        </div>

        <div className="aegis-guild-cp">
          <div className="aegis-guild-cp-head">
            <span className="aegis-guild-live">ACTION RECEIVED · gateway.tool_request</span>
            <strong>AEGISAI CONTROL PLANE</strong>
          </div>
          <div className="aegis-guild-pillars">
            {PILLARS.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <article key={pillar.id} className="aegis-guild-pillar">
                  <Icon size={28} />
                  <h4>{pillar.label}</h4>
                  <p>{pillar.desc}</p>
                </article>
              );
            })}
          </div>
          <div className="aegis-guild-coverage">
            <span>Gateway coverage</span>
            <strong>
              {coverage}% <em>/ {target}% pilot</em>
            </strong>
            <div className="aegis-progress">
              <div
                className="aegis-progress-fill"
                style={{ width: `${Math.min(100, (coverage / target) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="aegis-guild-integrations">
          <span className="aegis-guild-label">Integration hub</span>
          <div className="aegis-integration-grid">
            {integrations.map((name) => (
              <span key={name} className="aegis-integration-tile">
                {name}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="aegis-controls-row">
        {controls.map((control) => (
          <article key={control.control} className={`aegis-control-card status-${control.status}`}>
            <span className="aegis-control-status">{control.status}</span>
            <strong>{control.control}</strong>
            <p>{control.detail}</p>
          </article>
        ))}
      </div>

      <article className="aegis-violations-panel">
        <div className="aegis-violations-head">
          <div className="aegis-violation-total large">
            <strong>{counts.total}</strong>
            <span>Policy violations</span>
          </div>
          <div className="aegis-violation-breakdown large">
            <span className="status-open">
              <em>{counts.open}</em> Open
            </span>
            <span className="status-progress">
              <em>{counts.inProgress}</em> In progress
            </span>
            <span className="status-done">
              <em>{counts.remediated}</em> Remediated (7d)
            </span>
          </div>
        </div>

        <div className="aegis-table-wrap">
          <table className="aegis-table violations">
            <thead>
              <tr>
                <th>Violations</th>
                <th>Status</th>
                <th>Policy violated</th>
                <th>Entities affected</th>
              </tr>
            </thead>
            <tbody>
              {violations.map((v) => (
                <tr key={v.id} className={`row-${v.status}`}>
                  <td>{v.violation}</td>
                  <td>
                    <span className={`aegis-status-pill ${v.status}`}>
                      {v.status === "in_progress" ? "In progress" : v.status}
                    </span>
                  </td>
                  <td>{v.policy}</td>
                  <td>
                    <div className="aegis-entity-tags">
                      {v.entities.map((e) => (
                        <span key={`${v.id}-${e.label}`} className={`entity-${e.kind}`}>
                          {e.label}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>

      {actions.length > 0 ? (
        <article className="aegis-remediate-strip">
          <h3>Remediate · undo reversible actions</h3>
          <ul>
            {actions.map((action) => (
              <li key={String(action.execution_id)}>
                <div>
                  <strong>{action.action_type}</strong>
                  <span>{action.target_system}</span>
                  <p>{action.message}</p>
                </div>
                <button
                  type="button"
                  className="aegis-btn-secondary"
                  onClick={() => onUndo(String(action.execution_id))}
                  disabled={isLoading || action.status === "rolled_back"}
                >
                  <RotateCcw size={14} />
                  Undo
                </button>
              </li>
            ))}
          </ul>
        </article>
      ) : null}
    </section>
  );
}
