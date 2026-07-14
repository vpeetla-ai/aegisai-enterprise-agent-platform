"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Database,
  Layers,
  LayoutDashboard,
  RefreshCw
} from "lucide-react";
import { requestJson } from "@/lib/api/client";
import type { AgentRegistryPayload } from "@/lib/api/types";

type PlaneTab = "overview" | "completions" | "cache" | "isolation";

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
  agentRegistry?: AgentRegistryPayload | null;
  onRefreshAgents?: () => void;
  onOpenOnboard?: () => void;
  onOpenGateway?: () => void;
};

const TABS: Array<{ id: PlaneTab; label: string; hint: string; icon: typeof Activity }> = [
  { id: "overview", label: "Overview", hint: "Cost + cache at a glance", icon: LayoutDashboard },
  { id: "completions", label: "Completions", hint: "Model call volume", icon: Activity },
  { id: "cache", label: "Semantic cache", hint: "Hit / miss / rate", icon: Database },
  { id: "isolation", label: "Tenant isolation", hint: "How keys stay separate", icon: Layers }
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

function StatusPill({ fetch }: { fetch: PlaneFetch | null }) {
  const demo = fetch?.source === "demo_fallback";
  const live = Boolean(fetch?.reachable) && !demo;
  return (
    <span className={`aegis-status-pill ${live || demo ? "remediated" : "open"}`}>
      {demo ? "demo sample" : live ? "live" : "unreachable"}
    </span>
  );
}

export function LlmPlanePanel({ onOpenOnboard, onOpenGateway }: LlmPlanePanelProps) {
  const [tab, setTab] = useState<PlaneTab>("overview");
  const [completions, setCompletions] = useState<PlaneFetch | null>(null);
  const [cache, setCache] = useState<PlaneFetch | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    const [gw, ca] = await Promise.all([
      requestJson<PlaneFetch>("/api/llm-plane/gateway-metrics"),
      requestJson<PlaneFetch>("/api/llm-plane/cache-metrics")
    ]);
    setCompletions(gw.payload);
    setCache(ca.payload);
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const gw = completions?.metrics ?? {};
  const ca = cache?.metrics ?? {};
  const usingDemo =
    completions?.source === "demo_fallback" || cache?.source === "demo_fallback";

  return (
    <section className="aegis-page aegis-llm-plane" aria-label="LLM metrics">
      <header className="aegis-page-header">
        <div>
          <p className="aegis-kicker">Optional satellite · not tool governance</p>
          <h2>LLM metrics — cost &amp; cache dashboard</h2>
          <p className="aegis-page-lead">
            Read-only ops view of shared model completions and semantic cache across apps (VAP,
            Content Factory, …). This page does <strong>not</strong> intercept tools, issue tokens,
            or approve side effects — that is{" "}
            <button type="button" className="aegis-link-btn" onClick={() => onOpenGateway?.()}>
              AI Gateway
            </button>
            .
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
          <strong>AegisAI product vs this dashboard</strong>
          <p>
            <strong>AI Gateway</strong> = govern agent <em>tools</em> (deploy / notify / refund).{" "}
            <strong>LLM metrics</strong> = optional cost/cache numbers from the shared model plane
            services. Same org, different job.
          </p>
        </div>
      </aside>

      {usingDemo ? (
        <aside className="aegis-callout aegis-callout-warn" role="status">
          <AlertTriangle size={18} />
          <div>
            <strong>Demo sample metrics</strong>
            <p>
              Live Render ops URLs are not wired, so numbers are illustrative. For live data set{" "}
              <code>LLM_GATEWAY_OPS_URL</code> and <code>SEMANTIC_CACHE_OPS_URL</code> on the AegisAI
              API (paths end in <code>/v1/ops/metrics</code>).
            </p>
          </div>
        </aside>
      ) : null}

      <div className="aegis-segment" role="tablist" aria-label="LLM metrics sections">
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

      {tab === "overview" ? (
        <div className="aegis-llm-overview-grid">
          <article className="aegis-card">
            <div className="aegis-card-header">
              <h3>Completions</h3>
              <StatusPill fetch={completions} />
            </div>
            <p className="aegis-muted-line">
              Service <code>aegis-llm-gateway</code> · mode{" "}
              <code>{String(gw.control_plane_mode ?? "—")}</code>
            </p>
            <div className="aegis-metric-tile-grid">
              <MetricTile label="Completions" value={Number(gw.completions ?? 0)} />
              <MetricTile label="FinOps meters" value={Number(gw.finops_meters ?? 0)} />
              <MetricTile label="Budget blocks" value={Number(gw.finops_breaches_blocked ?? 0)} />
            </div>
            <button type="button" className="aegis-link-btn" onClick={() => setTab("completions")}>
              Full completions detail →
            </button>
          </article>
          <article className="aegis-card">
            <div className="aegis-card-header">
              <h3>Semantic cache</h3>
              <StatusPill fetch={cache} />
            </div>
            <p className="aegis-muted-line">
              Service <code>aegis-semantic-cache</code>
            </p>
            <div className="aegis-metric-tile-grid">
              <MetricTile label="Hits" value={Number(ca.hits ?? 0)} />
              <MetricTile label="Misses" value={Number(ca.misses ?? 0)} />
              <MetricTile
                label="Hit rate"
                value={
                  typeof ca.hit_rate === "number"
                    ? `${Math.round(Number(ca.hit_rate) * 1000) / 10}%`
                    : String(ca.hit_rate ?? "—")
                }
              />
            </div>
            <button type="button" className="aegis-link-btn" onClick={() => setTab("cache")}>
              Full cache detail →
            </button>
          </article>
        </div>
      ) : null}

      {tab === "completions" ? (
        <div className="aegis-card">
          <div className="aegis-card-header">
            <h3>Model completions</h3>
            <StatusPill fetch={completions} />
          </div>
          {!completions?.reachable && completions?.source !== "demo_fallback" ? (
            <p className="aegis-empty">
              Unreachable{completions?.url ? ` (${completions.url})` : ""}. Deploy the model plane
              API on Render or set <code>LLM_GATEWAY_OPS_URL</code>.
            </p>
          ) : (
            <>
              <p className="aegis-muted-line">
                Upstream service id <code>aegis-llm-gateway</code> (name of the satellite — not the
                AegisAI tool AI Gateway).
                {completions?.note ? ` · ${completions.note}` : null}
              </p>
              <div className="aegis-metric-tile-grid">
                <MetricTile label="Completions" value={Number(gw.completions ?? 0)} />
                <MetricTile label="Stub completions" value={Number(gw.stub_completions ?? 0)} />
                <MetricTile label="Cache hits (reported)" value={Number(gw.cache_hits ?? 0)} />
                <MetricTile label="Cache misses (reported)" value={Number(gw.cache_misses ?? 0)} />
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
            <h3>Semantic cache</h3>
            <StatusPill fetch={cache} />
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

      {tab === "isolation" ? (
        <div className="aegis-card">
          <h3>Tenant isolation on the model plane</h3>
          <p className="aegis-page-lead">
            Completions carry <code>X-Tenant-Id</code>. Cache keys include that tenant — a lookup
            from another tenant must miss. This is model-plane isolation, not AI Gateway tool
            policy.
          </p>
          <ul className="aegis-plain-list">
            <li>
              Known consumer ids: <code>vap</code>, <code>ai-content-factory</code>,{" "}
              <code>sentinel-brief</code>, <code>domainforge-rag-peft</code>, <code>omniforge</code>
            </li>
            <li>Strict mode: budget breach → HTTP 402; FinOps down → 503</li>
            <li>Demo mode: fail-open with honest posture endpoints</li>
          </ul>
          <p className="aegis-muted-line">
            Need to register an agent for <em>tool</em> governance? Use{" "}
            <button type="button" className="aegis-link-btn" onClick={() => onOpenOnboard?.()}>
              Onboard
            </button>{" "}
            — not this dashboard.
          </p>
        </div>
      ) : null}
    </section>
  );
}
