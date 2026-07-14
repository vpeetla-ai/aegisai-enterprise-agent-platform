"use client";

import { useEffect, useState } from "react";
import {
  ArrowDown,
  BookOpen,
  ExternalLink,
  Gauge,
  Layers,
  Scale,
  Shield
} from "lucide-react";

export type OpsMetrics = {
  service: string;
  collected_at?: string;
  total_runs: number;
  success_rate_pct: number;
  p95_latency_ms: number | null;
  active_entities: number;
  slo: { target_uptime_pct: number; success_target_pct: number };
  extra?: Record<string, unknown>;
};

export type ArchitectLayer = {
  tier: string;
  name: string;
  role: string;
  components: string[];
};

export type Tradeoff = {
  decision: string;
  gain: string;
  trade: string;
};

export type AdrLink = {
  title: string;
  href: string;
};

type MetricLabels = {
  runs?: string;
  entities?: string;
  latency?: string;
};

type Props = {
  tagline: string;
  layers: ArchitectLayer[];
  tradeoffs: Tradeoff[];
  metricsUrl: string;
  metricLabels?: MetricLabels;
  eagleEyeNote?: string;
  adrLinks?: AdrLink[];
  docsLinks?: AdrLink[];
  planeSplit?: { tools: string; models: string };
};

