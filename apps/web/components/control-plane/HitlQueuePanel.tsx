"use client";

import { CheckCircle2, RefreshCw, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { requestJson } from "@/lib/api/client";
import { safeArray } from "@/lib/api/safe";
import type { HitlQueuePayload, HitlQueueTask } from "@/lib/api/types";

type HitlQueuePanelProps = {
  apiHealthy: boolean;
};

export function HitlQueuePanel({ apiHealthy }: HitlQueuePanelProps) {
  const [queue, setQueue] = useState<HitlQueuePayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [actingId, setActingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    const res = await requestJson<HitlQueuePayload>("/api/hitl/queue?tenant_id=bank-demo&status=pending");
    setQueue(res.payload);
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const act = async (task: HitlQueueTask, action: "approve" | "reject") => {
    if (!task.case_id || !task.proposal_id) {
      setMessage("Task is missing case/proposal ids.");
      return;
    }
    setActingId(task.approval_task_id);
    setMessage(null);
    const res = await requestJson<{ status?: string; execution_token?: string; action?: string }>(
      "/api/control-plane/reviewer-action",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-AegisAI-Principal": "control-plane-admin",
          "X-AegisAI-Roles": "reviewer,admin"
        },
        body: JSON.stringify({
          tenant_id: task.tenant_id || "bank-demo",
          case_id: task.case_id,
          proposal_id: task.proposal_id,
          reviewer_id: "control-plane-admin",
          action,
          reason:
            action === "approve"
              ? "Approved from HITL queue in Control Room"
              : "Rejected from HITL queue in Control Room"
        })
      }
    );
    setActingId(null);
    if (res.payload?.status === "recorded") {
      setMessage(
        action === "approve"
          ? `Approved${res.payload.execution_token ? " · execution token issued" : ""}`
          : "Rejected — tool call will not execute"
      );
      await refresh();
    } else {
      setMessage("Reviewer action failed — check API health and roles.");
    }
  };

  const tasks = safeArray(queue?.tasks);

  return (
    <section className="aegis-page aegis-hitl-queue" aria-label="HITL approval queue">
      <header className="aegis-page-header">
        <div>
          <p className="aegis-kicker">Step 4 · Human gate</p>
          <h2>HITL approval queue</h2>
          <p className="aegis-page-lead">
            Agent tool calls that need a human land here. Approve to issue an execution token, or
            reject to block the side effect — with an audit trail either way.
          </p>
        </div>
        <button type="button" className="aegis-btn-ghost" onClick={() => void refresh()} disabled={loading}>
          <RefreshCw size={16} />
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      <div className="aegis-metric-tile-grid" style={{ marginBottom: 16 }}>
        <article className="aegis-metric-tile">
          <span>Pending</span>
          <strong>{queue?.pending_count ?? tasks.length}</strong>
        </article>
        <article className="aegis-metric-tile">
          <span>Showing</span>
          <strong>{tasks.length}</strong>
        </article>
      </div>

      {message ? (
        <p className="aegis-callout aegis-callout-info" role="status">
          {message}
        </p>
      ) : null}

      {!apiHealthy ? (
        <p className="aegis-empty">API offline — use Recheck API in the header.</p>
      ) : null}

      {tasks.length === 0 ? (
        <div className="aegis-try-placeholder">
          No pending approvals. Run a sample tool intercept on AI Gateway (deploy tools always need a
          human) or run Website Build / Content / Stock notify paths.
        </div>
      ) : (
        <ul className="aegis-hitl-list">
          {tasks.map((task) => (
            <li key={task.approval_task_id} className="aegis-card aegis-hitl-card">
              <div className="aegis-hitl-card-main">
                <strong>{task.action_type || "Tool action"}</strong>
                <span>
                  Agent <code>{task.agent_id || "—"}</code> → <code>{task.target_system || "—"}</code>
                </span>
                <span>
                  Role <em>{task.assigned_role}</em> · due {task.due_at || "—"}
                </span>
                <span className="aegis-muted-line">
                  case <code>{task.case_id}</code> · proposal <code>{task.proposal_id}</code>
                </span>
              </div>
              <div className="aegis-hitl-card-actions">
                <button
                  type="button"
                  className="aegis-btn-primary"
                  disabled={!apiHealthy || actingId === task.approval_task_id}
                  onClick={() => void act(task, "approve")}
                >
                  <CheckCircle2 size={16} />
                  Approve
                </button>
                <button
                  type="button"
                  className="aegis-btn-secondary"
                  disabled={!apiHealthy || actingId === task.approval_task_id}
                  onClick={() => void act(task, "reject")}
                >
                  <XCircle size={16} />
                  Reject
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
