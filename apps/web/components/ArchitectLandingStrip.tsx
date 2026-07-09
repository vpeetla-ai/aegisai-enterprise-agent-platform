"use client";

import { ArchitectOverview } from "@/components/ArchitectOverview";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "https://aegisai-api.onrender.com";
const PORTFOLIO = "https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main";

export function ArchitectLandingStrip() {
  return (
    <div className="architect-landing-strip" style={{ padding: "1.5rem 1.25rem", borderBottom: "1px solid var(--border, #222)" }}>
      <ArchitectOverview
        tagline="Governance control plane: policy, HITL approvals, action execution, and audit — separate from orchestration so agents cannot bypass side-effect gates."
        layers={[
          { tier: "L1", name: "Control room", role: "Operator UX", components: ["Governance modules", "HITL queue", "FinOps panel"] },
          { tier: "L2", name: "Gateway", role: "Side-effect gate", components: ["Action proposals", "OPA policy", "Approval tasks"] },
          { tier: "L3", name: "Execution", role: "Idempotent connectors", components: ["HTTP connectors", "Audit events", "Rollback refs"] },
          { tier: "L4", name: "Ops", role: "Regulated state", components: ["Control-plane DB", "/api/v1/ops/metrics", "Observability adapters"] },
        ]}
        tradeoffs={[
          { decision: "Governance separate from VAP orchestration", gain: "One policy engine for all agents", trade: "Cross-service latency on gated actions" },
          { decision: "SQLite/Postgres control plane as source of truth", gain: "Audit + HITL state survives trace TTL", trade: "Not serverless-only" },
          { decision: "Langfuse as adapter not authority", gain: "Best-of-breed traces without regulated data leakage", trade: "Two observability surfaces" },
          { decision: "MCP governance proxy", gain: "Tool calls gated like HTTP side effects", trade: "Proxy hop on every tool invocation" },
        ]}
        metricsUrl={`${API_BASE}/api/v1/ops/metrics`}
        metricLabels={{ runs: "Governed actions", entities: "Open cases", latency: "P95 latency" }}
        eagleEyeNote="Every side effect in the vpeetla-ai stack routes through this layer before production impact."
        adrLinks={[
          { title: "ADR-011 — Agent FinOps standalone service", href: `${PORTFOLIO}/adr/ADR-011-agent-finops-standalone-service.md` },
          { title: "Case study — AegisAI governance", href: `${PORTFOLIO}/case-studies/aegisai-enterprise-agent-platform.md` },
        ]}
        docsLinks={[
          { title: "Architecture", href: "https://github.com/vpeetla-ai/aegisai-enterprise-agent-platform/blob/main/docs/ARCHITECTURE.md" },
          { title: "SLO targets", href: "https://github.com/vpeetla-ai/aegisai-enterprise-agent-platform/blob/main/docs/SLO.md" },
        ]}
      />
    </div>
  );
}
