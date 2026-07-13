"use client";

import { useCallback, useEffect, useState } from "react";
import { Activity, Database, Layers, RefreshCw, UserPlus } from "lucide-react";
import { requestJson } from "@/lib/api/client";
import { safeArray } from "@/lib/api/safe";
import type { AgentRegistryPayload } from "@/lib/api/types";
import { AgentOnboardingWizard } from "@/components/control-plane/AgentOnboardingWizard";

type PlaneTab = "gateway" | "cache" | "tenants" | "registry";

type PlaneFetch = {
  reachable?: boolean;
  plane?: string;
  url?: string;
  error?: string;
  detail?: string;
  metrics?: Record<string, unknown>;
};

type LlmPlanePanelProps = {
  agentRegistry: AgentRegistryPayload | null;
  onRefreshAgents?: () => void;
};

function MetricCell({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function LlmPlanePanel({ agentRegistry, onRefreshAgents }: LlmPlanePanelProps) {
  const [tab, setTab] = useState<PlaneTab>("gateway");
  const [gateway, setGateway] = useState<PlaneFetch | null>(null);
  const [cache, setCache] = useState<PlaneFetch | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    const [gw, ca] = await Promise.all([
      requestJson<PlaneFetch>("/api/llm-plane/gateway-metrics"),
      requestJson<PlaneFetch>("/api/llm-plane/cache-metrics")
    ]);
    setGateway(gw.payload);
    setCache(ca.payload);
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const gw = gateway?.metrics ?? {};
  const ca = cache?.metrics ?? {};
  const agents = safeArray(agentRegistry?.agents);

  return (
    <section className="panel" aria-label="LLM gateway plane">
      <div className="panel-header">
        <div>
          <h3>LLM Gateway Plane</h3>
          <p className="aegis-page-lead">
            Federated model plane (ADR-028) — metrics from aegis-llm-gateway + aegis-semantic-cache.
            Tool intercept stays on <strong>AI Gateway</strong>. Completions are not proxied here.
          </p>
        </div>
        <button type="button" onClick={() => void refresh()} disabled={loading}>
          <RefreshCw size={16} /> {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      <div className="aegis-wizard-steps" role="tablist" style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        {(
          [
            ["gateway", "Gateway", Activity],
            ["cache", "Cache", Database],
            ["tenants", "Tenants", Layers],
            ["registry", "Registry", UserPlus]
          ] as const
        ).map(([id, label, Icon]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={tab === id ? "primary-action" : ""}
            onClick={() => setTab(id)}
          >
            <Icon size={16} /> {label}
          </button>
        ))}
      </div>

      {tab === "gateway" ? (
        <div className="aegis-card" style={{ marginTop: "1rem" }}>
          {!gateway?.reachable ? (
            <p>
              Gateway metrics unreachable
              {gateway?.url ? ` (${gateway.url})` : ""}. Set{" "}
              <code>LLM_GATEWAY_OPS_URL</code> on the API, or run aegis-llm-gateway locally on :8100.
              {gateway?.error ? ` — ${gateway.error}` : ""}
            </p>
          ) : (
            <>
              <p>
                Plane: <code>{String(gateway.plane)}</code> · mode:{" "}
                <code>{String(gw.control_plane_mode ?? "—")}</code>
              </p>
              <div className="metric-grid">
                <MetricCell label="Completions" value={Number(gw.completions ?? 0)} />
                <MetricCell label="Stub completions" value={Number(gw.stub_completions ?? 0)} />
                <MetricCell label="Cache hits (via GW)" value={Number(gw.cache_hits ?? 0)} />
                <MetricCell label="Cache misses (via GW)" value={Number(gw.cache_misses ?? 0)} />
                <MetricCell label="FinOps meters" value={Number(gw.finops_meters ?? 0)} />
                <MetricCell label="Budget blocks" value={Number(gw.finops_breaches_blocked ?? 0)} />
              </div>
            </>
          )}
        </div>
      ) : null}

      {tab === "cache" ? (
        <div className="aegis-card" style={{ marginTop: "1rem" }}>
          {!cache?.reachable ? (
            <p>
              Semantic cache metrics unreachable
              {cache?.url ? ` (${cache.url})` : ""}. Set <code>SEMANTIC_CACHE_OPS_URL</code> or run
              aegis-semantic-cache on :8101.
              {cache?.error ? ` — ${cache.error}` : ""}
            </p>
          ) : (
            <>
              <p>
                Plane: <code>{String(cache.plane)}</code>
              </p>
              <div className="metric-grid">
                <MetricCell label="Hits" value={Number(ca.hits ?? 0)} />
                <MetricCell label="Misses" value={Number(ca.misses ?? 0)} />
                <MetricCell label="Entries" value={Number(ca.entries ?? 0)} />
                <MetricCell
                  label="Hit rate"
                  value={
                    typeof ca.hit_rate === "number"
                      ? `${Math.round(ca.hit_rate * 1000) / 10}%`
                      : String(ca.hit_rate ?? "—")
                  }
                />
              </div>
            </>
          )}
        </div>
      ) : null}

      {tab === "tenants" ? (
        <div className="aegis-card" style={{ marginTop: "1rem" }}>
          <p>
            Logical multi-tenant isolation via <code>X-Tenant-Id</code> on the LLM plane (not hard
            cells). Consumer defaults: <code>vap</code>, <code>ai-content-factory</code>,{" "}
            <code>sentinel-brief</code>, <code>domainforge-rag-peft</code>, <code>omniforge</code>.
          </p>
          <ul>
            <li>Quota / budget usage surfaces through gateway FinOps meters when agent-finops is wired.</li>
            <li>Cache keys are tenant-scoped in aegis-semantic-cache.</li>
            <li>Demo mode may fail-open; strict mode fail-closed on budget breach (HTTP 402).</li>
          </ul>
        </div>
      ) : null}

      {tab === "registry" ? (
        <div style={{ marginTop: "1rem", display: "grid", gap: "1rem" }}>
          <div className="aegis-card">
            <h4>Registered agents ({agentRegistry?.summary?.total_agents ?? agents.length})</h4>
            {agents.length === 0 ? (
              <p>No agents in registry yet — use the form below to POST a real entry.</p>
            ) : (
              <ul>
                {agents.slice(0, 12).map((agent) => (
                  <li key={agent.agent_id}>
                    <strong>{agent.name}</strong> (<code>{agent.agent_id}</code>) — {agent.status} ·{" "}
                    {agent.risk_tier} · {agent.model_provider}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <AgentOnboardingWizard
            onComplete={() => {
              void onRefreshAgents?.();
            }}
          />
        </div>
      ) : null}
    </section>
  );
}
