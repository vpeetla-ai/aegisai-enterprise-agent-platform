"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Database,
  Layers,
  RefreshCw,
  UserPlus
} from "lucide-react";
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
  source?: string;
  note?: string;
  metrics?: Record<string, unknown>;
};

type LlmPlanePanelProps = {
  agentRegistry: AgentRegistryPayload | null;
  onRefreshAgents?: () => void;
};

const TABS: Array<{ id: PlaneTab; label: string; hint: string; icon: typeof Activity }> = [
  { id: "gateway", label: "Gateway", hint: "Completions & FinOps", icon: Activity },
  { id: "cache", label: "Cache", hint: "Hit / miss", icon: Database },
  { id: "tenants", label: "Tenants", hint: "Isolation model", icon: Layers },
  { id: "registry", label: "Registry", hint: "Onboard agents", icon: UserPlus }
];

function MetricTile({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <article className="aegis-metric-tile">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <em>{hint}</em> : null}
    </article>
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
  const usingDemo =
    gateway?.source === "demo_fallback" || cache?.source === "demo_fallback";

  return (
    <section className="aegis-page aegis-llm-plane" aria-label="Model plane">
      <header className="aegis-page-header">
        <div>
          <p className="aegis-kicker">Optional · Model plane</p>
          <h2>LLM Gateway Plane metrics</h2>
          <p className="aegis-page-lead">
            Shared completions + semantic cache for apps (VAP, ACF, …). This page only{" "}
            <strong>reads ops metrics</strong> — it does not proxy chat. Tool governance stays on{" "}
            <strong>AI Gateway</strong>.
          </p>
        </div>
        <button
          type="button"
          className="aegis-btn-ghost"
          onClick={() => void refresh()}
          disabled={loading}
        >
          <RefreshCw size={16} />
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      <aside className="aegis-callout aegis-callout-info" role="note">
        <Layers size={18} />
        <div>
          <strong>Two different gateways</strong>
          <p>
            <em>AI Gateway</em> = deploy / email / refund tools. <em>Model plane</em> ={" "}
            <code>aegis-llm-gateway</code> + <code>aegis-semantic-cache</code> completion metrics.
          </p>
        </div>
      </aside>

      {usingDemo ? (
        <aside className="aegis-callout aegis-callout-warn" role="status">
          <AlertTriangle size={18} />
          <div>
            <strong>Demo sample metrics</strong>
            <p>
              Live Render URLs are not configured yet, so you are seeing illustrative numbers. For
              live data: deploy gateway + cache on Render, then set{" "}
              <code>LLM_GATEWAY_OPS_URL</code> and <code>SEMANTIC_CACHE_OPS_URL</code> on the
              AegisAI API.
            </p>
          </div>
        </aside>
      ) : null}

      <div className="aegis-segment" role="tablist" aria-label="Model plane sections">
        {TABS.map((item) => {
          const Icon = item.icon;
          const active = tab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={active}
              className={`aegis-segment-item${active ? " is-active" : ""}`}
              onClick={() => setTab(item.id)}
            >
              <Icon size={16} />
              <span>
                <strong>{item.label}</strong>
                <em>{item.hint}</em>
              </span>
            </button>
          );
        })}
      </div>

      {tab === "gateway" ? (
        <div className="aegis-card">
          <div className="aegis-card-header">
            <h3>aegis-llm-gateway</h3>
            <span className={`aegis-status-pill ${gateway?.reachable ? "remediated" : "open"}`}>
              {gateway?.source === "demo_fallback"
                ? "demo sample"
                : gateway?.reachable
                  ? "live"
                  : "unreachable"}
            </span>
          </div>
          {!gateway?.reachable && gateway?.source !== "demo_fallback" ? (
            <p className="aegis-empty">
              Unreachable{gateway?.url ? ` (${gateway.url})` : ""}. Deploy on Render or set{" "}
              <code>LLM_GATEWAY_OPS_URL</code>.
            </p>
          ) : (
            <>
              <p className="aegis-muted-line">
                Mode: <code>{String(gw.control_plane_mode ?? "—")}</code>
                {gateway?.note ? ` · ${gateway.note}` : null}
              </p>
              <div className="aegis-metric-tile-grid">
                <MetricTile label="Completions" value={Number(gw.completions ?? 0)} />
                <MetricTile label="Stub completions" value={Number(gw.stub_completions ?? 0)} />
                <MetricTile label="Cache hits" value={Number(gw.cache_hits ?? 0)} />
                <MetricTile label="Cache misses" value={Number(gw.cache_misses ?? 0)} />
                <MetricTile label="FinOps meters" value={Number(gw.finops_meters ?? 0)} />
                <MetricTile label="Budget blocks" value={Number(gw.finops_breaches_blocked ?? 0)} />
              </div>
            </>
          )}
        </div>
      ) : null}

      {tab === "cache" ? (
        <div className="aegis-card">
          <div className="aegis-card-header">
            <h3>aegis-semantic-cache</h3>
            <span className={`aegis-status-pill ${cache?.reachable ? "remediated" : "open"}`}>
              {cache?.source === "demo_fallback"
                ? "demo sample"
                : cache?.reachable
                  ? "live"
                  : "unreachable"}
            </span>
          </div>
          {!cache?.reachable && cache?.source !== "demo_fallback" ? (
            <p className="aegis-empty">
              Unreachable{cache?.url ? ` (${cache.url})` : ""}. Deploy on Render or set{" "}
              <code>SEMANTIC_CACHE_OPS_URL</code>.
            </p>
          ) : (
            <div className="aegis-metric-tile-grid">
              <MetricTile label="Hits" value={Number(ca.hits ?? 0)} />
              <MetricTile label="Misses" value={Number(ca.misses ?? 0)} />
              <MetricTile label="Entries" value={Number(ca.entries ?? 0)} />
              <MetricTile
                label="Hit rate"
                value={
                  typeof ca.hit_rate === "number"
                    ? `${Math.round(Number(ca.hit_rate) * 1000) / 10}%`
                    : String(ca.hit_rate ?? "—")
                }
              />
            </div>
          )}
        </div>
      ) : null}

      {tab === "tenants" ? (
        <div className="aegis-card">
          <h3>Logical multi-tenant isolation</h3>
          <p>
            Every completion carries <code>X-Tenant-Id</code>. Cache keys include that tenant — a
            lookup from another tenant must miss.
          </p>
          <ul className="aegis-plain-list">
            <li>
              Known consumer ids: <code>vap</code>, <code>ai-content-factory</code>,{" "}
              <code>sentinel-brief</code>, <code>domainforge-rag-peft</code>, <code>omniforge</code>
            </li>
            <li>Strict mode: budget breach → HTTP 402; FinOps down → 503</li>
            <li>Demo mode: fail-open with honest <code>/v1/posture</code></li>
          </ul>
        </div>
      ) : null}

      {tab === "registry" ? (
        <div className="aegis-llm-registry">
          <div className="aegis-card">
            <div className="aegis-card-header">
              <h3>Registered agents</h3>
              <span>{agentRegistry?.summary?.total_agents ?? agents.length} total</span>
            </div>
            {agents.length === 0 ? (
              <p className="aegis-empty">No agents yet — use the form below to register one.</p>
            ) : (
              <div className="aegis-table-wrap">
                <table className="aegis-table compact">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Status</th>
                      <th>Risk</th>
                      <th>Model</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agents.slice(0, 12).map((agent) => (
                      <tr key={agent.agent_id}>
                        <td>
                          <strong>{agent.name}</strong>
                          <br />
                          <code>{agent.agent_id}</code>
                        </td>
                        <td>
                          <span className="aegis-status-pill in_progress">{agent.status}</span>
                        </td>
                        <td>{agent.risk_tier}</td>
                        <td>{agent.model_provider}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {agents.length > 0 ? (
              <p className="aegis-muted-line">
                <CheckCircle2 size={14} /> These rows come from real{" "}
                <code>POST /api/agent-registry/lifecycle</code> entries.
              </p>
            ) : null}
          </div>
          <AgentOnboardingWizard onComplete={() => void onRefreshAgents?.()} />
        </div>
      ) : null}
    </section>
  );
}
