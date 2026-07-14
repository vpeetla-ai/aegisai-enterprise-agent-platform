"use client";

import { ArchitectOverview } from "@/components/ArchitectOverview";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "https://aegisai-api.onrender.com";
const PORTFOLIO = "https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main";
const REPO = "https://github.com/vpeetla-ai/aegisai-enterprise-agent-platform/blob/main";

export function ArchitectLandingStrip() {
  return (
    <div className="aegis-architect-shell">
      <ArchitectOverview
        tagline="Governance control plane for agent side effects: policy, HITL approvals, execution tokens, and signed audit — kept separate from orchestration so agents cannot bypass the gate."
        eagleEyeNote="Every dangerous tool call in the vpeetla-ai stack is meant to route through AI Gateway before production impact."
        planeSplit={{
          tools:
            "Core product — intercept deploy / notify / refund, issue tokens, HITL, kill switch, audit.",
          models:
            "Optional satellite — read-only cost & cache metrics from aegis-llm-gateway + semantic cache (not tool intercept)."
        }}
        layers={[
          {
            tier: "L1",
            name: "Control Room",
            role: "Operator UX",
            components: ["Operate journey", "HITL queue", "Incidents / kill switch", "LLM metrics"]
          },
          {
            tier: "L2",
            name: "AI Gateway",
            role: "Side-effect gate",
            components: ["Tool request API", "Policy / OPA", "Approval tasks", "Execution tokens"]
          },
          {
            tier: "L3",
            name: "Execution broker",
            role: "Idempotent connectors",
            components: ["HTTP connectors", "Deploy / notify adapters", "Rollback refs", "Audit events"]
          },
          {
            tier: "L4",
            name: "Ops & state",
            role: "Regulated persistence",
            components: ["Control-plane DB", "/api/v1/ops/metrics", "Observability adapters"]
          }
        ]}
        tradeoffs={[
          {
            decision: "Governance separate from VAP orchestration",
            gain: "One policy engine for all agents across products",
            trade: "Cross-service latency on gated actions"
          },
          {
            decision: "SQLite / Postgres control plane as source of truth",
            gain: "Audit + HITL state survives trace TTL",
            trade: "Not a serverless-only design"
          },
          {
            decision: "Tool AI Gateway ≠ LLM metrics plane",
            gain: "Clear product story; model routing stays in satellite services",
            trade: "Two surfaces operators must not confuse"
          },
          {
            decision: "MCP governance proxy",
            gain: "Tool calls gated like HTTP side effects",
            trade: "Proxy hop on every tool invocation"
          }
        ]}
        metricsUrl={`${API_BASE}/api/v1/ops/metrics`}
        metricLabels={{ runs: "Governed actions", entities: "Open cases", latency: "P95 latency" }}
        adrLinks={[
          {
            title: "ADR-011 — Agent FinOps standalone service",
            href: `${PORTFOLIO}/adr/ADR-011-agent-finops-standalone-service.md`
          },
          {
            title: "Case study — AegisAI governance",
            href: `${PORTFOLIO}/case-studies/aegisai-enterprise-agent-platform.md`
          }
        ]}
        docsLinks={[
          {
            title: "Architecture (platform)",
            href: `${REPO}/platform/architecture/ARCHITECTURE.md`
          },
          {
            title: "Ecosystem map",
            href: `${REPO}/docs/ECOSYSTEM.md`
          },
          {
            title: "SLO targets",
            href: `${REPO}/docs/SLO.md`
          }
        ]}
      />
    </div>
  );
}
