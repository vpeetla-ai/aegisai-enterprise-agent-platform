"use client";

import { RefreshCw, ShieldOff, Snowflake } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { requestJson } from "@/lib/api/client";
import { safeArray } from "@/lib/api/safe";
import type { IncidentTimelinePayload, KillSwitchPayload } from "@/lib/api/types";

type IncidentsModulePanelProps = {
  incident: IncidentTimelinePayload | null;
  apiHealthy?: boolean;
  onRefreshIncident?: () => void;
};

export function IncidentsModulePanel({
  incident,
  apiHealthy = true,
  onRefreshIncident
}: IncidentsModulePanelProps) {
  const events = safeArray(incident?.events);
  const [posture, setPosture] = useState<KillSwitchPayload | null>(null);
  const [scopeType, setScopeType] = useState("agent");
  const [scopeValue, setScopeValue] = useState("agent-fe-builder");
  const [reason, setReason] = useState("Emergency freeze from Control Room");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const refreshKill = useCallback(async () => {
    const res = await requestJson<KillSwitchPayload>("/api/kill-switches");
    setPosture(res.payload);
  }, []);

  useEffect(() => {
    void refreshKill();
  }, [refreshKill]);

  const activate = async () => {
    setBusy(true);
    setNote(null);
    const res = await requestJson<KillSwitchPayload>("/api/kill-switches", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-AegisAI-Principal": "security-admin",
        "X-AegisAI-Roles": "admin,security"
      },
      body: JSON.stringify({
        scope_type: scopeType,
        scope_value: scopeValue,
        reason,
        created_by: "security-admin"
      })
    });
    setBusy(false);
    if (res.payload?.status === "activated") {
      setNote(`Frozen ${scopeType}:${scopeValue}`);
      await refreshKill();
      onRefreshIncident?.();
    } else {
      setNote("Activate failed — check API auth.");
    }
  };

  const deactivate = async (ruleId: string) => {
    setBusy(true);
    const res = await requestJson<KillSwitchPayload>(`/api/kill-switches/${ruleId}/deactivate`, {
      method: "POST",
      headers: {
        "X-AegisAI-Principal": "security-admin",
        "X-AegisAI-Roles": "admin,security"
      }
    });
    setBusy(false);
    if (res.payload?.status === "deactivated") {
      setNote(`Unfroze ${ruleId}`);
      await refreshKill();
      onRefreshIncident?.();
    }
  };

  const rules = safeArray(posture?.rules);

  return (
    <div className="gov-module-panel aegis-incidents">
      <p className="gov-module-lead">
        {incident?.headline ?? "Freeze, investigate, remediate, unfreeze."}
      </p>

      <article className="aegis-card" style={{ marginBottom: 16 }}>
        <div className="aegis-card-header">
          <h3>Kill switch controls</h3>
          <span>{posture?.active_rule_count ?? 0} active</span>
        </div>
        <p className="aegis-muted-line">
          Freezes persist in the control-plane store and block gateway + execution paths.
        </p>
        <div className="aegis-kill-form">
          <label>
            Scope
            <select value={scopeType} onChange={(e) => setScopeType(e.target.value)}>
              <option value="agent">agent</option>
              <option value="tool">tool</option>
              <option value="tenant">tenant</option>
              <option value="workflow">workflow</option>
            </select>
          </label>
          <label>
            Value
            <input value={scopeValue} onChange={(e) => setScopeValue(e.target.value)} />
          </label>
          <label>
            Reason
            <input value={reason} onChange={(e) => setReason(e.target.value)} />
          </label>
          <button
            type="button"
            className="aegis-btn-primary"
            disabled={!apiHealthy || busy}
            onClick={() => void activate()}
          >
            <Snowflake size={16} />
            Freeze scope
          </button>
        </div>
        {note ? <p className="aegis-muted-line">{note}</p> : null}
        {rules.length ? (
          <ul className="aegis-kill-rules">
            {rules.map((rule) => (
              <li key={rule.rule_id}>
                <strong>
                  {rule.scope_type}:{rule.scope_value}
                </strong>
                <span>{rule.active ? "active" : "inactive"}</span>
                <span>{rule.reason}</span>
                {rule.active ? (
                  <button
                    type="button"
                    className="aegis-link-btn"
                    disabled={busy}
                    onClick={() => void deactivate(rule.rule_id)}
                  >
                    <ShieldOff size={14} /> Unfreeze
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="aegis-empty">No kill-switch rules yet.</p>
        )}
      </article>

      <div className="aegis-card-header" style={{ marginBottom: 8 }}>
        <h3>Incident timeline</h3>
        <button type="button" className="aegis-btn-ghost" onClick={() => onRefreshIncident?.()}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>
      <ul className="gov-incident-list">
        {events.map((event, index) => (
          <li key={`${event.event}-${index}`}>
            <span>{event.time}</span>
            <strong>{event.event}</strong>
            <p>{event.detail}</p>
          </li>
        ))}
      </ul>
      {incident?.operating_procedure ? (
        <ol className="gov-procedure">
          {safeArray(incident.operating_procedure).map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}