export function ArchitectOverview({
  tagline,
  layers,
  tradeoffs,
  metricsUrl,
  metricLabels,
  eagleEyeNote,
  adrLinks,
  docsLinks,
  planeSplit
}: Props) {
  const [metrics, setMetrics] = useState<OpsMetrics | null>(null);
  const [metricsError, setMetricsError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(metricsUrl, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (cancelled) return;
        if (data) setMetrics(normalizeMetrics(data));
        else setMetricsError(true);
      })
      .catch(() => {
        if (!cancelled) setMetricsError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [metricsUrl]);

  const labels = {
    runs: metricLabels?.runs ?? "Total runs",
    entities: metricLabels?.entities ?? "Active entities",
    latency: metricLabels?.latency ?? "P95 latency"
  };

  return (
    <div className="aegis-architect">
      <header className="aegis-architect-hero">
        <p className="aegis-kicker">Architecture</p>
        <h2>How AegisAI is wired</h2>
        <p>{tagline}</p>
        {eagleEyeNote ? <p className="aegis-architect-hero-note">{eagleEyeNote}</p> : null}
      </header>

      {planeSplit ? (
        <div className="aegis-architect-planes" aria-label="Two planes">
          <article className="aegis-architect-plane is-core">
            <Shield size={18} aria-hidden />
            <div>
              <strong>Tool plane · AI Gateway</strong>
              <span>{planeSplit.tools}</span>
            </div>
          </article>
          <article className="aegis-architect-plane is-satellite">
            <Layers size={18} aria-hidden />
            <div>
              <strong>Model plane · LLM metrics</strong>
              <span>{planeSplit.models}</span>
            </div>
          </article>
        </div>
      ) : null}

      <section className="aegis-architect-section" aria-labelledby="arch-stack">
        <div className="aegis-architect-section-head">
          <Layers size={18} aria-hidden />
          <div>
            <p className="aegis-kicker">Stack</p>
            <h3 id="arch-stack">Control plane layers</h3>
          </div>
        </div>
        <ol className="aegis-architect-stack">
          {layers.map((layer, index) => (
            <li key={layer.tier}>
              {index > 0 ? (
                <div className="aegis-architect-stack-arrow" aria-hidden>
                  <ArrowDown size={14} />
                </div>
              ) : null}
              <article className="aegis-architect-layer">
                <span className="aegis-architect-tier">{layer.tier}</span>
                <div className="aegis-architect-layer-copy">
                  <strong>{layer.name}</strong>
                  <em>{layer.role}</em>
                </div>
                <ul className="aegis-architect-chips">
                  {layer.components.map((component) => (
                    <li key={component}>{component}</li>
                  ))}
                </ul>
              </article>
            </li>
          ))}
        </ol>
      </section>

      <section className="aegis-architect-section" aria-labelledby="arch-tradeoffs">
        <div className="aegis-architect-section-head">
          <Scale size={18} aria-hidden />
          <div>
            <p className="aegis-kicker">Principal tradeoffs</p>
            <h3 id="arch-tradeoffs">Decisions with explicit costs</h3>
          </div>
        </div>
        <div className="aegis-architect-tradeoff-grid">
          {tradeoffs.map((item) => (
            <article key={item.decision} className="aegis-architect-tradeoff">
              <h4>{item.decision}</h4>
              <p>
                <span className="aegis-architect-gain">Gain</span>
                {item.gain}
              </p>
              <p>
                <span className="aegis-architect-trade">Trade</span>
                {item.trade}
              </p>
            </article>
          ))}
        </div>
      </section>

      {(adrLinks?.length || docsLinks?.length) ? (
        <section className="aegis-architect-section" aria-labelledby="arch-record">
          <div className="aegis-architect-section-head">
            <BookOpen size={18} aria-hidden />
            <div>
              <p className="aegis-kicker">Record</p>
              <h3 id="arch-record">ADRs, case studies, SLOs</h3>
            </div>
          </div>
          <ul className="aegis-architect-links">
            {adrLinks?.map((link) => (
              <li key={link.href}>
                <a href={link.href} target="_blank" rel="noopener noreferrer">
                  {link.title}
                  <ExternalLink size={14} aria-hidden />
                </a>
              </li>
            ))}
            {docsLinks?.map((link) => (
              <li key={link.href}>
                <a href={link.href} target="_blank" rel="noopener noreferrer">
                  {link.title}
                  <ExternalLink size={14} aria-hidden />
                </a>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="aegis-architect-section" aria-labelledby="arch-metrics">
        <div className="aegis-architect-section-head">
          <Gauge size={18} aria-hidden />
          <div>
            <p className="aegis-kicker">Live ops</p>
            <h3 id="arch-metrics">Production metrics</h3>
          </div>
        </div>
        {metrics ? (
          <>
            <div className="aegis-metric-tile-grid">
              <article className="aegis-metric-tile">
                <span>{labels.runs}</span>
                <strong>{metrics.total_runs}</strong>
              </article>
              <article className="aegis-metric-tile">
                <span>Success rate</span>
                <strong>{metrics.success_rate_pct}%</strong>
              </article>
              <article className="aegis-metric-tile">
                <span>{labels.latency}</span>
                <strong>
                  {metrics.p95_latency_ms != null ? `${metrics.p95_latency_ms}ms` : "—"}
                </strong>
              </article>
              <article className="aegis-metric-tile">
                <span>{labels.entities}</span>
                <strong>{metrics.active_entities}</strong>
              </article>
            </div>
            <p className="aegis-muted-line">
              <code>{metricsUrl.replace(/^https?:\/\/[^/]+/, "")}</code>
              {" · "}
              SLO {metrics.slo.success_target_pct}% success · {metrics.slo.target_uptime_pct}% uptime
              target
            </p>
          </>
        ) : (
          <p className="aegis-empty">
            {metricsError
              ? "Ops metrics unreachable — API may be waking from idle. Use Recheck API, then refresh."
              : "Loading live ops metrics…"}
          </p>
        )}
      </section>
    </div>
  );
}

function normalizeMetrics(data: Record<string, unknown>): OpsMetrics {
  const sloRaw = (data.slo as Record<string, unknown>) || {};
  const successTarget =
    (sloRaw.success_target_pct as number) ??
    (sloRaw.pipeline_success_target_pct as number) ??
    95.0;

  return {
    service: String(data.service ?? "unknown"),
    collected_at: data.collected_at as string | undefined,
    total_runs: Number(data.total_runs ?? data.sample_size ?? data.total ?? 0),
    success_rate_pct: Number(data.success_rate_pct ?? 100 - Number(data.failure_rate_pct ?? 0)),
    p95_latency_ms:
      (data.p95_latency_ms as number | null) ??
      (data.p95_node_latency_ms as number | null) ??
      (data.p95_ms as number | null) ??
      null,
    active_entities: Number(data.active_entities ?? data.invited_users ?? data.active_users ?? 0),
    slo: {
      target_uptime_pct: Number(sloRaw.target_uptime_pct ?? 99.5),
      success_target_pct: successTarget
    },
    extra: (data.extra as Record<string, unknown>) ?? undefined
  };
}
